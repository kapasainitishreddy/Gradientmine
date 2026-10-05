"""Canonical JSON, Ed25519 identities and integrity receipts. No keys are sent to the server."""

from __future__ import annotations
import base64
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(raw: bytes) -> str:
    value = int.from_bytes(raw, "big")
    text = ""
    while value:
        value, remainder = divmod(value, 58)
        text = ALPHABET[remainder] + text
    return "1" * (len(raw) - len(raw.lstrip(b"\0"))) + text


def b58decode(text: str) -> bytes:
    if not isinstance(text, str) or len(text) > 256:
        raise ValueError("Invalid base58 value")
    value = 0
    for char in text:
        if char not in ALPHABET:
            raise ValueError("Invalid base58 character")
        value = value * 58 + ALPHABET.index(char)
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return b"\0" * (len(text) - len(text.lstrip("1"))) + raw


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


def safe_json(raw: bytes, limit: int = 262144) -> Any:
    if len(raw) > limit:
        raise ValueError("JSON exceeds size limit")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"Invalid JSON number: {value}")

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject_constant)
    except (RecursionError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid JSON") from exc


def validate_address(address: str) -> str:
    if len(b58decode(address)) != 32:
        raise ValueError("Expected a 32-byte Solana public key")
    return address


class Identity:
    def __init__(self, secret: bytes):
        self._key = Ed25519PrivateKey.from_private_bytes(secret)
        self.address = b58encode(self._key.public_key().public_bytes_raw())

    @classmethod
    def create(cls, path: Path) -> "Identity":
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        secret = os.urandom(32)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as file:
            json.dump(
                {"format": "gradientmine.ed25519.v1", "secret_key": base64.b64encode(secret).decode()}, file
            )
        return cls(secret)

    @classmethod
    def load(cls, path: Path) -> "Identity":
        path = Path(path)
        if os.name == "posix" and path.stat().st_mode & 0o077:
            raise ValueError("Identity permissions must be 0600; run chmod 600 on the file")
        value = safe_json(path.read_bytes(), limit=4096)
        if isinstance(value, list) and len(value) == 64:  # standard local Solana CLI file
            secret = bytes(value[:32])
            identity = cls(secret)
            if bytes(value[32:]) != b58decode(identity.address):
                raise ValueError("Invalid Solana identity")
            return identity
        if not isinstance(value, dict) or value.get("format") != "gradientmine.ed25519.v1":
            raise ValueError("Unsupported local identity file")
        return cls(base64.b64decode(value["secret_key"], validate=True))

    def sign_bytes(self, message: bytes) -> str:
        return base64.b64encode(self._key.sign(message)).decode()

    def sign(self, payload: dict) -> dict:
        raw = canonical(payload)
        return {
            "payload": payload,
            "payload_base64": base64.b64encode(raw).decode(),
            "signer": self.address,
            "signature": self.sign_bytes(raw),
        }

    def solana_bytes(self) -> bytes:
        """Only for the local SDK signer. Never log or transmit this value."""
        return self._key.private_bytes_raw() + self._key.public_key().public_bytes_raw()


def verify_bytes(address: str, message: bytes, signature: str) -> bool:
    try:
        raw = b58decode(validate_address(address))
        Ed25519PublicKey.from_public_bytes(raw).verify(base64.b64decode(signature, validate=True), message)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def verify_signed(envelope: dict) -> bool:
    try:
        if set(envelope) not in (
            {"payload", "signer", "signature"},
            {"payload", "payload_base64", "signer", "signature"},
        ):
            return False
        raw = canonical(envelope["payload"])
        if (
            "payload_base64" in envelope
            and base64.b64decode(envelope["payload_base64"], validate=True) != raw
        ):
            return False
        return verify_bytes(envelope["signer"], raw, envelope["signature"])
    except (ValueError, TypeError, KeyError):
        return False


def authentication_message(origin, address, nonce, expires):
    return (
        f"GradientMine wallet authentication v1\nOrigin: {origin}\n"
        f"Wallet: {address}\nNonce: {nonce}\nExpires: {expires}\n"
        "This message authenticates a session. It does not authorize a transaction."
    )


def validate_auth_challenge(challenge, origin, address):
    """Refuse arbitrary-message signing even when a malicious server requests it."""
    nonce = challenge.get("nonce", "")
    expires = challenge.get("expires_at")
    if not isinstance(nonce, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", nonce):
        raise ValueError("Invalid authentication nonce")
    if type(expires) is not int or not 0 < expires - time.time() <= 360:
        raise ValueError("Authentication challenge expired or has an unsafe validity period")
    expected = authentication_message(origin, validate_address(address), nonce, expires)
    if challenge.get("message") != expected:
        raise ValueError("Server requested a message that does not match this wallet authentication intent")
    return expected.encode()

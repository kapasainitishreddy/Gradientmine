"""Versioned wire layout shared with program/src/lib.rs. No model or evaluation data goes on-chain."""

import struct
from .crypto import b58decode, b58encode, digest, validate_address

BOUNTY_SIZE = 232
SUBMISSION_SIZE = 144
DEVNET_GENESIS = "EtWTRABZaYq6iMfeYKouRu166VU2xqa1wcaWoxPkrZBG"


def hash_bytes(value):
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("Expected a SHA-256 hexadecimal commitment")
    return bytes.fromhex(value)


def job_key(job):
    return bytes.fromhex(digest(job["id"].encode()))


def create_data(job):
    policy = job["policy"]
    validate_address(policy["validator"])
    return (
        b"\0"
        + job_key(job)
        + hash_bytes(job["policy_sha256"])
        + b58decode(policy["validator"])
        + struct.pack("<qqQ", policy["deadline"], policy["refund_after"], policy["reward_lamports"])
    )


def registration_data(sub):
    return b"\x01" + hash_bytes(sub["artifact_sha256"]) + hash_bytes(sub["manifest_sha256"])


def settlement_data(sub, receipt_sha):
    return b"\x02" + hash_bytes(sub["artifact_sha256"]) + hash_bytes(receipt_sha)


def decode_bounty(raw):
    if len(raw) != BOUNTY_SIZE or raw[:8] != b"GMBOUNT1" or raw[8] > 2 or raw[9] > 8 or any(raw[10:16]):
        raise ValueError("Unrecognized bounty account layout")
    deadline, refund_after, reward = struct.unpack_from("<qqQ", raw, 144)
    return {
        "state": raw[8],
        "submission_count": raw[9],
        "creator": b58encode(raw[16:48]),
        "validator": b58encode(raw[48:80]),
        "job_key": raw[80:112].hex(),
        "policy_sha256": raw[112:144].hex(),
        "deadline": deadline,
        "refund_after": refund_after,
        "reward_lamports": reward,
        "winner": b58encode(raw[168:200]),
        "receipt_sha256": raw[200:232].hex(),
    }


def decode_submission(raw):
    if len(raw) != SUBMISSION_SIZE or raw[:8] != b"GMSUBM01":
        raise ValueError("Unrecognized submission account layout")
    return {
        "bounty": b58encode(raw[8:40]),
        "worker": b58encode(raw[40:72]),
        "artifact_sha256": raw[72:104].hex(),
        "manifest_sha256": raw[104:136].hex(),
        "registered_at": struct.unpack_from("<q", raw, 136)[0],
    }

"""Strict JSON-RPC transaction verification. RPC endpoints themselves remain trusted data providers."""

import time
from urllib.parse import urlparse
import httpx
from .crypto import b58decode
from .wire import DEVNET_GENESIS


def validate_transaction(value, signature, spec):
    try:
        if len(b58decode(signature)) != 64 or not value or value["meta"]["err"] is not None:
            raise ValueError("Transaction is missing, invalid or failed on-chain")
        tx = value["transaction"]
        message = tx["message"]
        header = message["header"]
        keys = message["accountKeys"]
        if (
            tx["signatures"] != [signature]
            or header["numRequiredSignatures"] != 1
            or keys[0] != spec["payer"]
        ):
            raise ValueError("Transaction signer does not match the intended wallet")
        if header["numReadonlySignedAccounts"] != 0:
            raise ValueError("Unexpected signer privileges")
        if len(message["instructions"]) != 1:
            raise ValueError("Only the single intended GradientMine instruction is accepted")
        instruction = message["instructions"][0]
        if (
            type(instruction["programIdIndex"]) is not int
            or not 0 <= instruction["programIdIndex"] < len(keys)
            or any(type(index) is not int or not 0 <= index < len(keys) for index in instruction["accounts"])
            or type(header["numReadonlyUnsignedAccounts"]) is not int
            or not 0 <= header["numReadonlyUnsignedAccounts"] < len(keys)
        ):
            raise ValueError("Malformed transaction account indices or header")
        if (
            keys[instruction["programIdIndex"]] != spec["program"]
            or b58decode(instruction["data"]) != spec["data"]
        ):
            raise ValueError("Transaction program or committed instruction bytes differ")
        if len(instruction["accounts"]) != len(spec["accounts"]):
            raise ValueError("Unexpected instruction accounts")
        expected_keys = {spec["program"], spec["payer"], *(item[0] for item in spec["accounts"])}
        if len(keys) != len(set(keys)) or set(keys) != expected_keys:
            raise ValueError("Unexpected transaction account set")
        readonly = header["numReadonlyUnsignedAccounts"]
        for index, (address, is_signer, is_writable) in zip(instruction["accounts"], spec["accounts"]):
            actual_signer = index == 0
            actual_writable = index == 0 or index < len(keys) - readonly
            if keys[index] != address or actual_signer != is_signer or actual_writable != is_writable:
                raise ValueError("Transaction account identities or privileges differ")
        if type(value["meta"]["fee"]) is not int or not 0 <= value["meta"]["fee"] <= 100000:
            raise ValueError("Transaction exceeds the supported testnet fee cap")
        return value
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Malformed transaction evidence") from exc


class Rpc:
    def __init__(self, url):
        parsed = urlparse(url)
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")
        ):
            raise ValueError("RPC requires HTTPS or loopback")
        self.url = url

    def call(self, method, params=None):
        try:
            response = httpx.post(
                self.url,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []},
                timeout=20,
            )
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ValueError(f"Solana RPC {method} is unavailable; no confirmation can be inferred") from exc
        if "error" in result:
            error = result["error"]
            raise ValueError(
                f"Solana RPC {method} rejected the request (code {error.get('code', 'unknown')})"
            )
        if "result" not in result:
            raise ValueError("RPC returned no result")
        return result["result"]

    def require_devnet(self):
        genesis = self.call("getGenesisHash")
        if genesis != DEVNET_GENESIS:
            raise ValueError("Refusing this RPC: its genesis hash is not Solana Devnet")
        return genesis

    def account(self, address):
        return self.call("getAccountInfo", [str(address), {"encoding": "base64", "commitment": "finalized"}])[
            "value"
        ]

    def wait(self, signature, seconds=75):
        if len(b58decode(signature)) != 64:
            raise ValueError("Invalid transaction signature")
        until = time.monotonic() + seconds
        while True:
            result = self.call("getSignatureStatuses", [[signature], {"searchTransactionHistory": True}])[
                "value"
            ][0]
            if result and result.get("err") is not None:
                raise ValueError("The transaction failed on-chain; inspect Explorer and refresh")
            if result and result.get("confirmationStatus") == "finalized":
                return result
            if time.monotonic() >= until:
                raise ValueError(
                    "Transaction not yet finalized. Keep its signature and retry confirmation; do not assume success."
                )
            time.sleep(0.7)

    def transaction(self, signature, spec):
        self.require_devnet()
        self.wait(signature)
        value = self.call(
            "getTransaction",
            [signature, {"encoding": "json", "commitment": "finalized", "maxSupportedTransactionVersion": 0}],
        )
        return validate_transaction(value, signature, spec)

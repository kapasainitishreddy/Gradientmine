"""Public, wallet-authenticated worker checkpoints and conservative registration recovery.

Signed transaction bytes are persisted before broadcast. RPC uncertainty never authorizes
a fresh signature: replacement needs expiry, finalized failure/absence, and an absent PDA.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from .crypto import canonical, digest, safe_json, verify_signed
from .ml import validate_adapter
from .rpc import validate_transaction
from .store import atomic_write
from .wire import decode_submission

STATE_LIMIT = 2_000_000
MAX_ATTEMPTS = 16
STATE_FIELDS = {
    "format",
    "origin",
    "mode",
    "program_id",
    "rpc",
    "worker",
    "job",
    "artifact",
    "manifest",
    "losses",
    "submission",
    "pending",
    "attempts",
    "stage",
}
STAGES = {"trained", "submitted", "signed", "unknown", "waiting", "failed", "finalized", "complete"}


def validate_state(state, identity):
    try:
        if (
            not isinstance(state, dict)
            or set(state) != STATE_FIELDS
            or state["format"] != "gradientmine.worker-state.v1"
            or state["worker"] != identity.address
            or state["mode"] not in {"local", "devnet"}
            or state["stage"] not in STAGES
            or not isinstance(state["attempts"], list)
            or len(state["attempts"]) > MAX_ATTEMPTS
        ):
            raise ValueError("Invalid worker checkpoint fields or wallet binding")
        job, manifest = state["job"], state["manifest"]
        if digest(job["policy"]) != job["policy_sha256"]:
            raise ValueError("Checkpoint bounty policy commitment mismatch")
        if not verify_signed(manifest) or manifest["signer"] != identity.address:
            raise ValueError("Checkpoint manifest signature or wallet mismatch")
        payload = manifest["payload"]
        expected = {
            "format": "gradientmine.submission.v1",
            "job_id": job["id"],
            "policy_sha256": job["policy_sha256"],
            "parent_sha256": job["policy"]["parent_sha256"],
            "training_data_sha256": job["policy"]["train_sha256"],
            "artifact_sha256": digest(state["artifact"]),
        }
        if any(payload.get(k) != v for k, v in expected.items()):
            raise ValueError("Checkpoint manifest commitments mismatch")
        validate_adapter(state["artifact"], expected["parent_sha256"])
        if state["submission"] is not None:
            validate_submission(state["submission"], state)
        if not isinstance(state["losses"], list) or not 1 <= len(state["losses"]) <= 10000:
            raise ValueError("Invalid checkpoint training losses")
        if state["mode"] == "local" and (state["pending"] or state["attempts"]):
            raise ValueError("Local checkpoints cannot contain chain transactions")
        if state["pending"] is not None or state["attempts"]:
            from .chain import Chain

            chain = Chain(state["program_id"], state["rpc"])
            for pending in [state["pending"], *state["attempts"]]:
                if pending is not None:
                    validate_pending(chain, pending, state)
        return state
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("Malformed worker checkpoint") from exc


def validate_submission(sub, state):
    expected = {
        "job_id": state["job"]["id"],
        "worker": state["worker"],
        "artifact_sha256": digest(state["artifact"]),
        "manifest_sha256": digest(state["manifest"]),
    }
    if not isinstance(sub, dict) or not isinstance(sub.get("id"), str) or not sub["id"]:
        raise ValueError("Malformed submission response")
    if any(sub.get(k) != v for k, v in expected.items()):
        raise ValueError("Submission differs from the saved worker commitments")
    if state["submission"] is not None and sub["id"] != state["submission"]["id"]:
        raise ValueError("Submission identity changed during recovery")
    return sub


def validate_pending(chain, pending, state):
    if (
        not isinstance(pending, dict)
        or set(pending) != {"signature", "transaction_base64", "last_valid_block_height"}
        or type(pending["last_valid_block_height"]) is not int
        or not 0 <= pending["last_valid_block_height"] <= 2**63 - 1
        or not isinstance(pending["transaction_base64"], str)
        or len(pending["transaction_base64"]) > 1644
    ):
        raise ValueError("Invalid pending registration checkpoint")
    if state["submission"] is None:
        raise ValueError("Pending transaction has no bound submission")
    checked = chain.validate_signed(
        base64.b64decode(pending["transaction_base64"], validate=True),
        chain.spec("register", state["job"], state["submission"]),
    )
    if checked["signature"] != pending["signature"]:
        raise ValueError("Pending registration signature differs from its signed bytes")
    return pending


def save_state(out, state, identity):
    validate_state(state, identity)
    raw = canonical(identity.sign(state))
    if len(raw) > STATE_LIMIT:
        raise ValueError("Worker checkpoint exceeds size limit")
    out = Path(out)
    atomic_write(out / "worker-state.json", raw)
    # Durably publish the rename before the next remote write, including process/power loss.
    if os.name == "posix":
        fd = os.open(out, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def load_state(out, identity):
    path = Path(out) / "worker-state.json"
    with path.open("rb") as file:
        raw = file.read(STATE_LIMIT + 1)
    envelope = safe_json(raw, limit=STATE_LIMIT)
    if (
        not isinstance(envelope, dict)
        or not verify_signed(envelope)
        or envelope["signer"] != identity.address
    ):
        raise ValueError("Worker checkpoint signature or identity binding failed")
    return validate_state(envelope["payload"], identity)


def registration_account(chain, state):
    job, sub = state["job"], state["submission"]
    account = chain.rpc.account(chain.submission_address(job, sub["worker"]))
    if account is None:
        return None
    if account.get("owner") != chain.program_id:
        raise ValueError("Registration account is owned by a different program; refusing recovery")
    record = decode_submission(base64.b64decode(account["data"][0], validate=True))
    expected = {
        "bounty": chain.bounty_address(job),
        "worker": sub["worker"],
        "artifact_sha256": sub["artifact_sha256"],
        "manifest_sha256": sub["manifest_sha256"],
    }
    if any(record[k] != v for k, v in expected.items()):
        raise ValueError("Finalized registration account commitment mismatch")
    if not 0 <= record["registered_at"] < job["policy"]["deadline"]:
        raise ValueError("Finalized registration was outside the bounty deadline")
    return record


def signature_status(chain, signature):
    status = chain.rpc.call("getSignatureStatuses", [[signature], {"searchTransactionHistory": True}])[
        "value"
    ][0]
    if status is not None and (
        not isinstance(status, dict)
        or "err" not in status
        or status.get("confirmationStatus") not in {"processed", "confirmed", "finalized"}
    ):
        raise ValueError("Malformed RPC signature status; refusing recovery")
    return status


def discover_registration(chain, state, confirm, persist):
    """Find a finalized exact instruction; an account alone never proves a transaction."""
    sub = state["submission"]
    signatures = []
    if state["pending"]:
        signatures.append(state["pending"]["signature"])
    signatures.extend(item["signature"] for item in reversed(state["attempts"]))
    if sub.get("registration_signature"):
        signatures.append(sub["registration_signature"])

    def finalize(signature, check_intent=False):
        status = signature_status(chain, signature)
        if not status or status["err"] is not None or status["confirmationStatus"] != "finalized":
            return False
        if check_intent:
            value = chain.rpc.call(
                "getTransaction",
                [
                    signature,
                    {
                        "encoding": "json",
                        "commitment": "finalized",
                        "maxSupportedTransactionVersion": 0,
                    },
                ],
            )
            try:
                validate_transaction(value, signature, chain.spec("register", state["job"], sub))
            except ValueError:
                # Address histories also contain transfers and unrelated instructions.
                return False
        # Strict finalized transaction validation remains in Chain.confirm, unchanged.
        chain.confirm("register", state["job"], sub, signature)
        confirm(signature)
        state["stage"] = "finalized"
        sub["registration_signature"] = signature
        persist()
        return True

    for signature in dict.fromkeys(signatures):
        if finalize(signature):
            return "finalized"
    history = chain.rpc.call(
        "getSignaturesForAddress",
        [chain.submission_address(state["job"], sub["worker"]), {"limit": 32, "commitment": "finalized"}],
    )
    if not isinstance(history, list) or len(history) > 32:
        raise ValueError("Malformed or unbounded registration history")
    for item in history:
        if not isinstance(item, dict) or not isinstance(item.get("signature"), str):
            raise ValueError("Malformed registration history entry")
        if item.get("err") is None and item["signature"] not in signatures:
            if finalize(item["signature"], check_intent=True):
                return "finalized"
    state["stage"] = "unknown"
    persist()
    raise ValueError(
        "Finalized registration account exists but its exact transaction is unavailable; no retry"
    )


def recover_registration(chain, state, identity, intent, confirm, persist):
    """Perform one conservative recovery step; return a truthful persisted stage."""
    chain.deployment()
    job, sub = state["job"], state["submission"]
    bounty, _ = chain.read_bounty(job)
    account = registration_account(chain, state)
    if account is not None:
        return discover_registration(chain, state, confirm, persist)
    if bounty["state"] != 0:
        raise ValueError("Bounty is terminal; no worker registration broadcast is permitted")
    pending = state["pending"]
    if pending is not None:
        validate_pending(chain, pending, state)
        status = signature_status(chain, pending["signature"])
        if status and status["err"] is None:
            if status["confirmationStatus"] == "finalized":
                # A successful status without matching finalized accounts is insufficient.
                chain.confirm("register", job, sub, pending["signature"])
                confirm(pending["signature"])
                state["stage"] = "finalized"
                persist()
                return "finalized"
            state["stage"] = "waiting"
            persist()
            return "waiting"
        height = chain.rpc.call("getBlockHeight", [{"commitment": "finalized"}])
        if type(height) is not int or height < 0:
            raise ValueError("Malformed finalized block height")
        expired = height > pending["last_valid_block_height"]
        failed = status is not None and status["err"] is not None
        state["stage"] = "failed" if failed and status["confirmationStatus"] == "finalized" else "unknown"
        if failed and status["confirmationStatus"] != "finalized":
            state["stage"] = "waiting"
        persist()
        if failed and status["confirmationStatus"] != "finalized":
            return "waiting"
        if expired:
            from solders.transaction import Transaction

            tx = Transaction.from_bytes(base64.b64decode(pending["transaction_base64"], validate=True))
            valid = chain.rpc.call(
                "isBlockhashValid", [str(tx.message.recent_blockhash), {"commitment": "finalized"}]
            )["value"]
            if type(valid) is not bool:
                raise ValueError("Malformed finalized blockhash validity")
            if valid:
                return state["stage"]
            # Recheck finalized account/status immediately before replacing signed bytes.
            if registration_account(chain, state) is not None:
                return discover_registration(chain, state, confirm, persist)
            latest = signature_status(chain, pending["signature"])
            if latest and (latest["err"] is None or latest["confirmationStatus"] != "finalized"):
                state["stage"] = "waiting"
                persist()
                return "waiting"
            if len(state["attempts"]) >= MAX_ATTEMPTS:
                raise ValueError("Registration retry history limit reached; retain evidence and inspect RPC")
            state["attempts"].append(pending)
            state["pending"] = None
            pending = None
        elif failed:
            return "failed"
    if pending is None:
        if bounty["state"] != 0:
            raise ValueError("Bounty is terminal; no new worker registration is permitted")
        slot = chain.rpc.call("getSlot", [{"commitment": "finalized"}])
        if type(slot) is not int or slot < 0:
            raise ValueError("Malformed finalized slot; refusing a new registration")
        chain_time = chain.rpc.call("getBlockTime", [slot])
        if type(chain_time) is not int or chain_time < 0:
            raise ValueError("Finalized block time is unavailable; refusing a new registration")
        if chain_time >= job["policy"]["deadline"]:
            raise ValueError("The finalized registration deadline has passed; no replacement may be signed")
        pending = chain.sign_intent(intent(), "register", job, sub, identity)
        validate_pending(chain, pending, state)
        state["pending"] = pending
        state["stage"] = "signed"
        persist()
    try:
        chain.send_signed(pending)
    except Exception:
        state["stage"] = "unknown"
        persist()
        raise
    state["stage"] = "unknown"
    persist()
    return "unknown"

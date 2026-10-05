"""One-shot real Solana Devnet escrow smoke test.

This deliberately exercises only the chain state machine with disposable CI identities.
The normal release workflow separately proves real model training/evaluation. Private key
files are temporary runner files and must never be uploaded.
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path

from gradientmine.chain import Chain
from gradientmine.crypto import Identity, digest


def wait_finalized(chain: Chain, action: str, job: dict, sub: dict | None, signature: str, timeout=120):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            return chain.confirm(action, job, sub, signature)
        except Exception as exc:  # RPC finalization is eventually consistent; bounded retry only.
            last = exc
            time.sleep(2)
    raise RuntimeError(f"{action} did not reach verified finalized state: {last}")


def send(chain: Chain, action: str, job: dict, sub: dict | None, identity: Identity):
    intent = chain.intent(action, job, sub)
    pending = chain.sign_intent(intent, action, job, sub, identity)
    chain.send_signed(pending)
    evidence = wait_finalized(chain, action, job, sub, pending["signature"])
    return {**evidence, "last_valid_block_height": pending["last_valid_block_height"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--program", required=True)
    p.add_argument("--creator", required=True, type=Path)
    p.add_argument("--worker", required=True, type=Path)
    p.add_argument("--validator", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--reward-lamports", type=int, default=5_000_000)
    p.add_argument("--cutoff-seconds", type=int, default=35)
    a = p.parse_args()

    if a.reward_lamports <= 0 or not 20 <= a.cutoff_seconds <= 180:
        raise ValueError("Refusing unsafe smoke-test timing or zero reward")

    creator = Identity.load(a.creator)
    worker = Identity.load(a.worker)
    validator = Identity.load(a.validator)
    if len({creator.address, worker.address, validator.address}) != 3:
        raise ValueError("Creator, worker and validator must be distinct")

    chain = Chain(a.program)
    deployment = chain.deployment()
    now = int(time.time())
    policy = {
        "validator": validator.address,
        "deadline": now + a.cutoff_seconds,
        "refund_after": now + a.cutoff_seconds + 900,
        "reward_lamports": a.reward_lamports,
    }
    job = {
        "id": "devnet-smoke-" + str(uuid.uuid4()),
        "creator": creator.address,
        "policy": policy,
        "policy_sha256": digest(policy),
    }
    nonce = uuid.uuid4().hex
    sub = {
        "worker": worker.address,
        "artifact_sha256": digest(("artifact:" + nonce).encode()),
        "manifest_sha256": digest(("manifest:" + nonce).encode()),
        "receipt_sha256": digest(("receipt:" + nonce).encode()),
    }

    funded = send(chain, "fund", job, None, creator)
    registered = send(chain, "register", job, sub, worker)

    remaining = policy["deadline"] - int(time.time()) + 2
    if remaining > 0:
        time.sleep(remaining)

    settled = send(chain, "settle", job, sub, validator)
    result = {
        "format": "gradientmine.devnet-smoke.v1",
        "executed_at": int(time.time()),
        "network": "solana:devnet",
        "genesis": deployment["genesis"],
        "program_id": a.program,
        "bounty_address": chain.bounty_address(job),
        "creator": creator.address,
        "worker": worker.address,
        "validator": validator.address,
        "policy_sha256": job["policy_sha256"],
        "artifact_sha256": sub["artifact_sha256"],
        "manifest_sha256": sub["manifest_sha256"],
        "receipt_sha256": sub["receipt_sha256"],
        "reward_lamports": a.reward_lamports,
        "deadline": policy["deadline"],
        "funding": funded,
        "registration": registered,
        "settlement": settled,
        "disclosure": (
            "Real Devnet chain-state smoke test with disposable CI identities. "
            "It proves escrow/register/payout mechanics, not model-quality truth, "
            "a Phantom interaction, or independently operated workers."
        ),
        "private_keys_exported": False,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

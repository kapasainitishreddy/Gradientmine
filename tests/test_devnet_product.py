"""Actual API + CPU worker + compiled native SBF payout; explicitly local LiteSVM.

This is not Devnet evidence. RPC JSON is derived from real LiteSVM execution and
passes the production exact-instruction/finalized-account/balance verifier.
"""

import argparse
import base64
import copy
import json
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

from gradientmine.api import create_app
from gradientmine.chain import Chain
from gradientmine.config import Settings
from gradientmine.crypto import Identity, b58encode, canonical, digest, safe_json
from gradientmine.rpc import Rpc
from gradientmine.wire import DEVNET_GENESIS
from scripts.devnet_smoke import Checkpoint, execute_product
from scripts.public_evidence import checked_artifacts, export_public


class VmRpc(Rpc):
    """Local VM adapter. No network or synthetic success path, never a Devnet proof."""

    def __init__(self, machine):
        super().__init__("http://127.0.0.1:8899")
        self.machine = machine
        self.history = {}
        self.height = 1
        self.before_send = None
        self.drop_first_response = False

    def call(self, method, params=None):
        params = params or []
        if method == "getGenesisHash":
            return DEVNET_GENESIS  # synthetic fixture metadata, output classified local:litesvm
        if method == "getAccountInfo":
            account = self.machine.get_account(Pubkey.from_string(params[0]))
            return {"value": None if account is None else {
                "owner": str(account.owner), "executable": account.executable,
                "lamports": account.lamports, "data": [base64.b64encode(account.data).decode(), "base64"],
            }}
        if method == "getBalance":
            return {"value": self.machine.get_balance(Pubkey.from_string(params[0])) or 0}
        if method == "getLatestBlockhash":
            self.machine.expire_blockhash()
            self.height += 1
            return {"value": {"blockhash": str(self.machine.latest_blockhash()),
                              "lastValidBlockHeight": self.height + 150}}
        if method == "getSlot":
            return self.machine.get_clock().slot
        if method == "getBlockTime":
            return self.machine.get_clock().unix_timestamp
        if method == "getBlockHeight":
            return self.height
        if method == "getFeeForMessage":
            return {"value": 5000}
        if method == "getMinimumBalanceForRentExemption":
            return self.machine.minimum_balance_for_rent_exemption(params[0])
        if method == "getSignatureStatuses":
            return {"value": [{"err": None, "confirmationStatus": "finalized"}
                              if sig in self.history else None for sig in params[0]]}
        if method == "getTransaction":
            return self.history.get(params[0])
        if method == "getSignaturesForAddress":
            return [{"signature": sig, "err": None} for sig, value in self.history.items()
                    if params[0] in value["transaction"]["message"]["accountKeys"]]
        if method == "sendTransaction":
            if self.before_send:
                self.before_send()
            tx = Transaction.from_bytes(base64.b64decode(params[0], validate=True))
            signature = str(tx.signatures[0])
            if signature in self.history:
                return signature
            message = tx.message
            pre = [self.machine.get_balance(key) or 0 for key in message.account_keys]
            result = self.machine.send_transaction(tx)
            if isinstance(result, FailedTransactionMetadata):
                raise ValueError(f"Compiled SBF execution failed: {result}")
            post = [self.machine.get_balance(key) or 0 for key in message.account_keys]
            self.history[signature] = {
                "slot": self.machine.get_clock().slot,
                "transaction": {"signatures": [signature], "message": {
                    "accountKeys": [str(key) for key in message.account_keys],
                    "header": json.loads(message.header.to_json()),
                    "recentBlockhash": str(message.recent_blockhash),
                    "instructions": [{"programIdIndex": ix.program_id_index,
                                      "accounts": list(ix.accounts), "data": b58encode(ix.data)}
                                     for ix in message.instructions],
                }},
                "meta": {"err": None, "fee": 5000, "preBalances": pre, "postBalances": post},
            }
            if self.drop_first_response:
                self.drop_first_response = False
                raise ValueError("Injected lost RPC response after actual finalized execution")
            return signature
        raise AssertionError(f"Unhandled local VM RPC: {method}")


@pytest.fixture(scope="module")
def product_run(tmp_path_factory):
    path = Path(os.getenv("GM_SBF_PATH", ".local/sbf/gradientmine_escrow.so"))
    if not path.is_file():
        pytest.skip("Compiled SBF required; this local VM test is not Devnet deployment")
    root = tmp_path_factory.mktemp("product-vm")
    actors = {name: Identity.create(root / "private" / f"{name}.json")
              for name in ("creator", "worker", "validator")}
    machine, program = LiteSVM(), Keypair().pubkey()
    machine.add_program_from_file(program, path)
    vmclock = machine.get_clock()
    vmclock.unix_timestamp = int(time.time())
    machine.set_clock(vmclock)
    for identity in actors.values():
        result = machine.airdrop(Pubkey.from_string(identity.address), 10_000_000_000)
        assert not isinstance(result, FailedTransactionMetadata)
    rpc = VmRpc(machine)
    chain = Chain(str(program), rpc=rpc)

    def clock():
        return machine.get_clock().unix_timestamp

    def advance(seconds):
        current = machine.get_clock()
        current.unix_timestamp += int(seconds)
        machine.set_clock(current)

    origin = "http://127.0.0.1:8000"
    settings = Settings(root=root / "private" / "server", mode="devnet", origin=origin,
                        program_id=str(program), validator_key=str(root / "private" / "validator.json"))
    app = create_app(settings, clock=clock)
    app.state.market.chain = chain
    build = {"source_commit": "a" * 40, "program_sha256": digest(path.read_bytes()),
             "build_trust": "Local compiled SBF test fixture; no deployment claim"}
    checkpoint = Checkpoint(root / "private" / "harness-state.json", actors["creator"], {
        "origin": origin, "idempotency_key": "actual-product-vm", "pending_funding": None,
        "funding_attempts": [], "job_input": {"title": "Actual ML plus escrow integration",
            "duration_seconds": 60, "reward_lamports": 5_000_000, "minimum_delta": 0.01,
            "parent_job_id": None},
    })
    sent_funding = []

    def before_send():
        state = Checkpoint(checkpoint.path, actors["creator"]).state
        if not rpc.history:
            # First external side effect sees a durable, authenticated funding signature.
            assert state["pending_funding"] is not None
            sent_funding.append(state["pending_funding"]["signature"])

    rpc.before_send = before_send
    with pytest.MonkeyPatch.context() as patch, TestClient(app, base_url=origin) as client:
        import gradientmine.cli as cli
        import gradientmine.chain as chain_module

        patch.setattr(chain_module, "Chain", lambda program_id, rpc_url=None: Chain(program_id, rpc=rpc))
        patch.setattr(cli, "client_for", lambda api_url: (TestClient(app, base_url=origin), origin))

        def worker_runner(job_id):
            sub = cli.worker(argparse.Namespace(
                api=origin, identity=str(root / "private" / "worker.json"), out=str(root / "private" / "worker"),
                job=job_id, program_id=str(program), rpc="http://127.0.0.1:8899", resume=False,
                epochs=60, rank=8, lr=0.03, seed=7, negative_control=False,
            ))
            assert sub["state"] == "REGISTERED"
            return {"kind": "in-process-cli-injection-for-local-vm-test", "device": "cpu"}

        rpc.drop_first_response = True
        with pytest.raises(ValueError, match="lost RPC response"):
            execute_product(client, chain, actors, checkpoint, path.read_bytes(), build,
                            worker_runner, clock=clock, wait=advance, classification="localvm", max_polls=50)
        resumed = Checkpoint(checkpoint.path, actors["creator"])
        assert resumed.state["pending_funding"]["signature"] in rpc.history
        assert "funding" not in resumed.state
        proof, job = execute_product(client, chain, actors, resumed, path.read_bytes(), build,
                                     worker_runner, clock=clock, wait=advance,
                                     classification="localvm", max_polls=50)
        fetched = {}

        def fetch(sha):
            response = client.get(f"/api/artifacts/{sha}")
            assert response.status_code == 200
            fetched[sha] = response.content
            return response.content

        record = export_public(root / "public", proof, job, fetch)
    return {"proof": proof, "job": job, "record": record, "artifacts": fetched, "root": root,
            "chain": chain, "sbf": path.read_bytes(), "actors": actors, "sent_funding": sent_funding}


def test_actual_ml_api_compiled_sbf_registered_receipt_and_exact_payout(product_run):
    result = product_run
    proof, job = result["proof"], result["job"]
    assert job["state"] == "SETTLED"
    assert job["winner"]["eligible"] is True
    assert proof["network"] == "local:litesvm" and proof["mode"] == "localvm"
    assert "not Solana Devnet" in proof["disclosure"]
    for action in ("funding", "registration", "settlement"):
        assert proof[action]["signature"] and "explorer" not in proof[action]
    assert result["sent_funding"] == [proof["funding"]["signature"]]
    assert proof["final_bounty"]["state"] == 1
    assert proof["final_bounty"]["winner"] == result["actors"]["worker"].address
    assert proof["final_bounty"]["receipt_sha256"] == proof["receipt_sha256"]
    sub = job["submissions"][0]
    assert sub["worker_metrics"]["device"] == "cpu"
    assert sub["worker_metrics"]["last_loss"] < sub["worker_metrics"]["first_loss"]
    assert sub["score"]["candidate_accuracy"] > job["baseline_accuracy"]
    assert proof["deployment_before"] == proof["deployment_after"]
    assert proof["program_sha256"] == digest(result["sbf"])
    tx = proof["settlement"]["transaction"]
    index = tx["transaction"]["message"]["accountKeys"].index(proof["worker"])
    assert tx["meta"]["postBalances"][index] - tx["meta"]["preBalances"][index] == 5_000_000
    assert len(result["chain"].rpc.history) == 3


def test_exact_compiled_binary_mismatch_is_rejected(product_run):
    wrong = bytearray(product_run["sbf"])
    wrong[-1] ^= 1
    with pytest.raises(ValueError, match="exact built ELF"):
        product_run["chain"].verify_program(bytes(wrong))


def test_public_export_excludes_private_volume_and_unreferenced_artifacts(product_run, tmp_path):
    result = product_run
    job = copy.deepcopy(result["job"])
    job["private_key"] = "DO NOT EXPORT"
    job["pending_settlement"] = {"private": "DO NOT EXPORT"}
    job["submissions"][0]["private"] = "DO NOT EXPORT"
    # An unrelated private file exists alongside the server; exporter never traverses it.
    unrelated = result["root"] / "private" / "unrelated.json"
    unrelated.write_text('"DO NOT EXPORT"')
    record = export_public(tmp_path / "public", result["proof"], job, result["artifacts"].__getitem__)
    names = {p.name for p in (tmp_path / "public").rglob("*") if p.is_file()}
    assert names == {"run.json", "devnet-smoke.json", *(sha + ".json" for sha in record["artifacts"])}
    assert "DO NOT EXPORT" not in canonical(record).decode()
    assert "private-task.json" not in names and "state.sqlite3" not in names


def test_valid_signature_with_wrong_manifest_provenance_is_rejected(product_run):
    result = product_run
    job = copy.deepcopy(result["job"])
    blobs = dict(result["artifacts"])
    sub = job["submissions"][0]
    manifest = safe_json(blobs[sub["manifest_sha256"]])
    manifest["payload"]["job_id"] = "different-real-bounty"
    altered = result["actors"]["worker"].sign(manifest["payload"])
    raw = canonical(altered)
    sub["manifest_sha256"] = digest(raw)
    blobs[digest(raw)] = raw
    with pytest.raises(ValueError, match="provenance"):
        checked_artifacts(job, blobs.__getitem__)


def test_valid_receipt_signed_by_wrong_validator_is_rejected(product_run):
    result = product_run
    job = copy.deepcopy(result["job"])
    blobs = dict(result["artifacts"])
    sub = job["submissions"][0]
    receipt = safe_json(blobs[sub["receipt_sha256"]])
    raw = canonical(result["actors"]["worker"].sign(receipt["payload"]))
    sub["receipt_sha256"] = digest(raw)
    blobs[digest(raw)] = raw
    with pytest.raises(ValueError, match="expected validator"):
        checked_artifacts(job, blobs.__getitem__)

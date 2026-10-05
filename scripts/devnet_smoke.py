"""Real CPU model-improvement bounty through API, independent CLI and exact Devnet SBF.

Private recovery state is retained on failure. Only checked, bounty-referenced public
artifacts are exported after strict finalized payout verification. LiteSVM tests inject
an RPC adapter and classify their output as local VM evidence, never Devnet evidence.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import json
import os
import re
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx
from solders.transaction import Transaction

from gradientmine.chain import Chain
from gradientmine.cli import login
from gradientmine.crypto import Identity, canonical, digest, safe_json, verify_signed
from gradientmine.store import atomic_write
from scripts.public_evidence import export_public


class ApiError(ValueError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(f"API {status}: {message}")


def api(client, method, path, **kwargs):
    response = client.request(method, path, **kwargs)
    value = response.json()
    if response.is_error:
        raise ApiError(response.status_code, value.get("error", "request failed"))
    return value


class Checkpoint:
    """Creator-authenticated private harness state, durable before remote side effects."""

    def __init__(self, path, identity, initial=None):
        self.path, self.identity = Path(path), identity
        if self.path.exists():
            saved = safe_json(self.path.read_bytes(), limit=2_000_000)
            if not verify_signed(saved) or saved["signer"] != identity.address:
                raise ValueError("Harness checkpoint creator signature failed")
            self.state = saved["payload"]
        elif initial is not None:
            self.state = initial
            self.save()
        else:
            raise ValueError("No harness checkpoint exists to resume")

    def save(self):
        atomic_write(self.path, canonical(self.identity.sign(self.state)))
        if os.name == "posix":
            fd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)


def status(chain, signature):
    value = chain.rpc.call(
        "getSignatureStatuses", [[signature], {"searchTransactionHistory": True}]
    )["value"][0]
    if value is not None and (
        not isinstance(value, dict) or "err" not in value
        or value.get("confirmationStatus") not in {"processed", "confirmed", "finalized"}
    ):
        raise ValueError("Malformed signature status; no success or safe replacement inferred")
    return value


def fund_bounty(client, chain, creator, job, checkpoint, *, wait=time.sleep, attempts=45):
    """Bounded, signed-before-send funding. Expiry plus absence authorizes replacement."""
    saved = checkpoint.state
    for _ in range(attempts):
        pending = saved.get("pending_funding")
        if pending is None:
            pending = chain.sign_intent(
                api(client, "POST", f"/api/jobs/{job['id']}/transaction", json={"action": "fund"}),
                "fund", job, None, creator,
            )
            saved["pending_funding"] = pending
            checkpoint.save()
        checked = chain.validate_signed(
            base64.b64decode(pending["transaction_base64"], validate=True), chain.spec("fund", job)
        )
        if checked["signature"] != pending["signature"]:
            raise ValueError("Funding checkpoint signed bytes differ from signature")
        found = status(chain, pending["signature"])
        if found and found["err"] is None and found["confirmationStatus"] == "finalized":
            evidence = chain.confirm("fund", job, None, pending["signature"])
            api(client, "POST", f"/api/jobs/{job['id']}/confirm", json={
                "action": "fund", "signature": pending["signature"],
            })
            evidence["transaction"] = chain.rpc.transaction(pending["signature"], chain.spec("fund", job))
            saved["funding"] = evidence
            checkpoint.save()
            return evidence
        if found and found["err"] is None:
            wait(2)
            continue
        height = chain.rpc.call("getBlockHeight", [{"commitment": "finalized"}])
        if type(height) is not int or height < 0:
            raise ValueError("Malformed finalized block height")
        if height > pending["last_valid_block_height"]:
            tx = Transaction.from_bytes(base64.b64decode(pending["transaction_base64"], validate=True))
            valid = chain.rpc.call("isBlockhashValid", [
                str(tx.message.recent_blockhash), {"commitment": "finalized"},
            ])["value"]
            if type(valid) is not bool:
                raise ValueError("Malformed finalized blockhash validity")
            # A funded account alone is insufficient; retain signature and never create a duplicate.
            account = chain.rpc.account(chain.bounty_address(job))
            latest = status(chain, pending["signature"])
            absent_or_failed = latest is None or (
                latest["err"] is not None and latest["confirmationStatus"] == "finalized"
            )
            if valid or account is not None or not absent_or_failed:
                raise ValueError("Funding recovery remains ambiguous; original signed evidence retained")
            history = saved.setdefault("funding_attempts", [])
            if len(history) >= 2:
                raise ValueError("Bounded funding replacement limit reached; retain original checkpoint")
            history.append(pending)
            saved["pending_funding"] = None
            checkpoint.save()
            continue
        if found and found["err"] is not None:
            raise ValueError("Funding failed on-chain; original evidence retained until safe expiry")
        chain.send_signed(pending)  # RPC errors propagate; they never mean confirmation.
        wait(2)
    raise ValueError("Funding finalization timed out; retain private volume and resume the same checkpoint")


def balances(chain, actors, bounty=None):
    addresses = {name: actor.address for name, actor in actors.items()}
    if bounty:
        addresses["bounty"] = bounty
    result = {}
    for name, address in addresses.items():
        value = chain.rpc.call("getBalance", [address, {"commitment": "finalized"}])["value"]
        if type(value) is not int or value < 0:
            raise ValueError("Malformed finalized balance")
        result[name] = {"address": address, "lamports": value}
    return result


def execute_product(client, chain, actors, checkpoint, sbf, build, worker_runner, *,
                    clock=time.time, wait=time.sleep, max_polls=240, classification="devnet"):
    """Shared orchestration: actual API/ML/program, with injectable transport for VM tests."""
    saved = checkpoint.state
    creator, worker, validator = (actors[k] for k in ("creator", "worker", "validator"))
    origin = saved["origin"]
    before = chain.verify_program(sbf)
    config = api(client, "GET", "/api/config")
    if (
        config["mode"] != "devnet" or config["origin"] != origin
        or config["validator"] != validator.address or config["program_id"] != chain.program_id
    ):
        raise ValueError("API deployment, origin or named validator differs from the checked harness")
    login(client, creator, origin)
    if "deployment_before" not in saved:
        saved["deployment_before"] = before
        saved["balances_before"] = balances(chain, actors)
        checkpoint.save()
    elif before != saved["deployment_before"]:
        raise ValueError("Deployment changed since the original harness checkpoint; no signing attempted")
    job = api(client, "POST", "/api/jobs", headers={"Idempotency-Key": saved["idempotency_key"]},
              json=saved["job_input"])
    if saved.get("job_id") not in {None, job["id"]}:
        raise ValueError("Idempotent bounty identity differs from saved checkpoint")
    saved["job_id"] = job["id"]
    checkpoint.save()
    job = api(client, "GET", f"/api/jobs/{job['id']}")
    if digest(job["policy"]) != job["policy_sha256"] or job["policy"]["refund_after"] != job["policy"]["deadline"] + 3600:
        raise ValueError("Immutable policy hash or exact refund interval mismatch")
    if not saved.get("funding"):
        fund_bounty(client, chain, creator, job, checkpoint, wait=wait)
    else:
        chain.rpc.transaction(saved["funding"]["signature"], chain.spec("fund", job))
    job = api(client, "GET", f"/api/jobs/{job['id']}")
    if job["state"] == "OPEN":
        saved["worker_execution"] = worker_runner(job["id"])
        checkpoint.save()
    # Worker login/injection can alter the shared test client's authentication.
    login(client, creator, origin)
    for _ in range(max_polls):
        job = api(client, "GET", f"/api/jobs/{job['id']}")
        if job["state"] == "SETTLED":
            break
        if job["state"] in {"NO_WINNER", "REFUNDED"}:
            raise ValueError("Real evaluation selected no payable winner; no payout proof is exported")
        if clock() >= job["policy"]["deadline"]:
            if job["state"] == "OPEN":
                try:
                    api(client, "POST", f"/api/jobs/{job['id']}/evaluate")
                except ApiError as exc:
                    if exc.status != 409:
                        raise
            elif job["state"] in {"EVALUATED", "SETTLING"}:
                # Existing server persists settlement intent before broadcast. An error remains an error.
                route = "recover-settlement" if job["state"] == "SETTLING" else "settle"
                try:
                    api(client, "POST", f"/api/jobs/{job['id']}/{route}")
                except ApiError as exc:
                    if exc.status not in {409, 422}:
                        raise
        wait(2)
    else:
        raise ValueError("Evaluation/payout deadline exceeded; original API and signed state retained")
    winner = job["winner"]
    if not winner or winner["worker"] != worker.address:
        raise ValueError("Actual eligible winner differs from the registered harness worker")
    sub = next(s for s in job["submissions"] if s["id"] == winner["submission_id"])
    registration = chain.confirm("register", job, sub, sub["registration_signature"])
    registration["transaction"] = chain.rpc.transaction(
        sub["registration_signature"], chain.spec("register", job, sub)
    )
    settlement = chain.confirm("settle", job, sub, job["settlement_signature"])
    transaction = chain.rpc.transaction(job["settlement_signature"], chain.spec("settle", job, sub))
    settlement["transaction"] = transaction
    final_bounty, account = chain.read_bounty(job)
    after = chain.verify_program(sbf)
    if after != saved["deployment_before"]:
        raise ValueError("Program deployment/upgrade authority changed during the product run")
    proof = {
        "format": "gradientmine.devnet-product.v1", "executed_at": int(clock()),
        "mode": classification, "network": "solana:devnet" if classification == "devnet" else "local:litesvm",
        "source_commit": build["source_commit"], "program_sha256": digest(sbf), "build": build,
        "genesis": before["genesis"], "program_id": chain.program_id,
        "bounty_address": chain.bounty_address(job),
        "creator": creator.address, "worker": worker.address, "validator": validator.address,
        "policy_sha256": job["policy_sha256"],
        "policy_commitments": {k: job["policy"][k] for k in (
            "parent_sha256", "train_sha256", "validation_sha256", "evaluation_sha256"
        )},
        **{k: sub[k] for k in ("artifact_sha256", "manifest_sha256", "receipt_sha256", "model_sha256")},
        "reward_lamports": job["policy"]["reward_lamports"], "deadline": job["policy"]["deadline"],
        "funding": saved["funding"], "registration": registration, "settlement": settlement,
        "balances_before": saved["balances_before"],
        "balances_after": balances(chain, actors, chain.bounty_address(job)),
        "final_bounty": {**final_bounty, "lamports": account["lamports"]},
        "deployment_before": saved["deployment_before"], "deployment_after": after,
        "worker_execution": saved.get("worker_execution"),
        "disclosure": (
            "Actual CPU PyTorch training and one trusted held-out validator. Independent worker OS process "
            "on the same host in the live harness; injected in-process worker in LiteSVM tests. "
            "No Phantom interaction, GPU/LLM claim, decentralized verification, or proof of training from a signature."
        ),
        "private_keys_exported": False,
    }
    if classification != "devnet":
        for action in ("funding", "registration", "settlement"):
            proof[action].pop("explorer", None)  # VM signatures have no public Explorer transaction.
        proof["disclosure"] += " Local VM execution is not Solana Devnet deployment or payout."
    return proof, job


def source_commit():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def build_manifest(sbf, commit):
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or commit != source_commit():
        raise ValueError("Source commit must match the checked-out full Git commit")
    subprocess.run(["git", "diff", "--exit-code", commit, "--", "program"], check=True, capture_output=True)
    paths = subprocess.check_output(["git", "ls-files", "program"], text=True).splitlines()
    return {
        "format": "gradientmine.sbf-build.v1", "source_commit": commit, "program_sha256": digest(sbf),
        "program_sources_sha256": digest({p: digest(Path(p).read_bytes()) for p in paths}),
        "build_command": "cargo build-sbf --manifest-path program/Cargo.toml --tools-version v1.57 --jobs 2 -- --locked",
        "agave_version": "4.3.0", "platform_tools_version": "v1.57",
        "build_trust": "Builder attestation of a fresh locked build; exact deployed bytes independently checked by RPC",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--program")
    p.add_argument("--creator", type=Path)
    p.add_argument("--worker", type=Path)
    p.add_argument("--validator", type=Path)
    p.add_argument("--sbf", required=True, type=Path)
    p.add_argument("--source-commit", required=True)
    p.add_argument("--build-manifest", required=True, type=Path)
    p.add_argument("--record-build", action="store_true")
    p.add_argument("--out", type=Path)
    p.add_argument("--private-dir", type=Path)
    p.add_argument("--rpc", default="https://api.devnet.solana.com")
    p.add_argument("--reward-lamports", type=int, default=5_000_000)
    p.add_argument("--cutoff-seconds", type=int, default=180)
    p.add_argument("--resume", action="store_true")
    a = p.parse_args(argv)
    sbf = a.sbf.read_bytes()
    build = build_manifest(sbf, a.source_commit)
    if a.record_build:
        atomic_write(a.build_manifest, canonical(build))
        return 0
    for name in ("program", "creator", "worker", "validator", "out", "private_dir"):
        if getattr(a, name) is None:
            p.error(f"--{name.replace('_', '-')} is required for a product run")
    if safe_json(a.build_manifest.read_bytes()) != build:
        raise ValueError("Exact SBF binary/source build manifest mismatch")
    if not 60 <= a.cutoff_seconds <= 900 or not 1_000_000 <= a.reward_lamports <= 50_000_000:
        raise ValueError("Refusing unsupported duration or reward outside small Devnet test bounds")
    actors = {k: Identity.load(getattr(a, k)) for k in ("creator", "worker", "validator")}
    if len({actor.address for actor in actors.values()}) != 3:
        raise ValueError("Creator, worker and validator must be distinct disposable identities")
    a.private_dir = a.private_dir.resolve()
    a.out = a.out.resolve()
    if a.private_dir == a.out or a.private_dir.is_relative_to(a.out) or a.out.is_relative_to(a.private_dir):
        raise ValueError("Public output and private recovery directories must be disjoint")
    if a.out.exists() and any(a.out.iterdir()):
        raise ValueError("Public output already contains evidence; choose a new empty destination")
    a.private_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    state_path = a.private_dir / "harness-state.json"
    if state_path.exists() and not a.resume:
        raise ValueError("Private directory already contains a run; use --resume")
    chain = Chain(a.program, a.rpc)
    chain.verify_program(sbf)  # Verify network and exact deployment before API startup or wallet signing.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    initial = {
        "format": "gradientmine.harness-state.v1", "origin": f"http://127.0.0.1:{port}",
        "actors": {k: v.address for k, v in actors.items()}, "program_id": a.program,
        "rpc": a.rpc, "build": build, "idempotency_key": "devnet-" + uuid.uuid4().hex,
        "job_input": {"title": "Digits: actual measured improvement with Devnet payout",
                      "duration_seconds": a.cutoff_seconds, "reward_lamports": a.reward_lamports,
                      "minimum_delta": 0.01, "parent_job_id": None},
        "pending_funding": None, "funding_attempts": [],
    }
    checkpoint = Checkpoint(state_path, actors["creator"], None if a.resume else initial)
    saved = checkpoint.state
    if any(saved.get(k) != initial[k] for k in ("actors", "program_id", "rpc", "build", "job_input")):
        raise ValueError("Resume identity, program, RPC, build or bounty inputs differ from saved checkpoint")
    origin = saved["origin"]
    port = int(origin.rsplit(":", 1)[1])
    env = {**os.environ, "GM_MODE": "devnet", "GM_RPC_URL": a.rpc, "GM_PROGRAM_ID": a.program,
           "GM_VALIDATOR_KEY": str(a.validator.resolve()), "GM_ORIGIN": origin,
           "GM_DATA_DIR": str(a.private_dir / "server")}
    server = None
    log = (a.private_dir / "server.log").open("a")
    complete = False
    try:
        with httpx.Client(base_url=origin, timeout=100, follow_redirects=False) as client:
            try:
                ready = client.get("/health").status_code == 200
            except httpx.HTTPError:
                ready = False
            if not ready:
                server = subprocess.Popen(
                    [sys.executable, "-m", "gradientmine.cli", "serve", "--port", str(port)],
                    env=env, stdout=log, stderr=subprocess.STDOUT,
                )
                for _ in range(200):
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    if server.poll() is not None:
                        raise ValueError("Owned API process exited; see retained private server.log")
                    time.sleep(0.1)
                else:
                    raise ValueError("Owned API process did not become ready; private data retained")
                saved["server_pid"] = server.pid
                checkpoint.save()

            def worker_runner(job_id):
                worker_out = a.private_dir / "worker"
                command = [sys.executable, "-m", "gradientmine.cli", "worker", "--api", origin,
                           "--job", job_id, "--identity", str(a.worker.resolve()),
                           "--program-id", a.program, "--rpc", a.rpc, "--out", str(worker_out)]
                if (worker_out / "worker-state.json").exists():
                    command.append("--resume")
                with (a.private_dir / "worker.log").open("a") as worker_log:
                    process = subprocess.Popen(command, stdout=worker_log, stderr=subprocess.STDOUT)
                    saved["worker_execution"] = {
                        "kind": "independent-cli-os-process", "pid": process.pid, "exit_code": None,
                        "device": "cpu", "same_host": True,
                    }
                    checkpoint.save()
                    try:
                        code = process.wait(timeout=150)
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                        raise ValueError("Worker timed out; signed checkpoint retained for --resume") from None
                if code:
                    raise ValueError("Actual worker failed; inspect retained private worker.log and resume")
                return {"kind": "independent-cli-os-process", "pid": process.pid, "exit_code": code,
                        "device": "cpu", "same_host": True}

            proof, job = execute_product(client, chain, actors, checkpoint, sbf, build, worker_runner)

            def fetch(sha):
                response = client.get(f"/api/artifacts/{sha}")
                response.raise_for_status()
                return response.content

            record = export_public(a.out, proof, job, fetch)
            complete = True
            print(json.dumps({"evidence": str(a.out / "devnet-smoke.json"), "state": job["state"],
                              "program_sha256": record["program_sha256"],
                              "transactions": {k: record[k]["explorer"] for k in (
                                  "funding", "registration", "settlement")}}, indent=2))
    finally:
        # Preserve one API and its original private volume on failure for bounded --resume recovery.
        # Never stop a pre-existing process discovered during resume.
        if complete and server is not None:
            server.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                server.wait(timeout=5)
            if server.poll() is None:
                server.kill()
                server.wait()
        log.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, httpx.HTTPError, subprocess.CalledProcessError) as exc:
        print(f"Devnet product proof blocked: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

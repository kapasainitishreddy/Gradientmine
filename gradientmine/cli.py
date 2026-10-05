"""Reproducible local demo and independently running, wallet-authenticated training workers."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import numpy as np

from .crypto import Identity, canonical, digest, safe_json, validate_auth_challenge, verify_signed
from .ml import merge_adapter, predict, train_adapter
from .store import atomic_write


def request(client, method, url, **kwargs):
    response = client.request(method, url, **kwargs)
    try:
        result = response.json()
    except ValueError as exc:
        raise ValueError(f"Server returned non-JSON response ({response.status_code})") from exc
    if response.is_error:
        raise ValueError(f"{response.status_code}: {result.get('error', 'request failed')}")
    return result


def login(client, identity, origin):
    challenge = request(client, "POST", "/api/auth/challenge", json={"address": identity.address})
    message = validate_auth_challenge(challenge, origin, identity.address)
    session = request(
        client,
        "POST",
        "/api/auth/verify",
        json={"nonce": challenge["nonce"], "signature": identity.sign_bytes(message)},
    )
    client.headers["Authorization"] = "Bearer " + session["token"]
    return session


def client_for(url):
    from .config import Settings

    origin = Settings(origin=url).origin
    return httpx.Client(base_url=origin, timeout=100, follow_redirects=False), origin


def make_submission(identity, job, package, *, epochs=60, rank=8, lr=0.03, seed=7, negative_control=False):
    policy = job["policy"]
    for item, key in [
        ("parent", "parent_sha256"),
        ("train", "train_sha256"),
        ("validation", "validation_sha256"),
    ]:
        if digest(package[item]) != policy[key]:
            raise ValueError(f"Training package integrity mismatch: {item}")
    if digest(policy) != job["policy_sha256"] or package["policy_sha256"] != job["policy_sha256"]:
        raise ValueError("Bounty policy integrity failure")
    start = time.monotonic()
    adapter, losses = train_adapter(
        package["parent"],
        package["train"],
        epochs=epochs,
        rank=rank,
        lr=lr,
        seed=seed,
        shuffle_labels=negative_control,
    )
    after = predict(merge_adapter(package["parent"], adapter), package["validation"]["x"])
    score = float(np.mean(after == np.asarray(package["validation"]["y"])))
    payload = {
        "format": "gradientmine.submission.v1",
        "job_id": job["id"],
        "policy_sha256": job["policy_sha256"],
        "parent_sha256": policy["parent_sha256"],
        "artifact_sha256": digest(adapter),
        "training_data_sha256": policy["train_sha256"],
        "recipe": {
            "epochs": epochs,
            "rank": rank,
            "learning_rate": lr,
            "seed": seed,
            "negative_control": negative_control,
            "implementation": "gradientmine-pytorch-head-lora-v1",
        },
        "worker_metrics": {
            "public_validation_accuracy": score,
            "first_loss": losses[0],
            "last_loss": losses[-1],
            "elapsed_seconds": round(time.monotonic() - start, 4),
            "process_id": os.getpid(),
            "device": "cpu",
            "negative_control": negative_control,
        },
        "submitted_at": int(time.time()),
    }
    return adapter, identity.sign(payload), losses


def worker(args):
    from .worker_recovery import load_state

    identity = Identity.load(Path(args.identity))
    client, origin = client_for(args.api)
    out = Path(args.out) if args.out else None
    resume = getattr(args, "resume", False)
    if resume and out is None:
        raise ValueError("--resume requires --out with the original worker checkpoint")
    with contextlib.ExitStack() as stack:
        stack.enter_context(client)
        if out is not None:
            out.mkdir(parents=True, exist_ok=True)
            # Prevent two local processes from concurrently replaying one checkpoint.
            if os.name == "posix":
                import fcntl

                lock = stack.enter_context((out / ".worker.lock").open("a"))
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise ValueError("This worker output directory is already in use") from exc
            if not resume and (out / "worker-state.json").exists():
                raise ValueError("Output contains a worker checkpoint; use --resume to retain its evidence")
        state = load_state(out, identity) if resume else None
        if state is not None and (
            state["origin"] != origin
            or state["job"]["id"] != args.job
            or state["program_id"] != args.program_id
            or state["rpc"] != args.rpc
        ):
            raise ValueError("Checkpoint API, job, deployment or RPC binding differs from this invocation")
        return _worker_session(args, identity, client, origin, out, state)


def _worker_session(args, identity, client, origin, out, state):
    from .worker_recovery import recover_registration, save_state, validate_submission

    def persist():
        if out is not None:
            save_state(out, state, identity)

    def evidence():
        if out is not None:
            for name, key in [("artifact", "artifact"), ("manifest", "manifest"), ("losses", "losses")]:
                atomic_write(out / f"{name}.json", canonical(state[key]))
            if state["submission"] is not None:
                atomic_write(out / "submission.json", canonical(state["submission"]))
            if state["pending"] is not None:
                atomic_write(out / "pending-registration.json", canonical(state["pending"]))

    config = request(client, "GET", "/api/config")
    if config["origin"] != origin:
        raise ValueError("API origin configuration differs from the requested address")
    if config["mode"] not in {"local", "devnet"}:
        raise ValueError("Unrecognized API mode")
    if config["mode"] == "devnet":
        if not args.program_id or args.program_id != config["program_id"]:
            raise ValueError(
                "Devnet worker requires --program-id with the independently checked deployment address"
            )
        if out is None:
            raise ValueError("Devnet worker requires --out to persist registration recovery before broadcast")
    if state is not None and state["mode"] != config["mode"]:
        raise ValueError("Checkpoint mode differs from the API; no submission or signing attempted")
    login(client, identity, origin)
    job = request(client, "GET", f"/api/jobs/{args.job}")
    if state is not None:
        if any(job[k] != state["job"][k] for k in ("id", "creator", "policy", "policy_sha256")):
            raise ValueError("Checkpoint bounty policy differs from the live API")
        print(f"Resuming saved artifact {digest(state['artifact'])}; no retraining", flush=True)
    else:
        if any(sub["worker"] == identity.address for sub in job["submissions"]):
            raise ValueError("This wallet already submitted; resume its original --out checkpoint")
        package = request(client, "GET", f"/api/jobs/{args.job}/training")
        print(
            f"Worker {identity.address}\nProcess {os.getpid()} · actual PyTorch training on CPU", flush=True
        )
        adapter, manifest, losses = make_submission(
            identity,
            job,
            package,
            epochs=args.epochs,
            rank=args.rank,
            lr=args.lr,
            seed=args.seed,
            negative_control=args.negative_control,
        )
        state = {
            "format": "gradientmine.worker-state.v1",
            "origin": origin,
            "mode": config["mode"],
            "program_id": args.program_id,
            "rpc": args.rpc,
            "worker": identity.address,
            "job": {k: job[k] for k in ("id", "creator", "policy", "policy_sha256")},
            "artifact": adapter,
            "manifest": manifest,
            "losses": losses,
            "submission": None,
            "pending": None,
            "attempts": [],
            "stage": "trained",
        }
        # The original signed artifact survives a lost submission response or process crash.
        persist()
        evidence()
        print(
            f"Loss {losses[0]:.6f} → {losses[-1]:.6f}; public validation {manifest['payload']['worker_metrics']['public_validation_accuracy']:.4f}",
            flush=True,
        )
    existing = [sub for sub in job["submissions"] if sub["worker"] == identity.address]
    if len(existing) > 1:
        raise ValueError("API returned duplicate wallet submissions; refusing recovery")
    if existing:
        state["submission"] = validate_submission(existing[0], state)
    elif state["submission"] is not None:
        raise ValueError("Saved submission is missing from the API; refusing a duplicate upload")
    else:
        state["submission"] = validate_submission(
            request(
                client,
                "POST",
                f"/api/jobs/{args.job}/submissions",
                json={"artifact": state["artifact"], "manifest": state["manifest"]},
            ),
            state,
        )
    if state["stage"] == "trained":
        state["stage"] = "submitted"
    persist()
    evidence()
    sub = state["submission"]
    if config["mode"] == "devnet":
        from .chain import Chain

        chain = Chain(args.program_id, args.rpc)

        def intent():
            return request(
                client,
                "POST",
                f"/api/jobs/{args.job}/transaction",
                json={"action": "register", "submission_id": sub["id"]},
            )

        def confirm(signature):
            if sub.get("registration_signature") == signature and sub.get("state") != "AWAITING_REGISTRATION":
                return
            request(
                client,
                "POST",
                f"/api/jobs/{args.job}/confirm",
                json={"action": "register", "submission_id": sub["id"], "signature": signature},
            )

        stage = recover_registration(chain, state, identity, intent, confirm, persist)
        evidence()
        if stage != "finalized":
            pending = state["pending"]
            if stage == "failed":
                raise ValueError(
                    f"Registration failed on-chain: {pending['signature']}. Evidence retained; "
                    "resume after finalized blockhash expiry for a safe replacement."
                )
            if (
                stage == "unknown"
                and chain.rpc.call("getBlockHeight", [{"commitment": "finalized"}])
                > pending["last_valid_block_height"]
            ):
                raise ValueError(
                    "Registration status remains unknown; blockhash still valid. Retain --out and resume."
                )
            # A timeout preserves the checkpoint and never implies confirmation.
            chain.rpc.wait(pending["signature"])
            stage = recover_registration(chain, state, identity, intent, confirm, persist)
        if stage != "finalized":
            raise ValueError("Registration remains unresolved; retain --out and retry with --resume")
        if sub["state"] == "AWAITING_REGISTRATION":
            sub["state"] = "REGISTERED"
        sub["registration_signature"] = sub.get("registration_signature") or state["pending"]["signature"]
        print(f"Registration finalized: {sub['registration_signature']}", flush=True)
    state["stage"] = "complete"
    persist()
    evidence()
    print(
        f"Submitted {sub['artifact_sha256']}; held-out evaluation follows the bounty policy. No payout is inferred.",
        flush=True,
    )
    return sub


def demo(args):
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "run.json").exists():
        raise ValueError("Output already contains a run; choose a new directory to preserve evidence")
    identities = [Identity.create(out / "private" / f"wallet-{i}.json") for i in range(4)]
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    env = {
        **os.environ,
        "GM_MODE": "local",
        "GM_DATA_DIR": str(out / "private" / "server"),
        "GM_ORIGIN": origin,
    }
    log = (out / "server.log").open("w")
    server = subprocess.Popen(
        [sys.executable, "-m", "gradientmine.cli", "serve", "--port", str(port)],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    workers = []
    try:
        with httpx.Client(base_url=origin, timeout=100) as client:
            for _ in range(200):
                try:
                    if client.get("/health").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if server.poll() is not None:
                    raise ValueError("Demo server exited; see server.log")
                time.sleep(0.1)
            else:
                raise ValueError("Demo server did not become ready")
            login(client, identities[0], origin)
            job = request(
                client,
                "POST",
                "/api/jobs",
                headers={"Idempotency-Key": "reproducible-demo"},
                json={
                    "title": "Digits: pay only for measured improvement",
                    "duration_seconds": 20,
                    "reward_lamports": 0,
                    "minimum_delta": 0.01,
                },
            )
            for i in range(1, 4):
                worker_out = out / f"worker-{i}"
                worker_out.mkdir()
                worker_log = (worker_out / "worker.log").open("w")
                command = [
                    sys.executable,
                    "-m",
                    "gradientmine.cli",
                    "worker",
                    "--api",
                    origin,
                    "--job",
                    job["id"],
                    "--identity",
                    str(out / "private" / f"wallet-{i}.json"),
                    "--seed",
                    str(6 + i),
                    "--out",
                    str(worker_out),
                ]
                if i == 3:
                    command += ["--negative-control"]
                process = subprocess.Popen(command, stdout=worker_log, stderr=subprocess.STDOUT)
                workers.append((process, worker_log, command))
            for process, worker_log, command in workers:
                result = process.wait(timeout=90)
                worker_log.close()
                if result:
                    raise ValueError(
                        f"Worker process {process.pid} failed ({result}); inspect its worker.log"
                    )
            while time.time() <= job["policy"]["deadline"]:
                time.sleep(0.2)
            request(client, "POST", f"/api/jobs/{job['id']}/evaluate")
            detail = request(client, "GET", f"/api/jobs/{job['id']}")
            artifacts = set([detail["policy_sha256"], detail["policy"]["parent_sha256"]])
            for sub in detail["submissions"]:
                artifacts.update(
                    sub[k]
                    for k in ("artifact_sha256", "manifest_sha256", "receipt_sha256", "model_sha256")
                    if sub.get(k)
                )
            for sha in sorted(artifacts):
                response = client.get(f"/api/artifacts/{sha}")
                response.raise_for_status()
                if digest(response.content) != sha:
                    raise ValueError("Downloaded evidence hash mismatch")
                atomic_write(out / "artifacts" / f"{sha}.json", response.content)
                value = response.json()
                if "signature" in value and not verify_signed(value):
                    raise ValueError("Downloaded receipt or manifest signature failed")
            run = {
                "format": "gradientmine.recorded-run.v1",
                "recorded_at": int(time.time()),
                "mode": "local",
                "network": "No blockchain transactions in this run",
                "workers": [{"pid": p.pid, "exit_code": p.returncode} for p, _, _ in workers],
                "disclosure": "Three independent OS processes on one host, real CPU head-LoRA training. Third worker is a disclosed shuffled-label negative control. Not three independent machines or a fraud detector.",
                "job": detail,
                "artifacts": sorted(artifacts),
            }
            atomic_write(out / "run.json", canonical(run))
            print(
                json.dumps(
                    {
                        "run": str(out / "run.json"),
                        "state": detail["state"],
                        "winner": detail["winner"],
                        "worker_processes": run["workers"],
                        "on_chain": False,
                    },
                    indent=2,
                )
            )
            return run
    finally:
        for process, worker_log, _ in workers:
            if process.poll() is None:
                process.terminate()
            if not worker_log.closed:
                worker_log.close()
        server.terminate()
        with __import__("contextlib").suppress(subprocess.TimeoutExpired):
            server.wait(timeout=5)
        if server.poll() is None:
            server.kill()
        log.close()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="gradientmine",
        description="Measured model improvement with explicit local / Solana Devnet modes",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    identity = commands.add_parser(
        "identity", help="Create a locally stored Ed25519 identity; never share its file"
    )
    identity.add_argument("--out", required=True)
    serve = commands.add_parser("serve", help="Start one API/validator process with durable local storage")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    work = commands.add_parser(
        "worker", help="Fetch verified training inputs, actually train and submit a signed artifact"
    )
    work.add_argument("--api", required=True)
    work.add_argument("--job", required=True)
    work.add_argument("--identity", required=True)
    work.add_argument("--epochs", type=int, default=60)
    work.add_argument("--rank", type=int, default=8)
    work.add_argument("--lr", type=float, default=0.03)
    work.add_argument("--seed", type=int, default=7)
    work.add_argument(
        "--negative-control",
        action="store_true",
        help="Disclosed shuffled-label experiment, never called a detected cheater",
    )
    work.add_argument("--out")
    work.add_argument(
        "--resume",
        action="store_true",
        help="Resume the signed public checkpoint in --out without retraining",
    )
    work.add_argument("--program-id")
    work.add_argument("--rpc", default="https://api.devnet.solana.com")
    local = commands.add_parser(
        "demo", help="Run three real worker processes through the local API; no pretend tokens"
    )
    local.add_argument("--out", required=True)
    verify = commands.add_parser("verify", help="Independently verify a signed receipt or worker manifest")
    verify.add_argument("file")
    refund = commands.add_parser(
        "refund-address", help="Refund directly from public on-chain bounty data; coordinator not required"
    )
    refund.add_argument("--bounty", required=True)
    refund.add_argument("--program", required=True)
    refund.add_argument("--identity", required=True)
    refund.add_argument("--rpc", default="https://api.devnet.solana.com")
    refund.add_argument("--out", default="refund-public-receipt.json")
    verify.add_argument(
        "--expected-signer",
        help="Require a known validator/worker public address, not merely any valid signature",
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "identity":
            print(Identity.create(Path(args.out)).address)
        elif args.command == "serve":
            import uvicorn
            from .api import create_app

            uvicorn.run(
                create_app(scheduler=True), host=args.host, port=args.port, workers=1, access_log=False
            )
        elif args.command == "worker":
            worker(args)
        elif args.command == "demo":
            demo(args)
        elif args.command == "refund-address":
            from .emergency import refund_address

            print(
                json.dumps(
                    refund_address(args.bounty, args.program, args.identity, args.rpc, args.out), indent=2
                )
            )
        elif args.command == "verify":
            value = safe_json(Path(args.file).read_bytes())
            if not verify_signed(value) or (
                args.expected_signer and value.get("signer") != args.expected_signer
            ):
                raise ValueError("Signature or canonical payload verification failed")
            print(
                f"Verified signature by {value['signer']}. This authenticates the statement, not its scientific truth."
            )
    except (ValueError, OSError, httpx.HTTPError, subprocess.TimeoutExpired) as exc:
        print(f"GradientMine: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

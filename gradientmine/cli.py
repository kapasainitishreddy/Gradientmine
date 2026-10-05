"""Reproducible local demo and independently running, wallet-authenticated training workers."""

from __future__ import annotations

import argparse
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
    identity = Identity.load(Path(args.identity))
    client, origin = client_for(args.api)
    with client:
        config = request(client, "GET", "/api/config")
        if config["origin"] != origin:
            raise ValueError("API origin configuration differs from the requested address")
        if config["mode"] == "devnet" and (not args.program_id or args.program_id != config["program_id"]):
            raise ValueError(
                "Devnet worker requires --program-id with the independently checked deployment address"
            )
        login(client, identity, origin)
        job = request(client, "GET", f"/api/jobs/{args.job}")
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
        print(
            f"Loss {losses[0]:.6f} → {losses[-1]:.6f}; public validation {manifest['payload']['worker_metrics']['public_validation_accuracy']:.4f}",
            flush=True,
        )
        sub = request(
            client,
            "POST",
            f"/api/jobs/{args.job}/submissions",
            json={"artifact": adapter, "manifest": manifest},
        )
        if config["mode"] == "devnet":
            from .chain import Chain

            chain = Chain(args.program_id, args.rpc)
            intent = request(
                client,
                "POST",
                f"/api/jobs/{args.job}/transaction",
                json={"action": "register", "submission_id": sub["id"]},
            )
            pending = chain.sign_intent(intent, "register", job, sub, identity)
            if args.out:
                atomic_write(Path(args.out) / "pending-registration.json", canonical(pending))
            chain.send_signed(pending)
            request(
                client,
                "POST",
                f"/api/jobs/{args.job}/confirm",
                json={
                    "action": "register",
                    "submission_id": sub["id"],
                    "signature": pending["signature"],
                },
            )
            print(f"Registration finalized: {pending['signature']}", flush=True)
        if args.out:
            out = Path(args.out)
            atomic_write(out / "artifact.json", canonical(adapter))
            atomic_write(out / "manifest.json", canonical(manifest))
            atomic_write(out / "submission.json", canonical(sub))
            atomic_write(out / "losses.json", canonical(losses))
        print(
            f"Submitted {sub['artifact_sha256']}; hidden evaluation waits for the cutoff. No payout is inferred.",
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
    work.add_argument("--program-id")
    work.add_argument("--rpc", default="https://api.devnet.solana.com")
    local = commands.add_parser(
        "demo", help="Run three real worker processes through the local API; no pretend tokens"
    )
    local.add_argument("--out", required=True)
    verify = commands.add_parser("verify", help="Independently verify a signed receipt or worker manifest")
    verify.add_argument("file")
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
        elif args.command == "verify":
            value = safe_json(Path(args.file).read_bytes())
            if not verify_signed(value):
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

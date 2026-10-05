"""Durable, single-validator marketplace. All economic state is explicitly mode-labelled."""

from __future__ import annotations

import json
import re
import secrets
import threading
import time
import uuid
from collections import OrderedDict
from pathlib import Path

import numpy as np

from .config import Settings
from .crypto import (
    Identity,
    authentication_message,
    canonical,
    digest,
    safe_json,
    validate_address,
    verify_bytes,
    verify_signed,
)
from .ml import dataset_json, make_task, merge_adapter, predict, validate_adapter
from .scoring import assess, select_winner
from .store import Store, atomic_write


class Problem(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)


class Marketplace:
    """One server, one durable volume, one named validator. Never a consensus claim."""

    def __init__(self, settings: Settings, clock=time.time):
        self.settings, self.clock = settings, clock
        self.root = Path(settings.root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir(exist_ok=True, mode=0o700)
        key = Path(settings.validator_key) if settings.validator_key else self.root / "validator.json"
        if settings.validator_key and not key.is_file():
            raise ValueError("Configured validator identity does not exist; generate it locally first")
        self.validator = Identity.load(key) if key.exists() else Identity.create(key)
        self.store = Store(self.root / "state.sqlite3")
        self.lock = threading.RLock()
        self.rates = OrderedDict()
        self.task = self._task()
        self.put_artifact(self.task["model"])
        self.chain = None
        if settings.mode == "devnet":
            from .chain import Chain

            if not settings.program_id:
                raise ValueError(
                    "Devnet requires GM_PROGRAM_ID. Local mode never represents on-chain activity."
                )
            self.chain = Chain(settings.program_id, settings.rpc_url)

    def _task(self):
        path = self.root / "private-task.json"
        if path.exists():
            saved = safe_json(path.read_bytes(), limit=5_000_000)
            if saved["seed"] != self.settings.task_seed:
                raise ValueError("Do not change the task seed of a persisted marketplace")
            task = saved["task"]
        else:
            generated = make_task(self.settings.task_seed)
            task = {k: dataset_json(generated[k]) for k in ("train", "validation", "test")}
            task.update(model=generated["model"], manifest=generated["manifest"])
            atomic_write(path, canonical({"seed": self.settings.task_seed, "task": task}))
        m = task["manifest"]
        for key, commitment in [
            ("train", "train_sha256"),
            ("validation", "validation_sha256"),
            ("test", "evaluation_sha256"),
        ]:
            if digest(task[key]) != m[commitment]:
                raise ValueError("Private benchmark integrity failure; refusing to start")
        if digest(task["model"]) != m["parent_sha256"]:
            raise ValueError("Baseline integrity failure; refusing to start")
        return task

    def put_artifact(self, value):
        raw = canonical(value)
        sha = digest(raw)
        path = self.artifacts / f"{sha}.json"
        if path.exists():
            if digest(path.read_bytes()) != sha:
                raise Problem(503, "Artifact store integrity failure")
        else:
            atomic_write(path, raw)
        return sha

    def artifact_bytes(self, sha):
        if not re.fullmatch(r"[0-9a-f]{64}", sha or ""):
            raise Problem(404, "Artifact not found")
        path = self.artifacts / f"{sha}.json"
        if not path.is_file():
            raise Problem(404, "Artifact not found")
        raw = path.read_bytes()
        if digest(raw) != sha:
            raise Problem(503, "Artifact integrity failure; evaluation and payout are blocked")
        return raw

    def artifact(self, sha):
        return safe_json(self.artifact_bytes(sha), limit=262144)

    def rate(self, key, limit, period=60):
        with self.lock:
            now = self.clock()
            times = [v for v in self.rates.pop(key, []) if v > now - period]
            if len(times) >= limit:
                self.rates[key] = times
                raise Problem(429, "Rate limit reached. Wait one minute before retrying.")
            self.rates[key] = [*times, now]
            while len(self.rates) > 4096:
                self.rates.popitem(last=False)

    def challenge(self, address, ip="local"):
        validate_address(address)
        self.rate(("nonce-ip", ip), 40)
        self.rate(("nonce-wallet", address), 12)
        nonce = secrets.token_urlsafe(32)
        expires = int(self.clock()) + 300
        message = authentication_message(self.settings.origin, address, nonce, expires)
        with self.store.transaction() as db:
            db.execute("DELETE FROM nonces WHERE expires<?", (self.clock() - 60,))
            db.execute("DELETE FROM sessions WHERE expires<?", (self.clock(),))
            db.execute(
                "INSERT INTO nonces(nonce,address,message,expires) VALUES(?,?,?,?)",
                (nonce, address, message, expires),
            )
        return {"nonce": nonce, "expires_at": expires, "message": message}

    def authenticate(self, nonce, signature, ip="local"):
        self.rate(("auth-ip", ip), 60)
        with self.store.transaction() as db:
            row = db.execute("SELECT * FROM nonces WHERE nonce=?", (nonce,)).fetchone()
            if not row or row["used"] or self.clock() >= row["expires"]:
                raise Problem(401, "Authentication challenge expired or already used")
            expected_message = authentication_message(
                self.settings.origin, row["address"], nonce, int(row["expires"])
            )
            if row["message"] != expected_message:
                raise Problem(401, "Authentication challenge does not match this deployment")
            if not verify_bytes(row["address"], row["message"].encode(), signature):
                raise Problem(401, "Invalid wallet signature")
            db.execute("UPDATE nonces SET used=1 WHERE nonce=?", (nonce,))
            token = secrets.token_urlsafe(32)
            expires = int(self.clock()) + 3600
            db.execute(
                "INSERT INTO sessions VALUES(?,?,?)", (digest(token.encode()), row["address"], expires)
            )
        return {"token": token, "address": row["address"], "expires_at": expires}

    def session(self, header):
        if not isinstance(header, str) or not header.startswith("Bearer ") or len(header) > 128:
            raise Problem(401, "Connect a wallet and sign the authentication message first")
        token_hash = digest(header[7:].encode())
        with self.store.connect() as db:
            row = db.execute(
                "SELECT address,expires FROM sessions WHERE token_hash=?", (token_hash,)
            ).fetchone()
        if not row or self.clock() >= row["expires"]:
            raise Problem(401, "Session expired; reconnect and sign a new authentication message")
        return row["address"]

    def logout(self, header):
        self.session(header)
        with self.store.transaction() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (digest(header[7:].encode()),))

    def config(self):
        return {
            "name": "GradientMine",
            "version": "0.2.0",
            "mode": self.settings.mode,
            "origin": self.settings.origin,
            "validator": self.validator.address,
            "program_id": self.settings.program_id or None,
            "currency": "Devnet SOL (no monetary value)" if self.chain else "No payment: local verification",
            "trust": "One named validator evaluates and authorizes payouts. Not decentralized verification.",
            "task": self.task["manifest"],
            "max_candidates": 8,
            "registration_grace_seconds": 120 if self.chain else 0,
            "chain_verified": False,  # checked on each transaction, never inferred from configuration
        }

    def _job(self, db, job_id):
        job = self.store.job(db, job_id)
        if not job:
            raise Problem(404, "Bounty not found")
        return job

    def create_job(self, creator, values, idempotency_key=None):
        now = int(self.clock())
        duration = values["duration_seconds"]
        reward = values["reward_lamports"]
        if self.chain:
            if not 60 <= duration <= 86400 or not 1_000_000 <= reward <= 1_000_000_000:
                raise Problem(422, "Devnet supports 60–86400 seconds and 0.001–1 Devnet SOL rewards")
        elif reward != 0:
            raise Problem(422, "Local mode has no token or monetary rewards. Set reward_lamports to zero.")
        if idempotency_key is not None and not re.fullmatch(r"[A-Za-z0-9_-]{8,100}", idempotency_key):
            raise Problem(422, "Idempotency-Key must contain 8–100 letters, digits, underscores or hyphens")
        request_hash = digest(values)
        with self.lock, self.store.transaction() as db:
            if idempotency_key:
                prior = db.execute(
                    "SELECT document,request_hash FROM jobs WHERE creator=? AND idempotency_key=?",
                    (creator, idempotency_key),
                ).fetchone()
                if prior:
                    if prior["request_hash"] != request_hash:
                        raise Problem(409, "Idempotency key was already used for a different request")
                    return json.loads(prior["document"])
            if db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] >= self.settings.max_jobs:
                raise Problem(429, "This deployment has reached its bounty capacity")
            parent = self.task["model"]
            lineage = []
            if values.get("parent_job_id"):
                ancestor = self._job(db, values["parent_job_id"])
                required = "SETTLED" if self.chain else "EVALUATED"
                if ancestor["state"] != required or not ancestor.get("winner"):
                    raise Problem(
                        409, "Choose a completed bounty with an eligible winning model as the parent"
                    )
                parent = self.artifact(ancestor["winner"]["model_sha256"])
                lineage = [
                    *ancestor["lineage"],
                    {
                        "job_id": ancestor["id"],
                        "model_sha256": digest(parent),
                        "worker": ancestor["winner"]["worker"],
                    },
                ]
            parent_sha = self.put_artifact(parent)
            policy = {
                "format": "gradientmine.policy.v1",
                "task": "digits-lora-v1",
                "parent_sha256": parent_sha,
                "parent_job_id": values.get("parent_job_id"),
                "train_sha256": self.task["manifest"]["train_sha256"],
                "validation_sha256": self.task["manifest"]["validation_sha256"],
                "evaluation_sha256": self.task["manifest"]["evaluation_sha256"],
                "validator": self.validator.address,
                "mode": self.settings.mode,
                "program_id": self.settings.program_id or None,
                "deadline": now + duration,
                "refund_after": now + duration + 3600,
                "registration_evidence_grace_seconds": 120 if self.chain else 0,
                "reward_lamports": reward,
                "minimum_delta": values["minimum_delta"],
                "metric": "accuracy",
                "max_candidates": 8,
                "tie_break": "artifact_sha256_ascending",
                "statistical_rule": "paired-multinomial-bootstrap-v1",
                "bootstrap_resamples": 20000,
                "familywise_alpha": 0.05,
                "bootstrap_seed": 7301,
                "verification": "trusted-validator-heldout-evaluation",
                "baseline_disclosure": self.task["manifest"]["baseline_training"],
                "benchmark_warning": self.task["manifest"]["warning"],
            }
            job = {
                "id": str(uuid.uuid4()),
                "creator": creator,
                "title": values["title"].strip(),
                "created_at": now,
                "mode": self.settings.mode,
                "policy": policy,
                "policy_sha256": self.put_artifact(policy),
                "state": "AWAITING_FUNDING" if self.chain else "OPEN",
                "lineage": lineage,
                "winner": None,
                "funding_signature": None,
                "settlement_signature": None,
                "refund_signature": None,
            }
            if self.chain:
                job["bounty_address"] = self.chain.bounty_address(job)
            db.execute(
                "INSERT INTO jobs VALUES(?,?,?,?,?)",
                (job["id"], creator, idempotency_key, request_hash, canonical(job).decode()),
            )
            self.store.event(
                db,
                job["id"],
                now,
                "CREATED",
                "Immutable evaluation policy committed; reward not yet escrowed"
                if self.chain
                else "Local bounty opened; no funds or blockchain transaction",
            )
        return job

    def jobs(self):
        with self.store.connect() as db:
            return [
                json.loads(r[0])
                for r in db.execute("SELECT document FROM jobs ORDER BY rowid DESC LIMIT 100")
            ]

    def detail(self, job_id):
        with self.store.connect() as db:
            job = self._job(db, job_id)
            subs = self.store.submissions(db, job_id)
            events = [
                dict(r)
                for r in db.execute(
                    "SELECT seq,created,kind,message FROM events WHERE job_id=? ORDER BY seq", (job_id,)
                )
            ]
        # No submission includes test predictions or labels. Scoring only exists after the cutoff.
        return {**job, "submissions": subs, "events": events, "server_time": self.clock()}

    def training(self, job_id):
        job = self.detail(job_id)
        return {
            "job_id": job_id,
            "policy": job["policy"],
            "policy_sha256": job["policy_sha256"],
            "parent": self.artifact(job["policy"]["parent_sha256"]),
            "train": self.task["train"],
            "validation": self.task["validation"],
            "manifest": self.task["manifest"],
        }

    def submit(self, job_id, worker, adapter, envelope):
        if worker == self.validator.address:
            raise Problem(403, "The named validator cannot participate as a worker")
        if not verify_signed(envelope) or envelope.get("signer") != worker:
            raise Problem(422, "Submission requires a valid signature from the authenticated worker")
        payload = envelope["payload"]
        if not isinstance(payload, dict) or set(payload) != {
            "format",
            "job_id",
            "policy_sha256",
            "parent_sha256",
            "artifact_sha256",
            "training_data_sha256",
            "recipe",
            "worker_metrics",
            "submitted_at",
        }:
            raise Problem(422, "Unexpected submission manifest fields")
        if len(canonical(envelope)) > 16384:
            raise Problem(422, "Submission manifest is too large")
        if payload["format"] != "gradientmine.submission.v1" or payload["job_id"] != job_id:
            raise Problem(422, "Manifest belongs to a different protocol or bounty")
        with self.lock, self.store.transaction() as db:
            job = self._job(db, job_id)
            if job["state"] != "OPEN" or self.clock() >= job["policy"]["deadline"]:
                raise Problem(409, "Bounty is not open for new submissions")
            policy = job["policy"]
            if (
                payload["policy_sha256"] != job["policy_sha256"]
                or payload["parent_sha256"] != policy["parent_sha256"]
                or payload["training_data_sha256"] != policy["train_sha256"]
                or payload["artifact_sha256"] != digest(adapter)
            ):
                raise Problem(422, "Submission commitments do not match the bounty and uploaded artifact")
            validate_adapter(adapter, policy["parent_sha256"])
            # Also validate the merged weights before admission, not merely the adapter shape.
            merge_adapter(self.artifact(policy["parent_sha256"]), adapter)
            rows = self.store.submissions(db, job_id)
            if any(r["worker"] == worker or r["artifact_sha256"] == payload["artifact_sha256"] for r in rows):
                raise Problem(
                    409, "One submission per wallet and one copy of each artifact are allowed per bounty"
                )
            if len(rows) >= policy["max_candidates"]:
                raise Problem(409, "This bounty has reached its predeclared eight-candidate limit")
            sub = {
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "worker": worker,
                "artifact_sha256": self.put_artifact(adapter),
                "manifest_sha256": self.put_artifact(envelope),
                "submitted_at": self.clock(),
                "state": "AWAITING_REGISTRATION" if self.chain else "REGISTERED",
                "registration_signature": None,
                "receipt_sha256": None,
                "worker_metrics": payload["worker_metrics"],
                "metrics_source": "worker-claimed public validation; not held-out evaluation",
            }
            db.execute(
                "INSERT INTO submissions VALUES(?,?,?,?)",
                (sub["id"], job_id, worker, canonical(sub).decode()),
            )
            self.store.event(
                db,
                job_id,
                self.clock(),
                "SUBMITTED",
                f"Artifact {sub['artifact_sha256'][:12]} received; held-out evaluation unavailable until cutoff",
            )
        return sub

    def evaluate(self, job_id):
        with self.lock, self.store.transaction() as db:
            job = self._job(db, job_id)
            if job["state"] in {"EVALUATED", "SETTLING", "SETTLED", "NO_WINNER", "REFUNDED"}:
                return job
            if job["state"] != "OPEN" or self.clock() < job["policy"]["deadline"]:
                raise Problem(409, "Held-out evaluation is only available after a funded bounty closes")
            rows = self.store.submissions(db, job_id)
            if (
                self.chain
                and any(s["state"] == "AWAITING_REGISTRATION" for s in rows)
                and self.clock()
                < job["policy"]["deadline"] + job["policy"]["registration_evidence_grace_seconds"]
            ):
                raise Problem(409, "Registration confirmation grace period is still open")
            parent = self.artifact(job["policy"]["parent_sha256"])
            x, y = self.task["test"]["x"], self.task["test"]["y"]
            baseline = predict(parent, x)
            candidates = []
            for sub in rows:
                if sub["state"] != "REGISTERED":
                    continue
                artifact = self.artifact(sub["artifact_sha256"])
                envelope = self.artifact(sub["manifest_sha256"])
                if not verify_signed(envelope) or envelope["signer"] != sub["worker"]:
                    raise Problem(503, "Submission evidence integrity failed; settlement blocked")
                model = merge_adapter(parent, artifact)
                prediction = predict(model, x)
                score = assess(y, baseline, prediction, job["policy"]["minimum_delta"], 8)
                receipt = self.validator.sign(
                    {
                        "format": "gradientmine.evaluation.v1",
                        "job_id": job_id,
                        "worker": sub["worker"],
                        "policy_sha256": job["policy_sha256"],
                        "parent_sha256": job["policy"]["parent_sha256"],
                        "artifact_sha256": sub["artifact_sha256"],
                        "manifest_sha256": sub["manifest_sha256"],
                        "evaluation_sha256": job["policy"]["evaluation_sha256"],
                        "model_sha256": self.put_artifact(model),
                        "score": score,
                        "evaluated_at": int(self.clock()),
                        "validator": self.validator.address,
                        "trust": "Authenticated statement by one named evaluator, not a cryptographic proof of training or generalization",
                    }
                )
                sub.update(
                    state="ELIGIBLE" if score["eligible"] else "REJECTED",
                    score=score,
                    receipt_sha256=self.put_artifact(receipt),
                    model_sha256=receipt["payload"]["model_sha256"],
                )
                self.store.save_submission(db, sub)
                candidates.append(
                    {
                        **score,
                        "artifact_sha256": sub["artifact_sha256"],
                        "worker": sub["worker"],
                        "submission_id": sub["id"],
                        "receipt_sha256": sub["receipt_sha256"],
                        "model_sha256": sub["model_sha256"],
                    }
                )
            job.update(state="EVALUATED", evaluated_at=int(self.clock()), winner=select_winner(candidates))
            if job["winner"] is None:
                job["state"] = "NO_WINNER"
            job["baseline_accuracy"] = float(np.mean(np.asarray(y) == baseline))
            self.store.save_job(db, job)
            self.store.event(
                db,
                job_id,
                self.clock(),
                "EVALUATED",
                "Eligible winner selected by held-out accuracy and hash tie-break; no payment inferred"
                if job["winner"]
                else "No eligible winner; Devnet escrow is refundable after its timeout",
            )
        return job

    def transaction_intent(self, job_id, address, action, submission_id=None):
        if not self.chain:
            raise Problem(409, "Local mode has no blockchain transactions")
        job = self.detail(job_id)
        sub = next((s for s in job["submissions"] if s["id"] == submission_id), None)
        if action == "fund":
            if address != job["creator"] or job["state"] != "AWAITING_FUNDING":
                raise Problem(403, "Only the creator can fund this unescrowed bounty")
        elif action == "register":
            if (
                not sub
                or sub["worker"] != address
                or sub["state"] != "AWAITING_REGISTRATION"
                or job["state"] != "OPEN"
            ):
                raise Problem(403, "Only the submitting worker can register this pending artifact")
        elif action == "refund":
            if address != job["creator"] or self.clock() < job["policy"]["refund_after"]:
                raise Problem(403, "Only the creator can refund after the immutable timeout")
        else:
            raise Problem(422, "Unsupported wallet transaction")
        return self.chain.intent(action, job, sub)

    def broadcast(self, job_id, address, action, transaction_base64, submission_id=None):
        if not self.chain:
            raise Problem(409, "Local mode has no blockchain transactions")
        # Reuse the authorization and state checks; no server-side signing for wallet actions.
        self.transaction_intent(job_id, address, action, submission_id)
        job = self.detail(job_id)
        sub = next((s for s in job["submissions"] if s["id"] == submission_id), None)
        import base64

        try:
            raw = base64.b64decode(transaction_base64, validate=True)
        except ValueError as exc:
            raise Problem(422, "Invalid signed transaction encoding") from exc
        return self.chain.broadcast_wallet(raw, self.chain.spec(action, job, sub))

    def confirm(self, job_id, address, action, signature, submission_id=None):
        if not self.chain:
            raise Problem(409, "Local mode never records on-chain signatures")
        with self.lock:
            job = self.detail(job_id)
            sub = next((s for s in job["submissions"] if s["id"] == submission_id), None)
            expected = sub["worker"] if action == "register" and sub else job["creator"]
            if address != expected:
                raise Problem(403, "This transaction belongs to a different wallet")
            if action not in {"fund", "register", "refund"} or (action == "register" and not sub):
                raise Problem(422, "Invalid confirmation action or submission")
            # A finalized response can disappear and the bounty can progress before
            # its owner retries. Return the already-verified exact signature without
            # reopening the bounty, resetting eligibility, or needing new RPC access.
            recorded = sub.get("registration_signature") if action == "register" else job.get(
                "funding_signature" if action == "fund" else "refund_signature"
            )
            if recorded is not None and recorded == signature:
                return job
            # Verification is repeatable after an RPC timeout. No mutation happens before finalized evidence.
            self.chain.confirm(action, job, sub, signature)
            with self.store.transaction() as db:
                current = self._job(db, job_id)
                if action == "fund":
                    if current["state"] not in {"AWAITING_FUNDING", "OPEN"}:
                        raise Problem(409, "Bounty has already progressed beyond funding")
                    current.update(state="OPEN", funding_signature=signature)
                elif action == "register":
                    if current["state"] != "OPEN":
                        raise Problem(409, "Bounty evaluation is already closed")
                    sub.update(state="REGISTERED", registration_signature=signature)
                    self.store.save_submission(db, sub)
                elif action == "refund":
                    current.update(state="REFUNDED", refund_signature=signature)
                self.store.save_job(db, current)
                self.store.event(db, job_id, self.clock(), action.upper() + "_FINALIZED", signature)
            return self.detail(job_id)

    def settle(self, job_id):
        if not self.chain:
            raise Problem(409, "Local evaluation does not pay tokens and cannot be called settled")
        with self.lock:
            job = self.detail(job_id)
            if job["state"] == "SETTLED":
                return job
            if job["state"] not in {"EVALUATED", "SETTLING"} or not job["winner"]:
                raise Problem(409, "No eligible winner is ready for settlement")
            winner = job["winner"]
            sub = next(s for s in job["submissions"] if s["id"] == winner["submission_id"])
            receipt = self.artifact(winner["receipt_sha256"])
            if not verify_signed(receipt) or receipt["signer"] != self.validator.address:
                raise Problem(503, "Winning receipt integrity failure")
            if not job.get("pending_settlement"):
                transaction = self.chain.signed_settlement(job, sub, self.validator)
                # Persist the signed intent BEFORE sending. Only an expiring public transaction, never a key.
                with self.store.transaction() as db:
                    saved = self._job(db, job_id)
                    saved.update(state="SETTLING", pending_settlement=transaction)
                    self.store.save_job(db, saved)
                job.update(state="SETTLING", pending_settlement=transaction)
            pending = job["pending_settlement"]
            self.chain.send_signed(pending)
            self.chain.confirm("settle", job, sub, pending["signature"])
            with self.store.transaction() as db:
                saved = self._job(db, job_id)
                saved.update(state="SETTLED", settlement_signature=pending["signature"])
                saved.pop("pending_settlement", None)
                self.store.save_job(db, saved)
                self.store.event(db, job_id, self.clock(), "PAYOUT_FINALIZED", pending["signature"])
            return self.detail(job_id)

    def recover_settlement(self, job_id):
        """Only re-sign after an expired attempt is absent/failed and the bounty is still open."""
        if not self.chain:
            raise Problem(409, "Local mode has no settlement to recover")
        from .recovery import recovery_decision

        with self.lock:
            job = self.detail(job_id)
            pending = job.get("pending_settlement")
            if job["state"] == "SETTLED":
                return job
            if job["state"] != "SETTLING" or not pending:
                raise Problem(409, "No persisted settlement attempt needs recovery")
            self.chain.deployment()
            bounty, _ = self.chain.read_bounty(job)
            status = self.chain.rpc.call(
                "getSignatureStatuses", [[pending["signature"]], {"searchTransactionHistory": True}]
            )["value"][0]
            height = self.chain.rpc.call("getBlockHeight", [{"commitment": "finalized"}])
            decision = recovery_decision(status, height, pending["last_valid_block_height"], bounty["state"])
            if decision == "confirm":
                return self.settle(job_id)
            if decision == "refunded":
                raise Problem(
                    409,
                    "On-chain reward was refunded; no payout will be reissued. Confirm the creator's refund transaction.",
                )
            if decision == "wait":
                raise Problem(
                    409,
                    "The original transaction may still land. Retain its signature and retry confirmation later.",
                )
            with self.store.transaction() as db:
                saved = self._job(db, job_id)
                saved.setdefault("settlement_attempts", []).append(pending)
                saved.pop("pending_settlement", None)
                saved.pop("settlement_warning", None)
                saved["state"] = "EVALUATED"
                self.store.save_job(db, saved)
                self.store.event(
                    db,
                    job_id,
                    self.clock(),
                    "SETTLEMENT_RETRY",
                    "Expired unconfirmed attempt retained in history; on-chain bounty still open",
                )
            return self.settle(job_id)

    def tick(self):
        """Best-effort single-process scheduler. Errors remain visible; retry never invents success."""
        for job in self.jobs():
            if job["state"] == "OPEN" and self.clock() >= job["policy"]["deadline"]:
                try:
                    self.evaluate(job["id"])
                except (Problem, ValueError):
                    continue
            if self.chain:
                current = self.detail(job["id"])
                if current["state"] in {"EVALUATED", "SETTLING"} and current.get("winner"):
                    try:
                        self.settle(job["id"])
                    except (Problem, ValueError) as exc:
                        with self.store.transaction() as db:
                            saved = self._job(db, job["id"])
                            saved["settlement_warning"] = str(exc)
                            self.store.save_job(db, saved)

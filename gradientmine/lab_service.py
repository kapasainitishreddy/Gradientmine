"""Private research competitions, workspace authorization and signed evaluator evidence.

Intentionally separate from the audited Digits/Solana escrow protocol: these are
LOCAL, zero-reward research bounties. An evaluation or a reviewer signature
does not represent a Devnet payout, decentralized consensus, or paid service.
"""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
import threading
import time
import uuid
from pathlib import Path

from cryptography.fernet import Fernet

from .crypto import canonical, digest, validate_address, verify_signed
from .lab_evaluation import BASE, KINDS, compare, validate_artifact, validate_dataset
from .store import ClosingConnection, atomic_write


class LabError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__(message)


class LabService:
    def __init__(self, root: Path, validator, clock=time.time, model_dir=""):
        self.root, self.validator, self.clock = Path(root), validator, clock
        self.model_dir = str(model_dir or "")
        self.lock = threading.RLock()
        path = self.root / "lab-fernet.key"
        if not path.exists():
            atomic_write(path, Fernet.generate_key())
        if os.name == "posix" and path.stat().st_mode & 0o077:
            raise RuntimeError("Private benchmark encryption key is not owner-only")
        self.cipher = Fernet(path.read_bytes())
        self.database = self.root / "research.sqlite3"
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS workspaces (
                  id TEXT PRIMARY KEY, name TEXT NOT NULL, owner TEXT NOT NULL,
                  kind TEXT NOT NULL, created INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS members (
                  workspace_id TEXT NOT NULL REFERENCES workspaces(id),
                  address TEXT NOT NULL, role TEXT NOT NULL,
                  PRIMARY KEY(workspace_id,address)
                );
                CREATE TABLE IF NOT EXISTS benchmarks (
                  id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
                  document TEXT NOT NULL, sealed BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS entries (
                  id TEXT PRIMARY KEY, benchmark_id TEXT NOT NULL REFERENCES benchmarks(id),
                  worker TEXT NOT NULL, document TEXT NOT NULL,
                  UNIQUE(benchmark_id, worker)
                );
                CREATE TABLE IF NOT EXISTS reviews (
                  benchmark_id TEXT NOT NULL REFERENCES benchmarks(id),
                  signer TEXT NOT NULL, envelope TEXT NOT NULL,
                  PRIMARY KEY(benchmark_id,signer)
                );
                CREATE INDEX IF NOT EXISTS lab_workspace_idx ON benchmarks(workspace_id);
                CREATE INDEX IF NOT EXISTS lab_entry_idx ON entries(benchmark_id);
                """
            )

    def _connect(self):
        db = sqlite3.connect(self.database, timeout=30, factory=ClosingConnection)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=30000")
        return db

    @staticmethod
    def _document(row):
        if row is None:
            raise LabError(404, "Research resource not found")
        return json.loads(row["document"])

    @staticmethod
    def _workspace(db, identifier):
        row = db.execute("SELECT * FROM workspaces WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise LabError(404, "Workspace not found")
        return dict(row)

    @staticmethod
    def _role(db, identifier, address):
        row = db.execute(
            "SELECT role FROM members WHERE workspace_id=? AND address=?", (identifier, address)
        ).fetchone()
        return row["role"] if row else None

    def _access(self, db, identifier, address, roles=None):
        role = self._role(db, identifier, address)
        if role is None or (roles is not None and role not in roles):
            raise LabError(403, "Workspace membership or role is insufficient")
        return role

    def create_workspace(self, owner, name, kind="team"):
        if not isinstance(name, str) or not 3 <= len(name.strip()) <= 70 or any(ord(x) < 32 for x in name):
            raise LabError(422, "Workspace name must be 3-70 readable characters")
        if kind not in ("team", "enterprise"):
            raise LabError(422, "Unknown workspace category")
        workspace = {
            "id": str(uuid.uuid4()), "name": name.strip(), "owner": validate_address(owner),
            "kind": kind, "created": int(self.clock()),
            "billing": "not_configured", "usage_quota": "local_limits_only",
        }
        with self.lock, self._connect() as db:
            current = db.execute("SELECT count(*) FROM workspaces WHERE owner=?", (owner,)).fetchone()[0]
            if current >= 10:
                raise LabError(429, "Workspace quota reached")
            db.execute(
                "INSERT INTO workspaces VALUES(?,?,?,?,?)",
                (workspace["id"], workspace["name"], owner, kind, workspace["created"]),
            )
            db.execute(
                "INSERT INTO members VALUES(?,?,?)", (workspace["id"], owner, "owner")
            )
            db.commit()
        return workspace

    def list_workspaces(self, address):
        with self._connect() as db:
            rows = db.execute(
                "SELECT w.*,m.role FROM workspaces w JOIN members m ON m.workspace_id=w.id "
                "WHERE m.address=? ORDER BY w.created DESC", (address,)
            ).fetchall()
        return [{**dict(r), "billing": "not_configured", "usage_quota": "local_limits_only"} for r in rows]

    def add_member(self, workspace_id, owner, address, role):
        address = validate_address(address)
        if role not in ("researcher", "reviewer"):
            raise LabError(422, "Invite role must be researcher or reviewer")
        with self.lock, self._connect() as db:
            self._workspace(db, workspace_id)
            self._access(db, workspace_id, owner, {"owner"})
            existing = db.execute(
                "SELECT count(*) FROM members WHERE workspace_id=?", (workspace_id,)
            ).fetchone()[0]
            if existing >= 30:
                raise LabError(429, "Workspace member limit reached")
            db.execute(
                "INSERT INTO members VALUES(?,?,?) ON CONFLICT(workspace_id,address) DO UPDATE SET role=excluded.role "
                "WHERE members.role!='owner'",
                (workspace_id, address, role),
            )
            db.commit()
        return {"workspace_id": workspace_id, "address": address, "role": role}

    def create_benchmark(self, address, values):
        workspace_id = values["workspace_id"]
        title = values["title"].strip()
        kind = values["kind"]
        docs = values["documents"]
        development = values["development"]
        holdout = values["holdout"]
        if kind not in KINDS or not 3 <= len(title) <= 100 or any(ord(x) < 32 for x in title):
            raise LabError(422, "Invalid title or competition type")
        if kind == "llm_prompt" and not self.model_dir:
            raise LabError(422, "Configure GM_LOCAL_LLM_DIR to a trusted cached model before creating an LLM benchmark")
        if not 5 <= values["duration_seconds"] <= 86400:
            raise LabError(422, "Duration must be 5 to 86400 seconds")
        if not 0 <= values["minimum_delta"] <= 1:
            raise LabError(422, "Minimum improvement must be between 0 and 1")
        if values["visibility"] not in ("public", "private"):
            raise LabError(422, "Visibility must be public or private")
        try:
            validate_dataset(kind, docs, development, holdout)
        except ValueError as exc:
            raise LabError(422, str(exc)) from exc
        now = int(self.clock())
        seal_nonce = secrets.token_hex(16)
        policy = {
            "format": "gradientmine.lab-policy.v1",
            "kind": kind, "documents_sha256": digest(docs),
            "development_sha256": digest(development),
            "evaluation_sha256": digest({"salt": seal_nonce, "holdout": holdout}),
            "baseline_adapter_sha256": digest(BASE[kind]),
            "deadline": now + values["duration_seconds"],
            "minimum_delta": values["minimum_delta"],
            "max_candidates": 8, "validator": self.validator.address,
            "settlement": "local-no-money-no-chain",
            "evaluation": "named-trusted-validator-hidden-set",
            "model_runtime": "offline-cached-local" if kind == "llm_prompt" else "bounded-declarative",
        }
        item = {
            "id": str(uuid.uuid4()), "workspace_id": workspace_id, "title": title,
            "kind": kind, "visibility": values["visibility"], "creator": address,
            "created_at": now, "state": "OPEN",
            "documents": docs, "development": development,
            "policy": policy, "policy_sha256": digest(policy),
            "baseline_adapter": BASE[kind], "winner": None,
            "mode": "local", "reward_lamports": 0, "settlement_signature": None,
        }
        sealed = self.cipher.encrypt(canonical({"salt": seal_nonce, "holdout": holdout}))
        with self.lock, self._connect() as db:
            self._workspace(db, workspace_id)
            self._access(db, workspace_id, address, {"owner", "researcher"})
            count = db.execute(
                "SELECT count(*) FROM benchmarks WHERE workspace_id=?", (workspace_id,)
            ).fetchone()[0]
            if count >= 100:
                raise LabError(429, "Workspace benchmark quota reached")
            db.execute(
                "INSERT INTO benchmarks VALUES(?,?,?,?)",
                (item["id"], workspace_id, canonical(item).decode(), sealed),
            )
            db.commit()
        return item

    def _get_benchmark(self, db, benchmark_id, address=None):
        row = db.execute(
            "SELECT document,sealed FROM benchmarks WHERE id=?", (benchmark_id,)
        ).fetchone()
        item = self._document(row)
        if item["visibility"] == "private":
            if address is None:
                raise LabError(404, "Research resource not found")
            self._access(db, item["workspace_id"], address)
        return item, row

    def list_benchmarks(self, address=None):
        with self._connect() as db:
            rows = db.execute("SELECT document FROM benchmarks ORDER BY rowid DESC LIMIT 100").fetchall()
            output = []
            for row in rows:
                item = json.loads(row["document"])
                if item["visibility"] == "public" or (
                    address is not None and self._role(db, item["workspace_id"], address)
                ):
                    output.append(self._public(item))
        return output

    def _entries(self, db, benchmark_id):
        return [json.loads(row["document"]) for row in db.execute(
            "SELECT document FROM entries WHERE benchmark_id=? ORDER BY rowid", (benchmark_id,)
        )]

    @staticmethod
    def _public(item):
        # No secret holdout, key, signed-in owner contact, or model tokens.
        return item

    def detail(self, benchmark_id, address=None):
        with self._connect() as db:
            item, _ = self._get_benchmark(db, benchmark_id, address)
            entries = self._entries(db, benchmark_id)
            reviews = [
                json.loads(row["envelope"]) for row in db.execute(
                    "SELECT envelope FROM reviews WHERE benchmark_id=? ORDER BY signer", (benchmark_id,)
                )
            ]
        if item["state"] == "OPEN":
            entries = [{k: v for k, v in entry.items() if k not in ("score", "receipt")} for entry in entries]
        return {**self._public(item), "entries": entries, "reviews": reviews}

    def development(self, benchmark_id, address=None):
        return self.detail(benchmark_id, address)

    def submit(self, benchmark_id, worker, artifact, manifest):
        if worker == self.validator.address:
            raise LabError(403, "The named validator cannot compete")
        if not verify_signed(manifest) or manifest.get("signer") != worker:
            raise LabError(422, "A worker-signed candidate manifest is required")
        if not isinstance(manifest.get("payload"), dict) or len(canonical(manifest)) > 8192:
            raise LabError(422, "Invalid candidate manifest")
        claim = manifest["payload"]
        if set(claim) != {"format", "benchmark_id", "policy_sha256", "artifact_sha256", "submitted_at"}:
            raise LabError(422, "Unexpected signed manifest fields")
        if (claim["format"] != "gradientmine.lab-submission.v1"
                or claim["benchmark_id"] != benchmark_id or claim["artifact_sha256"] != digest(artifact)):
            raise LabError(422, "Signed manifest does not match the artifact or benchmark")
        with self.lock, self._connect() as db:
            item, _ = self._get_benchmark(db, benchmark_id, worker)
            if item["state"] != "OPEN" or self.clock() >= item["policy"]["deadline"]:
                raise LabError(409, "Competition is closed")
            if claim["policy_sha256"] != item["policy_sha256"]:
                raise LabError(422, "Signed policy does not match frozen competition policy")
            if type(claim["submitted_at"]) is not int or abs(int(self.clock()) - claim["submitted_at"]) > 600:
                raise LabError(422, "Signed submission timestamp must be recent")
            try:
                validate_artifact(item["kind"], artifact)
            except ValueError as exc:
                raise LabError(422, str(exc)) from exc
            prior = self._entries(db, benchmark_id)
            if any(entry["worker"] == worker or entry["artifact_sha256"] == claim["artifact_sha256"] for entry in prior):
                raise LabError(409, "Only one candidate per wallet and unique artifact per competition")
            if len(prior) >= item["policy"]["max_candidates"]:
                raise LabError(409, "Candidate budget exhausted")
            sub = {
                "id": str(uuid.uuid4()), "benchmark_id": benchmark_id, "worker": worker,
                "artifact": artifact, "artifact_sha256": digest(artifact),
                "manifest": manifest, "submitted_at": int(self.clock()), "state": "SEALED",
            }
            db.execute(
                "INSERT INTO entries VALUES(?,?,?,?)",
                (sub["id"], benchmark_id, worker, canonical(sub).decode()),
            )
            db.commit()
        return {k: v for k, v in sub.items() if k not in ("score", "receipt")}

    def evaluate(self, benchmark_id, actor):
        with self.lock, self._connect() as db:
            item, row = self._get_benchmark(db, benchmark_id, actor)
            self._access(db, item["workspace_id"], actor, {"owner", "researcher", "reviewer"})
            if item["state"] != "OPEN":
                return self.detail(benchmark_id, actor)
            if self.clock() < item["policy"]["deadline"]:
                raise LabError(409, "Private evaluation is only available after cutoff")
            # The sealed bytes never leave the private server-side volume.
            private = json.loads(self.cipher.decrypt(row["sealed"]))
            holdout = private["holdout"]
            if digest(private) != item["policy"]["evaluation_sha256"]:
                raise LabError(503, "Private evaluation commitment does not match stored examples")
            original = self._entries(db, benchmark_id)
            results = []
            for entry in original:
                if not verify_signed(entry["manifest"]) or digest(entry["artifact"]) != entry["artifact_sha256"]:
                    raise LabError(503, "Submitted candidate commitment was corrupted")
                try:
                    score = compare(
                        item["kind"], item["documents"], holdout,
                        entry["artifact"], item["policy"]["minimum_delta"],
                        item["policy"]["max_candidates"], self.model_dir,
                    )
                except (ValueError, RuntimeError) as exc:
                    raise LabError(503, "Benchmark evaluator failed: " + str(exc)) from exc
                payload = {
                    "format": "gradientmine.lab-receipt.v1",
                    "benchmark_id": benchmark_id, "worker": entry["worker"],
                    "artifact_sha256": entry["artifact_sha256"],
                    "policy_sha256": item["policy_sha256"],
                    "evaluation_sha256": item["policy"]["evaluation_sha256"],
                    "score": score, "evaluated_at": int(self.clock()),
                    "validator": self.validator.address,
                    "trust": "Single trusted evaluator, no independent consensus or on-chain payment",
                }
                receipt = self.validator.sign(payload)
                results.append({**entry, "state": "ELIGIBLE" if score["eligible"] else "REJECTED",
                                "score": score, "receipt": receipt, "receipt_sha256": digest(receipt)})
            eligible = [r for r in results if r["score"]["eligible"]]
            key = (
                (lambda r: (-r["score"]["delta"], -r["score"]["candidate_accuracy"], r["artifact_sha256"]))
                if item["kind"] == "efficiency" else
                (lambda r: (-r["score"]["candidate_accuracy"], r["artifact_sha256"]))
            )
            winner = sorted(eligible, key=key)[0] if eligible else None
            item.update(
                state="EVALUATED" if winner else "NO_WINNER",
                winner=(
                    {"worker": winner["worker"], "submission_id": winner["id"],
                     "artifact_sha256": winner["artifact_sha256"],
                     "receipt_sha256": winner["receipt_sha256"], "score": winner["score"]}
                    if winner else None
                ),
                evaluated_at=int(self.clock()), settlement_signature=None,
            )
            # A second immutable digest supports independent, signed reviewer statements.
            item["result_sha256"] = digest({
                "policy_sha256": item["policy_sha256"],
                "winner": item["winner"], "evaluated_at": item["evaluated_at"],
                "entries": [{k: e[k] for k in ("id", "artifact_sha256", "score")} for e in results],
            })
            for entry in results:
                db.execute("UPDATE entries SET document=? WHERE id=?",
                           (canonical(entry).decode(), entry["id"]))
            db.execute("UPDATE benchmarks SET document=? WHERE id=?",
                       (canonical(item).decode(), benchmark_id))
            db.commit()
        return self.detail(benchmark_id, actor)

    def attest(self, benchmark_id, actor, envelope):
        if not verify_signed(envelope) or envelope.get("signer") != actor:
            raise LabError(422, "Reviewer must sign the exact attestation payload")
        claim = envelope.get("payload")
        with self.lock, self._connect() as db:
            item, _ = self._get_benchmark(db, benchmark_id, actor)
            self._access(db, item["workspace_id"], actor, {"owner", "reviewer"})
            if item["state"] not in ("EVALUATED", "NO_WINNER"):
                raise LabError(409, "No finalized evaluation exists to attest")
            expected = {
                "format": "gradientmine.review.v1", "benchmark_id": benchmark_id,
                "policy_sha256": item["policy_sha256"], "results_sha256": item["result_sha256"],
            }
            if claim != expected:
                raise LabError(422, "Reviewer attestation does not match the frozen evaluated result")
            db.execute(
                "INSERT OR REPLACE INTO reviews VALUES(?,?,?)",
                (benchmark_id, actor, canonical(envelope).decode()),
            )
            db.commit()
        return {"signed": True, "reviewer": actor, "scope": "result-hash attestation only, not independently rerun evaluation"}

    @staticmethod
    def fee_quote(reward_lamports):
        if type(reward_lamports) is not int or not 0 <= reward_lamports <= 10_000_000_000:
            raise LabError(422, "Invalid hypothetical reward amount")
        fee = reward_lamports * 1000 // 10000
        return {
            "fee_bps": 1000, "reward_lamports": reward_lamports,
            "projected_protocol_fee_lamports": fee,
            "projected_worker_net_lamports": reward_lamports - fee,
            "collectible": False, "status": "simulation-only",
            "notice": "No live fee collection, Stripe billing, mainnet rewards or Devnet settlement is enabled in research competitions",
        }

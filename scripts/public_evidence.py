"""Export only bounty-referenced, integrity-checked public product evidence."""

from __future__ import annotations

from pathlib import Path

from gradientmine.crypto import canonical, digest, safe_json, verify_signed
from gradientmine.ml import merge_adapter, validate_adapter
from gradientmine.scoring import select_winner
from gradientmine.store import atomic_write

JOB_FIELDS = {
    "id", "creator", "title", "created_at", "mode", "policy", "policy_sha256", "state", "lineage",
    "winner", "funding_signature", "settlement_signature", "refund_signature", "bounty_address",
    "evaluated_at", "baseline_accuracy", "submissions", "events",
}
SUB_FIELDS = {
    "id", "job_id", "worker", "artifact_sha256", "manifest_sha256", "submitted_at", "state",
    "registration_signature", "receipt_sha256", "worker_metrics", "metrics_source", "score", "model_sha256",
}


def checked_artifacts(job, fetch):
    """Verify signer identity and cross-artifact provenance, not just self-consistent hashes."""
    if digest(job["policy"]) != job["policy_sha256"]:
        raise ValueError("Bounty policy hash mismatch")
    hashes = {job["policy_sha256"], job["policy"]["parent_sha256"]}
    for sub in job["submissions"]:
        hashes.update(sub[key] for key in (
            "artifact_sha256", "manifest_sha256", "receipt_sha256", "model_sha256"
        ) if sub.get(key))
    raw, values = {}, {}
    for sha in sorted(hashes):
        content = fetch(sha)
        if digest(content) != sha:
            raise ValueError("Public artifact integrity mismatch")
        raw[sha], values[sha] = content, safe_json(content, limit=262144)
    if values[job["policy_sha256"]] != job["policy"]:
        raise ValueError("Downloaded policy differs from bounty")
    policy = job["policy"]
    parent = values[policy["parent_sha256"]]
    for sub in job["submissions"]:
        artifact = values[sub["artifact_sha256"]]
        validate_adapter(artifact, policy["parent_sha256"])
        manifest = values[sub["manifest_sha256"]]
        if not verify_signed(manifest) or manifest["signer"] != sub["worker"]:
            raise ValueError("Worker manifest signature or expected signer mismatch")
        expected = {
            "format": "gradientmine.submission.v1", "job_id": job["id"],
            "policy_sha256": job["policy_sha256"], "parent_sha256": policy["parent_sha256"],
            "artifact_sha256": sub["artifact_sha256"], "training_data_sha256": policy["train_sha256"],
        }
        if sub["job_id"] != job["id"] or any(manifest["payload"].get(k) != v for k, v in expected.items()):
            raise ValueError("Worker manifest bounty provenance mismatch")
        if sub.get("receipt_sha256"):
            receipt = values[sub["receipt_sha256"]]
            if not verify_signed(receipt) or receipt["signer"] != policy["validator"]:
                raise ValueError("Evaluation receipt expected validator mismatch")
            expected = {
                "format": "gradientmine.evaluation.v1", "job_id": job["id"], "worker": sub["worker"],
                "validator": policy["validator"], "policy_sha256": job["policy_sha256"],
                "parent_sha256": policy["parent_sha256"], "artifact_sha256": sub["artifact_sha256"],
                "manifest_sha256": sub["manifest_sha256"], "evaluation_sha256": policy["evaluation_sha256"],
                "model_sha256": sub["model_sha256"], "score": sub["score"],
            }
            if any(receipt["payload"].get(k) != v for k, v in expected.items()):
                raise ValueError("Evaluation receipt bounty provenance mismatch")
            if receipt["payload"]["evaluated_at"] < policy["deadline"]:
                raise ValueError("Evaluation receipt predates held-out evaluation boundary")
            if digest(merge_adapter(parent, artifact)) != sub["model_sha256"]:
                raise ValueError("Winning model is not the committed parent plus adapter")
    candidates = [{**sub["score"], "artifact_sha256": sub["artifact_sha256"],
                   "worker": sub["worker"], "submission_id": sub["id"],
                   "receipt_sha256": sub["receipt_sha256"], "model_sha256": sub["model_sha256"]}
                  for sub in job["submissions"] if sub.get("receipt_sha256")]
    winner = job.get("winner")
    if winner != select_winner(candidates):
        raise ValueError("Winner differs from deterministic receipt-based selection")
    if winner:
        matched = [s for s in job["submissions"] if s["id"] == winner["submission_id"]]
        if len(matched) != 1 or not matched[0].get("score", {}).get("eligible"):
            raise ValueError("Winner is not an evaluated eligible submission")
        sub = matched[0]
        if any(winner.get(k) != sub.get(k) for k in (
            "worker", "artifact_sha256", "receipt_sha256", "model_sha256"
        )):
            raise ValueError("Winner commitments differ from signed evaluated submission")
    return raw


def export_public(out, proof, job, fetch):
    """Never copy a server volume, worker checkpoint, identity, or unreferenced artifact."""
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError("Public evidence output must be empty; preserve previous proof")
    artifacts = checked_artifacts(job, fetch)
    if job["state"] != "SETTLED" or not job.get("winner"):
        raise ValueError("A finalized paid bounty is required for public product proof")
    expected = {
        "program_id": job["policy"]["program_id"], "bounty_address": job["bounty_address"],
        "creator": job["creator"], "worker": job["winner"]["worker"], "validator": job["policy"]["validator"],
        "policy_sha256": job["policy_sha256"], "reward_lamports": job["policy"]["reward_lamports"],
        "deadline": job["policy"]["deadline"],
        **{k: job["winner"][k] for k in ("artifact_sha256", "receipt_sha256", "model_sha256")},
    }
    if any(proof.get(k) != v for k, v in expected.items()):
        raise ValueError("Public proof commitments differ from the checked bounty")
    winning = next(s for s in job["submissions"] if s["id"] == job["winner"]["submission_id"])
    if proof["manifest_sha256"] != winning["manifest_sha256"]:
        raise ValueError("Public proof manifest differs from the signed winning artifact")
    if (proof["funding"]["signature"] != job["funding_signature"]
        or proof["registration"]["signature"] != winning["registration_signature"]
        or proof["settlement"]["signature"] != job["settlement_signature"]
        or proof["settlement"]["state"] != 1):
        raise ValueError("Public transaction proof differs from verified job signatures")
    if proof["deployment_before"] != proof["deployment_after"]:
        raise ValueError("Public deployment verification changed during the run")
    public_job = {k: v for k, v in job.items() if k in JOB_FIELDS}
    public_job["submissions"] = [
        {k: v for k, v in sub.items() if k in SUB_FIELDS} for sub in job["submissions"]
    ]
    # Wholly caller-controlled arbitrary fields are not copied into the public proof.
    allowed = {
        "format", "executed_at", "mode", "network", "source_commit", "program_sha256", "build",
        "genesis", "program_id", "bounty_address", "creator", "worker", "validator", "policy_sha256",
        "policy_commitments", "artifact_sha256", "manifest_sha256", "receipt_sha256", "model_sha256",
        "reward_lamports", "deadline", "funding", "registration", "settlement", "balances_before",
        "balances_after", "final_bounty", "deployment_before", "deployment_after", "worker_execution",
        "disclosure", "private_keys_exported",
    }
    if set(proof) - allowed:
        raise ValueError("Unexpected fields in public proof")
    record = {**proof, "job": public_job, "artifacts": sorted(artifacts)}
    # Validate everything before producing any output. Existing private files are never inspected.
    for sha, content in artifacts.items():
        atomic_write(out / "artifacts" / f"{sha}.json", content)
    atomic_write(out / "devnet-smoke.json", canonical(record))
    atomic_write(out / "run.json", canonical(record))
    return record

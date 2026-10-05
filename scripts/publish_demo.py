"""Export only integrity-checked, referenced PUBLIC artifacts. Never copy a data directory."""

from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from gradientmine.crypto import canonical, digest, safe_json, verify_signed


def publish(run_path: Path, destination: Path) -> dict:
    run = safe_json(run_path.read_bytes(), limit=2_000_000)
    job = run.get("job", {})
    if (
        run.get("format") != "gradientmine.recorded-run.v1"
        or run.get("mode") != "local"
        or job.get("mode") != "local"
    ):
        raise ValueError("This exporter supports explicitly local recorded runs only")
    if any(
        job.get(k)
        for k in ("funding_signature", "settlement_signature", "refund_signature", "pending_settlement")
    ):
        raise ValueError("A local recorded run must not claim a blockchain transaction")
    allowed = {job["policy_sha256"], job["policy"]["parent_sha256"]}
    expected_signers = {}
    for sub in job["submissions"]:
        allowed.update(
            sub[k]
            for k in ("artifact_sha256", "manifest_sha256", "receipt_sha256", "model_sha256")
            if sub.get(k)
        )
        expected_signers[sub["manifest_sha256"]] = sub["worker"]
        if sub.get("receipt_sha256"):
            expected_signers[sub["receipt_sha256"]] = job["policy"]["validator"]
    if set(run["artifacts"]) != allowed or any(not re.fullmatch("[a-f0-9]{64}", s) for s in allowed):
        raise ValueError("Artifact list differs from the public, referenced evidence allowlist")
    verified = {}
    for sha in sorted(allowed):
        raw = (run_path.parent / "artifacts" / f"{sha}.json").read_bytes()
        if digest(raw) != sha:
            raise ValueError(f"Artifact SHA-256 mismatch: {sha}")
        value = safe_json(raw)
        if sha in expected_signers and (
            not verify_signed(value) or value.get("signer") != expected_signers[sha]
        ):
            raise ValueError(f"Unexpected signature or signer: {sha}")
        verified[sha] = raw
    target = destination / "assets" / "artifacts"
    target.mkdir(parents=True, exist_ok=True)
    for sha, raw in verified.items():
        (target / f"{sha}.json").write_bytes(raw)
    (destination / "assets" / "recorded-run.json").write_bytes(canonical(run))
    manifest = {
        "format": "gradientmine.public-export.v1",
        "mode": "local",
        "artifacts": len(verified),
        "run_sha256": digest(canonical(run)),
        "files": {f"{sha}.json": sha for sha in verified},
        "private_data_exported": False,
    }
    (destination / "assets" / "export-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True, type=Path)
    p.add_argument("--web", default=Path("web"), type=Path)
    a = p.parse_args()
    print(json.dumps(publish(a.run, a.web), indent=2))

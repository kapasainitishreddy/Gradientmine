import json
import pytest
from scripts.publish_demo import publish
from gradientmine.crypto import canonical, digest


def test_publisher_rejects_network_claim_and_private_artifact(tmp_path):
    run = {
        "format": "gradientmine.recorded-run.v1",
        "mode": "devnet",
        "job": {"mode": "devnet"},
        "artifacts": [],
    }
    path = tmp_path / "run.json"
    path.write_text(json.dumps(run))
    with pytest.raises(ValueError):
        publish(path, tmp_path / "web")
    run.update(
        mode="local",
        job={
            "mode": "local",
            "policy_sha256": "a" * 64,
            "policy": {"parent_sha256": "b" * 64},
            "submissions": [],
        },
    )
    run["artifacts"] = ["private-task"]
    path.write_text(json.dumps(run))
    with pytest.raises(ValueError):
        publish(path, tmp_path / "web")


def test_publisher_only_exports_referenced_integrity_checked_public_evidence(tmp_path):
    artifact = {"weights": [1, 2, 3]}
    raw = canonical(artifact)
    sha = digest(raw)
    run = {
        "format": "gradientmine.recorded-run.v1",
        "mode": "local",
        "job": {"mode": "local", "policy_sha256": sha, "policy": {"parent_sha256": sha}, "submissions": []},
        "artifacts": [sha],
    }
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / f"{sha}.json").write_bytes(raw)
    (tmp_path / "private-task.json").write_text("private")
    path = tmp_path / "run.json"
    path.write_bytes(canonical(run))
    out = tmp_path / "web"
    publish(path, out)
    assert (out / "assets/artifacts" / f"{sha}.json").read_bytes() == raw
    assert not list(out.rglob("*private*"))
    (tmp_path / "artifacts" / f"{sha}.json").write_bytes(b"wrong")
    with pytest.raises(ValueError):
        publish(path, out)

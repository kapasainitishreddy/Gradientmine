import copy
from fastapi.testclient import TestClient
from gradientmine.api import create_app
from gradientmine.cli import make_submission
from gradientmine.crypto import digest, verify_signed
from conftest import login


def new_job(client, auth, **extra):
    r = client.post(
        "/api/jobs", headers=auth, json={"title": "Real training bounty", "duration_seconds": 10, **extra}
    )
    assert r.status_code == 200, r.text
    return r.json()


def submit(client, person, job, **kwargs):
    auth = login(client, person)
    package = client.get(f"/api/jobs/{job['id']}/training", headers=auth).json()
    artifact, manifest, _ = make_submission(person, job, package, **kwargs)
    result = client.post(
        f"/api/jobs/{job['id']}/submissions", headers=auth, json={"artifact": artifact, "manifest": manifest}
    )
    return result, auth, artifact, manifest


def test_complete_real_training_receipts_lineage_and_restart(client, app, identities, clock):
    auth = login(client, identities[0])
    job = new_job(client, auth)
    assert "test" not in client.get(f"/api/jobs/{job['id']}/training", headers=auth).json()
    good, _, _, _ = submit(client, identities[1], job)
    bad, _, _, _ = submit(client, identities[2], job, negative_control=True)
    assert good.status_code == bad.status_code == 200
    assert client.post(f"/api/jobs/{job['id']}/evaluate", headers=auth).status_code == 409
    detail = client.get(f"/api/jobs/{job['id']}").json()
    assert all("score" not in s for s in detail["submissions"])
    clock.advance(11)
    evaluated = client.post(f"/api/jobs/{job['id']}/evaluate", headers=auth).json()
    assert evaluated["state"] == "EVALUATED"
    assert evaluated["winner"]["worker"] == identities[1].address
    repeat = client.post(f"/api/jobs/{job['id']}/evaluate", headers=auth).json()
    assert repeat == evaluated
    assert client.post(f"/api/jobs/{job['id']}/settle", headers=auth).status_code == 409
    for sub in client.get(f"/api/jobs/{job['id']}").json()["submissions"]:
        response = client.get(f"/api/artifacts/{sub['receipt_sha256']}")
        assert digest(response.content) == sub["receipt_sha256"]
        assert verify_signed(response.json())
    child = new_job(client, auth, parent_job_id=job["id"])
    assert child["policy"]["parent_sha256"] == evaluated["winner"]["model_sha256"]
    assert child["lineage"][0]["job_id"] == job["id"]
    restarted = create_app(app.state.market.settings, clock=clock)
    with TestClient(restarted) as again:
        assert again.get(f"/api/jobs/{job['id']}").json()["winner"] == evaluated["winner"]
        assert again.get("/api/config").json()["validator"] == app.state.market.validator.address


def test_wrong_parent_signed_manifest_and_duplicate_artifact(client, identities):
    creator = login(client, identities[0])
    job = new_job(client, creator)
    result, auth, artifact, manifest = submit(client, identities[1], job)
    assert result.status_code == 200
    again = client.post(
        f"/api/jobs/{job['id']}/submissions", headers=auth, json={"artifact": artifact, "manifest": manifest}
    )
    assert again.status_code == 409
    other = login(client, identities[2])
    copied = identities[2].sign(manifest["payload"])
    assert (
        client.post(
            f"/api/jobs/{job['id']}/submissions",
            headers=other,
            json={"artifact": artifact, "manifest": copied},
        ).status_code
        == 409
    )
    tampered = copy.deepcopy(manifest)
    tampered["payload"]["artifact_sha256"] = "0" * 64
    assert (
        client.post(
            f"/api/jobs/{job['id']}/submissions",
            headers=other,
            json={"artifact": artifact, "manifest": tampered},
        ).status_code
        == 422
    )


def test_submission_cutoff_and_empty_round(client, identities, clock):
    auth = login(client, identities[0])
    job = new_job(client, auth)
    clock.advance(11)
    result, _, _, _ = submit(client, identities[1], job)
    assert result.status_code == 409
    result = client.post(f"/api/jobs/{job['id']}/evaluate", headers=auth).json()
    assert result["state"] == "NO_WINNER" and result["winner"] is None


def test_artifact_corruption_blocks_evaluation(client, app, identities, clock):
    auth = login(client, identities[0])
    job = new_job(client, auth)
    result, _, _, _ = submit(client, identities[1], job)
    sub = result.json()
    (app.state.market.artifacts / f"{sub['artifact_sha256']}.json").write_bytes(b"{}")
    clock.advance(11)
    response = client.post(f"/api/jobs/{job['id']}/evaluate", headers=auth)
    assert response.status_code == 503
    assert client.get(f"/api/jobs/{job['id']}").json()["state"] == "OPEN"


def test_no_chain_operations_in_local_mode(client, identities):
    auth = login(client, identities[0])
    job = new_job(client, auth)
    r = client.post(f"/api/jobs/{job['id']}/transaction", headers=auth, json={"action": "fund"})
    assert r.status_code == 409
    assert job["funding_signature"] is None and job["settlement_signature"] is None

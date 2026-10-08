"""Security regression tests for private Research Lab competition boundaries."""

import json
import sqlite3

from conftest import login
from gradientmine.crypto import digest


DOCS = [
    {"id": "a", "title": "Application hosting", "text": "Applications are deployed on servers."},
    {"id": "b", "title": "Animal hospital", "text": "Veterinarians provide care to pets."},
]
PUBLIC = [
    {"query": "applications", "relevant_ids": ["a"]},
    {"query": "pets", "relevant_ids": ["b"]},
]
SEALED = [
    {"query": f"applications privateitem{i}", "relevant_ids": ["a"]} for i in range(32)
]


def setup_lab(client, identities, kind="retrieval", visibility="private"):
    owner = login(client, identities[0])
    workspace = client.post(
        "/api/lab/workspaces", headers=owner, json={"name": "Verified Research", "kind": "team"}
    )
    assert workspace.status_code == 200, workspace.text
    workspace_id = workspace.json()["id"]
    member = login(client, identities[1])
    result = client.post(
        f"/api/lab/workspaces/{workspace_id}/members", headers=owner,
        json={"address": identities[1].address, "role": "researcher"},
    )
    assert result.status_code == 200, result.text
    body = {
        "workspace_id": workspace_id, "title": "A controlled retrieval challenge",
        "kind": kind, "visibility": visibility, "duration_seconds": 8,
        "minimum_delta": 0.1, "documents": DOCS, "development": PUBLIC, "holdout": SEALED,
    }
    created = client.post("/api/lab/benchmarks", headers=owner, json=body)
    assert created.status_code == 200, created.text
    return owner, member, workspace_id, created.json()


def signed_entry(identities, clock, competition):
    from gradientmine.lab_evaluation import BASE

    adapter = dict(BASE["retrieval"], expansion={"application": "applications"})
    envelope = identities[1].sign({
        "format": "gradientmine.lab-submission.v1",
        "benchmark_id": competition["id"],
        "policy_sha256": competition["policy_sha256"],
        "artifact_sha256": digest(adapter),
        "submitted_at": int(clock()),
    })
    return adapter, envelope


def test_competing_artifacts_and_manifests_are_sealed_until_evaluation(
    client, identities, clock
):
    owner, member, wsid, competition = setup_lab(client, identities, visibility="public")
    artifact, manifest = signed_entry(identities, clock, competition)
    response = client.post(
        f"/api/lab/benchmarks/{competition['id']}/submissions",
        headers=member, json={"artifact": artifact, "manifest": manifest},
    )
    assert response.status_code == 200, response.text
    for content in [
        response.json(),
        client.get(f"/api/lab/benchmarks/{competition['id']}", headers=owner).json()["entries"][0],
        client.get(f"/api/lab/benchmarks/{competition['id']}").json()["entries"][0],
        client.get(f"/api/lab/benchmarks/{competition['id']}", headers=member).json()["entries"][0],
    ]:
        assert content["state"] == "SEALED"
        assert "artifact_sha256" in content
        assert not ({"artifact", "manifest", "score", "receipt"} & content.keys())
    clock.advance(9)
    scored = client.post(
        f"/api/lab/benchmarks/{competition['id']}/evaluate", headers=owner
    )
    assert scored.status_code == 200, scored.text
    entry = client.get(f"/api/lab/benchmarks/{competition['id']}").json()["entries"][0]
    assert entry["artifact"] == artifact
    assert entry["manifest"] == manifest
    assert "score" in entry and "receipt" in entry


def test_role_changes_member_listing_and_revocation_take_effect_immediately(
    client, identities
):
    owner, member, wsid, competition = setup_lab(client, identities)
    path = f"/api/lab/workspaces/{wsid}"
    listed = client.get(path + "/members", headers=owner)
    assert listed.status_code == 200
    assert {v["role"] for v in listed.json()["members"]} == {"owner", "researcher"}
    assert client.get(path + "/members", headers=member).status_code == 403
    assert client.post(
        path + f"/members/{identities[0].address}/revoke", headers=owner
    ).status_code == 409
    assert client.post(
        path + "/members", headers=owner,
        json={"address": identities[0].address, "role": "reviewer"},
    ).status_code == 409

    role = client.post(
        path + "/members", headers=owner,
        json={"address": identities[1].address, "role": "reviewer"},
    )
    assert role.status_code == 200 and role.json()["role"] == "reviewer"
    assert client.post(
        "/api/lab/benchmarks", headers=member,
        json={
            "workspace_id": wsid, "title": "Not permitted to create",
            "kind": "retrieval", "duration_seconds": 8,
            "minimum_delta": 0, "visibility": "private", "documents": DOCS,
            "development": PUBLIC, "holdout": SEALED,
        },
    ).status_code == 403
    removed = client.post(
        path + f"/members/{identities[1].address}/revoke", headers=owner
    )
    assert removed.status_code == 200 and removed.json()["revoked"] is True
    assert client.get(f"/api/lab/benchmarks/{competition['id']}", headers=member).status_code == 403
    assert client.get(path + "/audit", headers=member).status_code == 403
    assert not client.get("/api/lab/benchmarks", headers=member).json()["benchmarks"]
    assert client.post(
        path + f"/members/{identities[1].address}/revoke", headers=owner
    ).status_code == 404

    audit = client.get(path + "/audit", headers=owner)
    assert audit.status_code == 200
    kinds = [row["kind"] for row in audit.json()["events"]]
    for event in (
        "WORKSPACE_CREATED", "MEMBER_ADDED", "BENCHMARK_CREATED",
        "MEMBER_ROLE_CHANGED", "MEMBER_REVOKED",
    ):
        assert event in kinds
    assert "privateitem" not in json.dumps(audit.json())
    assert client.get(path + "/audit").status_code == 401


def test_corrupted_sealed_evaluation_fails_closed_and_does_not_select_a_winner(
    client, identities, clock, app
):
    owner, member, wsid, competition = setup_lab(client, identities)
    artifact, manifest = signed_entry(identities, clock, competition)
    created = client.post(
        f"/api/lab/benchmarks/{competition['id']}/submissions",
        headers=member, json={"artifact": artifact, "manifest": manifest},
    )
    assert created.status_code == 200
    with sqlite3.connect(app.state.market.lab.database) as conn:
        conn.execute(
            "UPDATE benchmarks SET sealed=? WHERE id=?",
            (b"broken-ciphertext", competition["id"]),
        )
    clock.advance(9)
    failed = client.post(
        f"/api/lab/benchmarks/{competition['id']}/evaluate", headers=owner
    )
    assert failed.status_code == 503
    assert failed.json()["error"] == "Private evaluation evidence is unavailable or corrupt"
    detail = client.get(f"/api/lab/benchmarks/{competition['id']}", headers=owner).json()
    assert detail["state"] == "OPEN" and detail["winner"] is None
    assert "artifact" not in detail["entries"][0]


def test_evaluator_rechecks_original_signed_worker_and_policy_commitments(
    client, identities, clock, app
):
    owner, member, wsid, competition = setup_lab(client, identities)
    artifact, manifest = signed_entry(identities, clock, competition)
    response = client.post(
        f"/api/lab/benchmarks/{competition['id']}/submissions",
        headers=member, json={"artifact": artifact, "manifest": manifest},
    )
    assert response.status_code == 200
    with sqlite3.connect(app.state.market.lab.database) as conn:
        raw = conn.execute(
            "SELECT id,document FROM entries WHERE benchmark_id=?", (competition["id"],)
        ).fetchone()
        record = json.loads(raw[1])
        # The replacement is itself validly signed, but by the WRONG worker.
        record["manifest"] = identities[2].sign(record["manifest"]["payload"])
        conn.execute("UPDATE entries SET document=? WHERE id=?", (json.dumps(record), raw[0]))
    clock.advance(9)
    failed = client.post(
        f"/api/lab/benchmarks/{competition['id']}/evaluate", headers=owner
    )
    assert failed.status_code == 503
    assert client.get(f"/api/lab/benchmarks/{competition['id']}", headers=owner).json()["state"] == "OPEN"


def test_llm_tasks_have_separate_candidate_and_holdout_budgets(client, identities, app):
    owner, member, wsid, _ = setup_lab(client, identities)
    app.state.market.lab.model_dir = "/operator/local-llm"
    response = client.post(
        "/api/lab/benchmarks", headers=owner,
        json={
            "workspace_id": wsid, "title": "Large offline evaluation rejected",
            "kind": "llm_prompt", "visibility": "private",
            "duration_seconds": 10, "minimum_delta": 0.05,
            "documents": [], "development": [
                {"question": "Explain", "answer": "Example"} for _ in range(2)
            ], "holdout": [
                {"question": f"What {i}?", "answer": "Example"} for i in range(20)
            ],
        },
    )
    assert response.status_code == 422
    info = client.get("/api/lab/types").json()
    assert info["limits"]["llm_max_candidates"] == 2
    assert info["limits"]["llm_max_holdout"] == 16

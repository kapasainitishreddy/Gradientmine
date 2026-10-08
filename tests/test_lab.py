"""Real API integration for private research lab. Zero payments or networked LLM assumptions."""
import json

import pytest

from conftest import login
from gradientmine.api import create_app
from gradientmine.crypto import digest, verify_signed
from gradientmine.lab_evaluation import BASE, compare, validate_artifact
from gradientmine.lab_worker import search


def docs():
    return [
        {"id": "d1", "title": "Application platform", "text": "Application platform provides hosted software and deployment."},
        {"id": "d2", "title": "Animal care", "text": "Veterinary experts treat animals and pets."},
        {"id": "d3", "title": "Archives", "text": "Older records live in the archives."},
    ]


def research_payload(workspace_id, kind="retrieval", visibility="private"):
    if kind == "retrieval":
        development = [{"query": "app", "relevant_ids": ["d1"]} for _ in range(7)]
        holdout = [
            {"query": f"app onlyhiddenmarker{i}", "relevant_ids": ["d1"]}
            for i in range(60)
        ]
    elif kind == "safety_refusal":
        development = [
            {"prompt": "prohibited request", "should_refuse": True},
            {"prompt": "normal topic", "should_refuse": False},
        ]
        holdout = [
            {"prompt": f"prohibited message{i}", "should_refuse": True}
            for i in range(30)
        ] + [
            {"prompt": f"ordinary message{i}", "should_refuse": False}
            for i in range(30)
        ]
    else:
        development = [{"query": "application", "relevant_ids": ["d1"]} for _ in range(7)]
        holdout = [{"query": f"application item{i}", "relevant_ids": ["d1"]} for i in range(45)]
    return {
        "workspace_id": workspace_id, "title": "Privacy-preserving model research",
        "kind": kind, "visibility": visibility, "duration_seconds": 9,
        "minimum_delta": 0.2, "documents": docs(),
        "development": development, "holdout": holdout,
    }


def signed_candidate(person, benchmark, adapter, now):
    return person.sign({
        "format": "gradientmine.lab-submission.v1",
        "benchmark_id": benchmark["id"],
        "policy_sha256": benchmark["policy_sha256"],
        "artifact_sha256": digest(adapter),
        "submitted_at": int(now),
    })


def bootstrap(client, identities):
    creator = login(client, identities[0])
    response = client.post("/api/lab/workspaces", headers=creator, json={"name": "Research Team", "kind": "enterprise"})
    assert response.status_code == 200, response.text
    ws = response.json()
    return creator, ws


def test_retrieval_competition_private_dataset_lifecycle(client, identities, clock, app):
    owner, ws = bootstrap(client, identities)
    query = client.post("/api/lab/benchmarks", headers=owner, json=research_payload(ws["id"]))
    assert query.status_code == 200, query.text
    benchmark = query.json()
    assert benchmark["policy_sha256"] == digest(benchmark["policy"])
    assert "holdout" not in query.text and "onlyhiddenmarker" not in query.text
    assert client.get("/api/lab/benchmarks").json()["benchmarks"] == []
    assert client.get("/api/lab/benchmarks/" + benchmark["id"]).status_code == 404

    worker = login(client, identities[1])
    assert client.get("/api/lab/benchmarks/" + benchmark["id"], headers=worker).status_code == 403
    assert client.post("/api/lab/benchmarks/" + benchmark["id"] + "/evaluate", headers=owner).status_code == 409

    grant = client.post(f"/api/lab/workspaces/{ws['id']}/members", headers=owner,
                        json={"address": identities[1].address, "role": "researcher"})
    assert grant.status_code == 200, grant.text
    development = client.get("/api/lab/benchmarks/" + benchmark["id"], headers=worker).json()
    assert len(development["development"]) == 7
    assert "holdout" not in json.dumps(development)
    artifact = dict(BASE["retrieval"], expansion={"app": "application"})
    manifest = signed_candidate(identities[1], benchmark, artifact, clock())
    send = client.post(f"/api/lab/benchmarks/{benchmark['id']}/submissions",
                       headers=worker, json={"artifact": artifact, "manifest": manifest})
    assert send.status_code == 200, send.text
    assert "score" not in client.get("/api/lab/benchmarks/" + benchmark["id"], headers=worker).text
    dup = client.post(f"/api/lab/benchmarks/{benchmark['id']}/submissions",
                      headers=worker, json={"artifact": artifact, "manifest": manifest})
    assert dup.status_code == 409

    key_store = app.state.market.root / "research.sqlite3"
    assert b"onlyhiddenmarker" not in key_store.read_bytes()
    assert (app.state.market.root / "lab-fernet.key").exists()

    clock.advance(11)
    scored = client.post(f"/api/lab/benchmarks/{benchmark['id']}/evaluate", headers=owner)
    assert scored.status_code == 200, scored.text
    result = scored.json()
    assert result["state"] == "EVALUATED"
    assert result["winner"]["worker"] == identities[1].address
    assert result["winner"]["score"]["candidate_accuracy"] == 1
    assert result["winner"]["score"]["eligible"] is True
    assert verify_signed(result["entries"][0]["receipt"])
    assert result["entries"][0]["receipt"]["payload"]["evaluation_sha256"] == benchmark["policy"]["evaluation_sha256"]
    assert result["settlement_signature"] is None
    assert result["mode"] == "local"

    # The encrypted evaluation dataset and keys survive process recreation.
    reopened = create_app(app.state.market.settings, clock=clock)
    assert reopened.state.market.lab.detail(benchmark["id"], identities[0].address)["winner"] == result["winner"]


def test_signed_independent_review_is_attestation_not_consensus(client, identities, clock):
    owner, ws = bootstrap(client, identities)
    bench = client.post("/api/lab/benchmarks", headers=owner, json=research_payload(ws["id"])).json()
    clock.advance(11)
    client.post(f"/api/lab/benchmarks/{bench['id']}/evaluate", headers=owner)
    reviewer = login(client, identities[2])
    assert client.get(f"/api/lab/benchmarks/{bench['id']}", headers=reviewer).status_code == 403
    grant = client.post(f"/api/lab/workspaces/{ws['id']}/members", headers=owner,
                        json={"address": identities[2].address, "role": "reviewer"})
    assert grant.status_code == 200, grant.text
    result = client.get(f"/api/lab/benchmarks/{bench['id']}", headers=reviewer).json()
    payload = {
        "format": "gradientmine.review.v1", "benchmark_id": bench["id"],
        "policy_sha256": bench["policy_sha256"], "results_sha256": result["result_sha256"],
    }
    bad = identities[2].sign(dict(payload, results_sha256="0" * 64))
    assert client.post(f"/api/lab/benchmarks/{bench['id']}/reviews",
                       headers=reviewer, json={"envelope": bad}).status_code == 422
    good = identities[2].sign(payload)
    r = client.post(f"/api/lab/benchmarks/{bench['id']}/reviews",
                    headers=reviewer, json={"envelope": good})
    assert r.status_code == 200, r.text
    assert "not independently rerun" in r.json()["scope"]
    final = client.get(f"/api/lab/benchmarks/{bench['id']}", headers=owner).json()
    assert len(final["reviews"]) == 1
    assert verify_signed(final["reviews"][0])


def test_safety_and_efficiency_have_real_bounded_evaluation():
    safety = dict(BASE["safety_refusal"], block_terms=["prohibited"])
    examples = research_payload("x", "safety_refusal")["holdout"]
    results = compare("safety_refusal", [], examples, safety, .2)
    assert results["candidate_accuracy"] == 1
    assert results["baseline_accuracy"] == 0.5
    assert results["eligible"] is True

    pack = research_payload("x", "efficiency")["holdout"]
    efficient = dict(BASE["efficiency"], top_k=1, max_docs=1)
    score = compare("efficiency", docs(), pack, efficient, .2)
    assert score["eligible"] is True
    assert score["candidate_work_units"] < score["baseline_work_units"]
    assert score["metric"] == "deterministic-retrieval-work-units"
    assert score["bootstrap_lower_bound"] is None


def test_rag_rule_agent_uses_only_visible_examples_and_is_bounded():
    data = research_payload("x")
    proposal = search("retrieval", data["documents"], data["development"], max_proposals=18)
    assert proposal["proposals_tested"] <= 18
    assert proposal["public_development_accuracy"] >= 0
    assert "held-out" in proposal["privacy"]
    validate_artifact("retrieval", proposal["artifact"])
    with pytest.raises(ValueError):
        validate_artifact("retrieval", dict(BASE["retrieval"], __class__="unsafe"))
    with pytest.raises(ValueError):
        validate_artifact("safety_refusal", dict(BASE["safety_refusal"], block_terms=["$(rm -rf /)"]))


def test_research_api_never_promises_escrow_or_billing(client, identities):
    info = client.get("/api/lab/types").json()
    assert set(info["types"]) == {"retrieval", "grounded_qa", "safety_refusal", "efficiency", "llm_prompt"}
    assert info["live_payments"] is False and info["llm_available"] is False
    quote = client.get("/api/lab/fee-quote?reward_lamports=25000").json()
    assert quote["fee_bps"] == 1000
    assert quote["projected_protocol_fee_lamports"] == 2500
    assert quote["collectible"] is False
    owner, ws = bootstrap(client, identities)
    assert ws["billing"] == "not_configured"
    no_llm = client.post("/api/lab/benchmarks", headers=owner, json={
        **research_payload(ws["id"]), "kind": "llm_prompt",
    })
    assert no_llm.status_code == 422
    r = client.get("/api/lab/workspaces", headers=owner)
    assert r.status_code == 200 and len(r.json()["workspaces"]) == 1
    assert client.get("/api/lab/workspaces").status_code == 401

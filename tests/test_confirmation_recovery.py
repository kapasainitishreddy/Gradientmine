import pytest

from gradientmine.cli import make_submission
from gradientmine.crypto import b58encode
from gradientmine.service import Problem
from conftest import login


class NoNewRpcEvidence:
    def confirm(self, *args):
        raise ValueError("RPC unavailable after an already-verified response was lost")


def bounty(client, identities):
    response = client.post("/api/jobs", headers=login(client, identities[0]), json={
        "title": "Confirmation recovery", "duration_seconds": 20, "reward_lamports": 0,
    })
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize("state", ["OPEN", "EVALUATED", "SETTLING", "SETTLED", "NO_WINNER", "REFUNDED"])
def test_lost_funding_confirmation_response_is_recoverable_after_progress(client, app, identities, state):
    job = bounty(client, identities)
    signature = b58encode(bytes(range(64)))
    market = app.state.market
    with market.store.transaction() as db:
        job.update(state=state, funding_signature=signature)
        market.store.save_job(db, job)
    market.chain = NoNewRpcEvidence()
    assert market.confirm(job["id"], identities[0].address, "fund", signature)["state"] == state
    with pytest.raises(Problem, match="different wallet"):
        market.confirm(job["id"], identities[1].address, "fund", signature)
    with pytest.raises(ValueError, match="RPC unavailable"):
        market.confirm(job["id"], identities[0].address, "fund", b58encode(bytes(64)))


@pytest.mark.parametrize("state", ["REGISTERED", "ELIGIBLE", "REJECTED"])
def test_lost_worker_confirmation_response_is_recoverable_after_evaluation(client, app, identities, state):
    job = bounty(client, identities)
    auth = login(client, identities[1])
    package = client.get(f"/api/jobs/{job['id']}/training", headers=auth).json()
    adapter, manifest, _ = make_submission(identities[1], job, package, epochs=1)
    sub = client.post(f"/api/jobs/{job['id']}/submissions", headers=auth,
                      json={"artifact": adapter, "manifest": manifest}).json()
    signature = b58encode(bytes(range(64)))
    market = app.state.market
    with market.store.transaction() as db:
        sub.update(state=state, registration_signature=signature)
        market.store.save_submission(db, sub)
        job["state"] = "EVALUATED"
        market.store.save_job(db, job)
    market.chain = NoNewRpcEvidence()
    detail = market.confirm(job["id"], identities[1].address, "register", signature, sub["id"])
    assert detail["state"] == "EVALUATED" and detail["submissions"][0]["state"] == state

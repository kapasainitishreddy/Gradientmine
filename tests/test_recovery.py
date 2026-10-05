import pytest
from gradientmine.recovery import recovery_decision


def test_pending_payment_is_never_reissued():
    assert recovery_decision({"err": None}, 200, 100, 0) == "confirm"
    assert recovery_decision(None, 99, 100, 0) == "wait"
    assert recovery_decision(None, 101, 100, 1) == "confirm"


def test_retry_requires_expired_or_finalized_failure_and_open_bounty():
    assert recovery_decision(None, 101, 100, 0) == "retry"
    assert (
        recovery_decision({"err": {"failure": 1}, "confirmationStatus": "finalized"}, 101, 100, 0) == "retry"
    )
    assert recovery_decision({"err": 1, "confirmationStatus": "processed"}, 101, 100, 0) == "wait"
    assert recovery_decision(None, 101, 100, 2) == "refunded"
    with pytest.raises(ValueError):
        recovery_decision(None, 101, 100, 9)


def test_recovery_api_requires_auth_and_refuses_local(client, identities):
    from tests.conftest import login

    assert client.post("/api/jobs/x/recover-settlement").status_code == 401
    response = client.post("/api/jobs/x/recover-settlement", headers=login(client, identities[0]))
    assert response.status_code == 409

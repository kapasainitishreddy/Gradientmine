import pytest
from gradientmine.crypto import canonical, safe_json, verify_signed
from conftest import login


@pytest.mark.parametrize("body", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b"not json"])
def test_ambiguous_json_is_rejected(body):
    with pytest.raises(ValueError):
        safe_json(body)


def test_canonical_numbers_cannot_be_nan():
    with pytest.raises(ValueError):
        canonical({"number": float("nan")})


def test_signed_receipt_tampering(identities):
    envelope = identities[0].sign({"score": 0.9})
    assert verify_signed(envelope)
    envelope["payload"]["score"] = 0.99
    assert not verify_signed(envelope)


def test_wallet_challenge_single_use(client, identities):
    person = identities[0]
    challenge = client.post("/api/auth/challenge", json={"address": person.address}).json()
    body = {"nonce": challenge["nonce"], "signature": person.sign_bytes(challenge["message"].encode())}
    assert "does not authorize a transaction" in challenge["message"]
    assert client.post("/api/auth/verify", json=body).status_code == 200
    assert client.post("/api/auth/verify", json=body).status_code == 401


def test_wrong_signer_and_expiry(client, identities, clock):
    challenge = client.post("/api/auth/challenge", json={"address": identities[0].address}).json()
    body = {"nonce": challenge["nonce"], "signature": identities[1].sign_bytes(challenge["message"].encode())}
    assert client.post("/api/auth/verify", json=body).status_code == 401
    challenge = client.post("/api/auth/challenge", json={"address": identities[0].address}).json()
    clock.advance(301)
    body = {"nonce": challenge["nonce"], "signature": identities[0].sign_bytes(challenge["message"].encode())}
    assert client.post("/api/auth/verify", json=body).status_code == 401


def test_auth_required_and_logout(client, identities):
    assert client.post("/api/jobs", json={}).status_code == 401
    auth = login(client, identities[0])
    assert client.get("/api/auth/me", headers=auth).status_code == 200
    assert client.post("/api/auth/logout", headers=auth).status_code == 200
    assert client.get("/api/auth/me", headers=auth).status_code == 401


def test_duplicate_json_keys_and_body_limit(client, identities):
    auth = login(client, identities[0])
    assert client.post("/api/jobs", headers=auth, content=b'{"title":"a","title":"b"}').status_code == 400
    response = client.post("/api/jobs", headers=auth, content=b" " * 262145)
    assert response.status_code == 413


def test_cors_and_security_headers(client):
    result = client.get("/api/config", headers={"Origin": "https://attacker.example"})
    assert result.headers.get("access-control-allow-origin") is None
    assert result.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'self'" in result.headers["content-security-policy"]
    assert client.post("/api/auth/challenge", json={"address": "bad"}).status_code == 422


def test_does_not_serve_private_files(client):
    for url in [
        "/api/artifacts/../../validator.json",
        "/.local/gradientmine/validator.json",
        "/api/evaluation-data",
        "/.env",
    ]:
        assert client.get(url).status_code == 404


def test_nonce_endpoint_rate_limited(client, identities):
    codes = [
        client.post("/api/auth/challenge", json={"address": identities[0].address}).status_code
        for _ in range(16)
    ]
    assert 429 in codes


def test_local_mode_does_not_create_money(client, identities):
    auth = login(client, identities[0])
    r = client.post("/api/jobs", headers=auth, json={"title": "No fake money", "reward_lamports": 25_000_000})
    assert r.status_code == 422
    assert client.get("/api/config").json()["mode"] == "local"


def test_idempotent_creation_and_mismatch(client, identities):
    auth = {**login(client, identities[0]), "Idempotency-Key": "repeatable-job-1"}
    body = {"title": "Improve the classifier", "duration_seconds": 20}
    a = client.post("/api/jobs", headers=auth, json=body)
    b = client.post("/api/jobs", headers=auth, json=body)
    assert a.status_code == b.status_code == 200
    assert a.json()["id"] == b.json()["id"]
    body["title"] = "Different request"
    assert client.post("/api/jobs", headers=auth, json=body).status_code == 409
    assert len(client.get("/api/jobs").json()["jobs"]) == 1

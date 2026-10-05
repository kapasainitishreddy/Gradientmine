import base64
from conftest import login


def test_browser_is_served_with_locked_down_assets(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "GradientMine" in response.text
    assert "assets/main.mjs" in response.text
    assert client.get("/assets/main.mjs").status_code == 200
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert client.get("/assets/../../gradientmine/config.py").status_code == 404


def test_signed_broadcast_requires_authentication_and_refuses_local_mode(client, identities):
    payload = {"action": "fund", "transaction_base64": base64.b64encode(b"bad").decode()}
    response = client.post("/api/jobs/no-job/broadcast", json=payload)
    assert response.status_code == 401
    headers = login(client, identities[0])
    response = client.post("/api/jobs/no-job/broadcast", json=payload, headers=headers)
    assert response.status_code == 409
    assert "Local" in response.json()["error"]


def test_signed_wire_rejects_modified_message_and_missing_signature(identities):
    import pytest
    from solders.hash import Hash
    from solders.keypair import Keypair
    from solders.transaction import Transaction
    from gradientmine.chain import Chain
    from gradientmine.crypto import digest

    owner, validator = identities[:2]
    chain = Chain(str(Keypair().pubkey()))
    job = {
        "id": "00000000-0000-0000-0000-000000000001",
        "creator": owner.address,
        "policy": {
            "validator": validator.address,
            "deadline": 2000000100,
            "refund_after": 2000003700,
            "reward_lamports": 25000000,
        },
    }
    job["policy_sha256"] = digest(job["policy"])
    spec = chain.spec("fund", job)
    tx = chain.unsigned(spec, str(Hash.default()))
    with pytest.raises(ValueError):
        chain.validate_signed(bytes(tx), spec)
    tx.sign([Keypair.from_bytes(owner.solana_bytes())], tx.message.recent_blockhash)
    assert chain.validate_signed(bytes(tx), spec)["signature"] == str(tx.signatures[0])
    altered = {**spec, "data": spec["data"][:-1] + b"\xff"}
    with pytest.raises(ValueError):
        chain.validate_signed(bytes(tx), altered)
    wrong = Transaction.new_signed_with_payer(
        [chain.instruction(altered)],
        Keypair.from_bytes(owner.solana_bytes()).pubkey(),
        [Keypair.from_bytes(owner.solana_bytes())],
        Hash.default(),
    )
    with pytest.raises(ValueError):
        chain.validate_signed(bytes(wrong), spec)

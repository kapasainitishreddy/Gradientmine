from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from gradientmine.config import Settings
from gradientmine.crypto import Identity


@pytest.fixture
def clock():
    class Clock:
        now = 2_000_000_000.0

        def __call__(self):
            return self.now

        def advance(self, seconds):
            self.now += seconds

    return Clock()


@pytest.fixture
def app(tmp_path, clock):
    from gradientmine.api import create_app

    return create_app(Settings(root=tmp_path / "state"), clock=clock)


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def identities(tmp_path):
    return [Identity.create(Path(tmp_path) / f"person-{i}.json") for i in range(4)]


def login(client, identity):
    challenge = client.post("/api/auth/challenge", json={"address": identity.address}).json()
    response = client.post(
        "/api/auth/verify",
        json={
            "nonce": challenge["nonce"],
            "signature": identity.sign_bytes(challenge["message"].encode()),
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["token"]}

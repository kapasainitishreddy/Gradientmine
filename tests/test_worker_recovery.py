"""Crash-boundary regression tests use actual wallet-signed Solana transactions."""

import base64
import copy
import struct
from types import SimpleNamespace

import httpx
import pytest
from solders.hash import Hash
from solders.keypair import Keypair

from gradientmine.chain import Chain
from gradientmine.crypto import Identity, b58decode, b58encode, canonical, digest, safe_json
from gradientmine.rpc import validate_transaction
from gradientmine.worker_recovery import load_state, recover_registration, save_state


@pytest.fixture
def recovery(tmp_path):
    identity = Identity.create(tmp_path / "identity.json")
    policy = {
        "validator": str(Keypair().pubkey()),
        "deadline": 2000,
        "refund_after": 5600,
        "reward_lamports": 1000,
        "parent_sha256": "11" * 32,
        "train_sha256": "22" * 32,
    }
    job = {
        "id": "recovery-job",
        "creator": str(Keypair().pubkey()),
        "policy": policy,
        "policy_sha256": digest(policy),
    }
    adapter = {
        "format": "gradientmine.adapter.v1",
        "parent_sha256": policy["parent_sha256"],
        "rank": 1,
        "a": [[0.1] * 48],
        "b": [[0.1] for _ in range(10)],
    }
    manifest = identity.sign(
        {
            "format": "gradientmine.submission.v1",
            "job_id": job["id"],
            "policy_sha256": job["policy_sha256"],
            "parent_sha256": policy["parent_sha256"],
            "training_data_sha256": policy["train_sha256"],
            "artifact_sha256": digest(adapter),
        }
    )
    sub = {
        "id": "submission-id",
        "job_id": job["id"],
        "worker": identity.address,
        "artifact_sha256": digest(adapter),
        "manifest_sha256": digest(manifest),
        "state": "AWAITING_REGISTRATION",
        "registration_signature": None,
    }

    class FakeRpc:
        status = None
        height = 99
        registered = None
        block_valid = True
        chain_time = 1999
        sends = 0
        send_error = None

        def __init__(self):
            self.signed = {}
            self.history = []
            self.transactions = []

        def require_devnet(self):
            return "devnet"

        def account(self, address):
            if address == chain.program_id:
                return {"executable": True}
            return self.registered

        def call(self, method, params=None):
            if method == "getSignatureStatuses":
                if state["attempts"] and params[0][0] != state["attempts"][0]["signature"]:
                    return {"value": [None]}
                return {"value": [self.status]}
            if method == "getBlockHeight":
                return self.height
            if method == "getSlot":
                return self.height
            if method == "getBlockTime":
                return self.chain_time
            if method == "isBlockhashValid":
                return {"value": self.block_valid}
            if method == "sendTransaction":
                from solders.transaction import Transaction

                self.sends += 1
                tx = Transaction.from_bytes(base64.b64decode(params[0]))
                signature = str(tx.signatures[0])
                self.signed[signature] = {
                    "signature": signature,
                    "transaction_base64": params[0],
                    "last_valid_block_height": self.height + 1,
                }
                if self.send_error:
                    raise self.send_error
                return signature
            if method == "getSignaturesForAddress":
                return self.history
            if method == "getTransaction":
                signature = params[0]
                return self.transaction(signature, chain.spec("register", job, sub))
            raise AssertionError(method)

        def transaction(self, signature, spec):
            from solders.transaction import Transaction

            self.transactions.append(signature)
            signed = self.signed[signature]
            tx = Transaction.from_bytes(base64.b64decode(signed["transaction_base64"]))
            message = tx.message
            value = {
                "transaction": {
                    "signatures": [signature],
                    "message": {
                        "accountKeys": [str(key) for key in message.account_keys],
                        "header": safe_json(message.header.to_json().encode()),
                        "instructions": [
                            {
                                "programIdIndex": item.program_id_index,
                                "accounts": list(item.accounts),
                                "data": b58encode(item.data),
                            }
                            for item in message.instructions
                        ],
                    },
                },
                "meta": {"err": None, "fee": 5000},
            }
            return validate_transaction(value, signature, spec)

    rpc = FakeRpc()
    chain = Chain(str(Keypair().pubkey()), rpc=rpc)
    chain.read_bounty = lambda value: ({"state": 0}, {})
    state = {
        "format": "gradientmine.worker-state.v1",
        "origin": "http://localhost:8000",
        "mode": "devnet",
        "program_id": chain.program_id,
        "rpc": "https://api.devnet.solana.com",
        "worker": identity.address,
        "job": job,
        "artifact": adapter,
        "manifest": manifest,
        "losses": [1.0, 0.5],
        "submission": sub,
        "pending": None,
        "attempts": [],
        "stage": "submitted",
    }
    saves, confirmed, intents = [], [], []

    def persist():
        save_state(tmp_path, state, identity)
        saves.append(copy.deepcopy(state))

    def intent():
        intents.append(True)
        unsigned = chain.unsigned(chain.spec("register", job, sub), str(Hash.new_unique()))
        return {
            "chain": "solana:devnet",
            "transaction_base64": base64.b64encode(bytes(unsigned)).decode(),
            "last_valid_block_height": rpc.height + 1,
        }

    def confirm(signature):
        confirmed.append(signature)

    def run():
        return recover_registration(chain, state, identity, intent, confirm, persist)

    def register_account():
        raw = (
            b"GMSUBM01"
            + b58decode(chain.bounty_address(job))
            + b58decode(identity.address)
            + bytes.fromhex(sub["artifact_sha256"])
            + bytes.fromhex(sub["manifest_sha256"])
            + struct.pack("<q", 1999)
        )
        rpc.registered = {"owner": chain.program_id, "data": [base64.b64encode(raw).decode(), "base64"]}

    return SimpleNamespace(**locals())


def test_signed_registration_is_durable_before_lost_broadcast_response(recovery):
    r = recovery
    r.rpc.send_error = httpx.ReadTimeout("response lost after RPC accepted bytes")
    with pytest.raises(httpx.ReadTimeout):
        r.run()
    saved = load_state(r.tmp_path, r.identity)
    assert saved["pending"]["signature"] == r.state["pending"]["signature"]
    assert r.saves[0]["pending"] is not None
    assert r.rpc.sends == 1
    r.rpc.send_error = None
    r.rpc.status = {"err": None, "confirmationStatus": "finalized"}
    r.register_account()
    r.run()
    assert r.rpc.sends == 1
    assert len(r.intents) == 1
    assert r.state["stage"] == "finalized"


def test_restart_after_process_crash_resends_only_identical_signed_bytes(recovery):
    r = recovery
    r.rpc.send_error = KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        r.run()
    first = r.state["pending"].copy()
    r.state.clear()
    r.state.update(load_state(r.tmp_path, r.identity))
    r.rpc.send_error = None
    r.run()
    assert r.state["pending"] == first
    assert len(r.intents) == 1


def test_constructed_intent_crash_before_signing_does_not_broadcast(recovery, monkeypatch):
    r = recovery
    r.persist()

    def crash(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(r.chain, "sign_intent", crash)
    with pytest.raises(KeyboardInterrupt):
        r.run()
    assert len(r.intents) == 1
    assert r.rpc.sends == 0
    assert load_state(r.tmp_path, r.identity)["pending"] is None


def test_signed_checkpoint_write_failure_prevents_any_network_broadcast(recovery):
    r = recovery
    r.persist()

    def write_failure():
        if r.state["stage"] == "signed":
            raise OSError("disk full before signed checkpoint can be persisted")
        r.persist()

    with pytest.raises(OSError, match="disk full"):
        recover_registration(r.chain, r.state, r.identity, r.intent, r.confirm, write_failure)
    assert r.rpc.sends == 0
    assert load_state(r.tmp_path, r.identity)["pending"] is None


def test_confirmation_response_lost_is_repeated_without_broadcast(recovery):
    r = recovery
    r.run()
    r.register_account()
    r.rpc.status = {"err": None, "confirmationStatus": "finalized"}
    successful_confirms = []

    def lose_response(signature):
        successful_confirms.append(signature)
        raise httpx.ReadTimeout("server already committed confirmation")

    with pytest.raises(httpx.ReadTimeout):
        recover_registration(r.chain, r.state, r.identity, r.intent, lose_response, r.persist)
    r.run()
    assert r.rpc.sends == 1
    assert len(successful_confirms) == 1
    assert r.state["stage"] == "finalized"


@pytest.mark.parametrize(
    "status,stage",
    [
        (None, "unknown"),
        ({"err": {"InstructionError": [0, "x"]}, "confirmationStatus": "finalized"}, "failed"),
    ],
)
def test_failed_and_unknown_are_distinct_and_neither_is_replaced_while_valid(recovery, status, stage):
    r = recovery
    r.run()
    r.rpc.status = status
    r.run()
    assert r.state["stage"] == stage
    assert len(r.intents) == 1


@pytest.mark.parametrize("status", [None, {"err": 1, "confirmationStatus": "finalized"}])
def test_expired_absent_or_finalized_failure_gets_safe_replacement(recovery, status):
    r = recovery
    r.run()
    original = r.state["pending"].copy()
    r.rpc.status = status
    r.rpc.height = 101
    r.rpc.block_valid = False
    r.run()
    assert len(r.intents) == 2
    assert r.state["pending"]["signature"] != original["signature"]
    assert r.state["attempts"] == [original]


@pytest.mark.parametrize(
    "status,valid",
    [
        ({"err": None, "confirmationStatus": "processed"}, False),
        ({"err": 1, "confirmationStatus": "processed"}, False),
        (None, True),
    ],
)
def test_expiry_alone_does_not_replace_possible_live_transaction(recovery, status, valid):
    r = recovery
    r.run()
    r.rpc.height = 101
    r.rpc.status = status
    r.rpc.block_valid = valid
    r.run()
    assert len(r.intents) == 1


def test_registration_account_commitments_must_match_before_recovery(recovery):
    r = recovery
    r.run()
    r.register_account()
    raw = base64.b64decode(r.rpc.registered["data"][0])
    r.rpc.registered["data"][0] = base64.b64encode(raw[:72] + b"x" * 32 + raw[104:]).decode()
    with pytest.raises(ValueError, match="commitment"):
        r.run()
    assert len(r.intents) == 1


def test_finalized_account_recovers_missing_pending_signature_from_exact_history(recovery):
    r = recovery
    r.run()
    signature = r.state["pending"]["signature"]
    r.register_account()
    r.rpc.status = {"err": None, "confirmationStatus": "finalized"}
    r.rpc.history = [{"signature": signature, "err": None}]
    r.state["pending"] = None
    assert r.run() == "finalized"
    assert r.state["submission"]["registration_signature"] == signature
    assert r.rpc.transactions == [signature, signature]
    assert len(r.intents) == r.rpc.sends == 1


def test_finalized_account_without_available_transaction_never_gets_new_signature(recovery):
    r = recovery
    r.run()
    r.register_account()
    r.state["pending"] = None
    with pytest.raises(ValueError, match="transaction is unavailable"):
        r.run()
    assert len(r.intents) == r.rpc.sends == 1


def test_rpc_timeout_before_signed_broadcast_never_replaces_saved_intent(recovery, monkeypatch):
    r = recovery
    r.run()
    original = r.state["pending"].copy()
    original_call = r.rpc.call

    def timeout(method, params=None):
        if method == "getSignatureStatuses":
            raise ValueError("Solana RPC unavailable; no confirmation can be inferred")
        return original_call(method, params)

    monkeypatch.setattr(r.rpc, "call", timeout)
    with pytest.raises(ValueError, match="unavailable"):
        r.run()
    assert load_state(r.tmp_path, r.identity)["pending"] == original
    assert len(r.intents) == r.rpc.sends == 1


def test_terminal_bounty_does_not_broadcast_pending_registration(recovery):
    r = recovery
    r.run()
    r.chain.read_bounty = lambda value: ({"state": 2}, {})
    with pytest.raises(ValueError, match="terminal"):
        r.run()
    assert r.rpc.sends == 1


def test_expired_registration_is_not_replaced_after_finalized_deadline(recovery):
    r = recovery
    r.run()
    r.rpc.height = 101
    r.rpc.block_valid = False
    r.rpc.chain_time = 2000
    with pytest.raises(ValueError, match="deadline"):
        r.run()
    assert len(r.intents) == r.rpc.sends == 1


def test_finalized_success_status_without_account_is_never_recorded_as_registered(recovery):
    r = recovery
    r.run()
    r.rpc.status = {"err": None, "confirmationStatus": "finalized"}
    with pytest.raises(ValueError, match="submission account"):
        r.run()
    assert not r.confirmed
    assert r.state["stage"] != "finalized"


def test_pending_signature_or_instruction_tampering_is_rejected(recovery):
    r = recovery
    r.run()
    r.state["pending"]["signature"] = str(Keypair().sign_message(b"wrong"))
    with pytest.raises(ValueError, match="signature"):
        r.persist()


def test_devnet_cli_restart_after_server_confirmation_loss_uses_finalized_original(recovery, monkeypatch):
    from gradientmine import chain as chain_module, cli

    r = recovery
    r.persist()
    server_sub = copy.deepcopy(r.sub)
    api_writes = []
    lost_confirmation = []

    def transport(request):
        if request.url.path == "/api/config":
            return httpx.Response(
                200,
                json={
                    "origin": r.state["origin"],
                    "mode": "devnet",
                    "program_id": r.chain.program_id,
                },
            )
        if request.method == "GET" and request.url.path == f"/api/jobs/{r.job['id']}":
            return httpx.Response(200, json={**r.job, "submissions": [server_sub]})
        api_writes.append(request.url.path)
        if request.url.path.endswith("/transaction"):
            return httpx.Response(200, json=r.intent())
        if request.url.path.endswith("/confirm"):
            body = safe_json(request.content)
            server_sub.update(state="REGISTERED", registration_signature=body["signature"])
            lost_confirmation.append(body)
            raise httpx.ReadTimeout("confirmation committed; response lost")
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    def wait(signature):
        r.rpc.status = {"err": None, "confirmationStatus": "finalized"}
        r.register_account()

    monkeypatch.setattr(r.rpc, "wait", wait, raising=False)
    monkeypatch.setattr(chain_module, "Chain", lambda *args: r.chain)
    monkeypatch.setattr(cli, "login", lambda *args: None)
    monkeypatch.setattr(
        cli,
        "client_for",
        lambda url: (
            httpx.Client(base_url=url, transport=httpx.MockTransport(transport)),
            url,
        ),
    )
    monkeypatch.setattr(cli, "make_submission", lambda *args, **kw: pytest.fail("retrained on resume"))
    args = SimpleNamespace(
        identity=str(r.tmp_path / "identity.json"),
        api=r.state["origin"],
        out=str(r.tmp_path),
        resume=True,
        job=r.job["id"],
        rpc=r.state["rpc"],
        program_id=r.chain.program_id,
    )
    with pytest.raises(httpx.ReadTimeout):
        cli.worker(args)
    saved_signature = load_state(r.tmp_path, r.identity)["pending"]["signature"]
    result = cli.worker(args)
    assert result["registration_signature"] == saved_signature
    assert r.rpc.sends == len(r.intents) == 1
    assert len(lost_confirmation) == 1
    assert all(not path.endswith("/submissions") for path in api_writes)
    assert load_state(r.tmp_path, r.identity)["stage"] == "complete"


def test_state_rejects_tampering_wrong_identity_and_oversize(recovery):
    r = recovery
    r.persist()
    path = r.tmp_path / "worker-state.json"
    envelope = safe_json(path.read_bytes(), limit=2_000_000)
    assert "secret_key" not in path.read_text()
    assert "Authorization" not in path.read_text()
    with pytest.raises(ValueError):
        load_state(r.tmp_path, Identity(bytes(32)))
    envelope["payload"]["rpc"] = "https://attacker.example"
    path.write_bytes(canonical(envelope))
    with pytest.raises(ValueError):
        load_state(r.tmp_path, r.identity)
    path.write_bytes(b" " * 2_000_001)
    with pytest.raises(ValueError):
        load_state(r.tmp_path, r.identity)


@pytest.fixture
def worker_api(client, identities, tmp_path, monkeypatch, clock):
    from gradientmine import cli
    from tests.conftest import login

    monkeypatch.setattr(cli.time, "time", clock)

    job = client.post(
        "/api/jobs",
        headers=login(client, identities[0]),
        json={
            "title": "Crash-safe real training",
            "duration_seconds": 100,
            "reward_lamports": 0,
            "minimum_delta": 0.01,
        },
    ).json()
    origin = client.get("/api/config").json()["origin"]
    monkeypatch.setattr(cli, "client_for", lambda url: (client, origin))
    args = SimpleNamespace(
        api=origin,
        job=job["id"],
        identity=str(tmp_path / "person-1.json"),
        out=str(tmp_path / "worker"),
        resume=False,
        program_id=None,
        rpc="https://api.devnet.solana.com",
        epochs=2,
        rank=1,
        lr=0.03,
        seed=7,
        negative_control=False,
    )
    training = []
    original_training = cli.make_submission

    def train(*a, **kw):
        training.append(True)
        return original_training(*a, **kw)

    monkeypatch.setattr(cli, "make_submission", train)
    return SimpleNamespace(**locals())


def test_lost_submission_response_resumes_real_training_without_duplicate_upload(worker_api, monkeypatch):
    r = worker_api
    uploads = []
    original = r.cli.request

    def lose_response(client, method, url, **kwargs):
        if method == "POST" and url.endswith("/submissions"):
            saved = load_state(r.args.out, r.identities[1])
            assert saved["stage"] == "trained"
            assert saved["submission"] is None
            result = original(client, method, url, **kwargs)
            uploads.append(result)
            raise httpx.ReadTimeout("submission committed, HTTP response lost")
        return original(client, method, url, **kwargs)

    monkeypatch.setattr(r.cli, "request", lose_response)
    with pytest.raises(httpx.ReadTimeout):
        r.cli.worker(r.args)
    r.args.resume = True
    resumed = r.cli.worker(r.args)
    assert resumed["id"] == uploads[0]["id"]
    assert len(uploads) == len(r.training) == 1
    assert len(r.client.get(f"/api/jobs/{r.job['id']}").json()["submissions"]) == 1


def test_crash_before_submission_uses_original_signed_artifact_on_restart(worker_api, monkeypatch):
    r = worker_api
    original = r.cli.request

    def crash(client, method, url, **kwargs):
        if method == "POST" and url.endswith("/submissions"):
            assert load_state(r.args.out, r.identities[1])["stage"] == "trained"
            raise KeyboardInterrupt()
        return original(client, method, url, **kwargs)

    monkeypatch.setattr(r.cli, "request", crash)
    with pytest.raises(KeyboardInterrupt):
        r.cli.worker(r.args)
    saved_manifest = load_state(r.args.out, r.identities[1])["manifest"]
    monkeypatch.setattr(r.cli, "request", original)
    r.args.resume = True
    resumed = r.cli.worker(r.args)
    assert resumed["manifest_sha256"] == digest(saved_manifest)
    assert len(r.training) == 1


def test_resume_rejects_changed_bindings_and_existing_output_cannot_be_overwritten(worker_api):
    r = worker_api
    r.cli.worker(r.args)
    with pytest.raises(ValueError, match="--resume"):
        r.cli.worker(r.args)
    r.args.resume = True
    r.args.rpc = "https://different-rpc.example"
    with pytest.raises(ValueError, match="binding"):
        r.cli.worker(r.args)
    assert len(r.training) == 1


def test_resume_rejects_another_server_submission_instead_of_reuploading(worker_api, monkeypatch):
    r = worker_api
    r.cli.worker(r.args)
    original = r.cli.request

    def mutate(client, method, url, **kwargs):
        result = original(client, method, url, **kwargs)
        if method == "GET" and url == f"/api/jobs/{r.job['id']}":
            result["submissions"][0]["manifest_sha256"] = "ff" * 32
        return result

    r.args.resume = True
    monkeypatch.setattr(r.cli, "request", mutate)
    with pytest.raises(ValueError, match="commitments"):
        r.cli.worker(r.args)
    assert len(r.training) == 1

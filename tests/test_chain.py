import copy
import json
import os
from pathlib import Path

import pytest
from solders.hash import Hash
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from solders.system_program import transfer, TransferParams

from gradientmine.chain import Chain
from gradientmine.crypto import b58encode, digest
from gradientmine.rpc import validate_transaction
from gradientmine.wire import decode_bounty, decode_submission, BOUNTY_SIZE


@pytest.fixture
def vm():
    path = Path(os.getenv("GM_SBF_PATH", ".local/sbf/gradientmine_escrow.so"))
    if not path.is_file():
        pytest.skip(
            "Build the SBF program or set GM_SBF_PATH; this is not counted as verified Devnet execution"
        )
    machine = LiteSVM()
    program = Keypair().pubkey()
    machine.add_program_from_file(program, path)
    actors = [Keypair() for _ in range(5)]
    for actor in actors:
        result = machine.airdrop(actor.pubkey(), 10_000_000_000)
        assert not isinstance(result, FailedTransactionMetadata)
    chain = Chain(str(program))
    now = machine.get_clock().unix_timestamp
    policy = {
        "validator": str(actors[1].pubkey()),
        "deadline": now + 100,
        "refund_after": now + 3700,
        "reward_lamports": 25_000_000,
    }
    job = {
        "id": "00000000-0000-0000-0000-000000000001",
        "creator": str(actors[0].pubkey()),
        "policy": policy,
        "policy_sha256": digest(policy),
    }
    return machine, chain, actors, job


def send(vm, spec, actor):
    machine, chain, _, _ = vm
    machine.expire_blockhash()
    tx = Transaction.new_signed_with_payer(
        [chain.instruction(spec)], actor.pubkey(), [actor], machine.latest_blockhash()
    )
    result = machine.send_transaction(tx)
    return result, tx


def success(value):
    assert not isinstance(value, FailedTransactionMetadata), str(value)


def advance(vm, timestamp):
    machine = vm[0]
    clock = machine.get_clock()
    clock.unix_timestamp = timestamp
    machine.set_clock(clock)


def register(vm, actor_index=2):
    machine, chain, actors, job = vm
    sub = {
        "worker": str(actors[actor_index].pubkey()),
        "artifact_sha256": "a1" * 32,
        "manifest_sha256": "b2" * 32,
        "receipt_sha256": "c3" * 32,
    }
    result, _ = send(vm, chain.spec("register", job, sub), actors[actor_index])
    success(result)
    return sub


def test_compiled_escrow_full_payout_and_duplicate_rejection(vm):
    machine, chain, actors, job = vm
    success(send(vm, chain.spec("fund", job), actors[0])[0])
    bounty = Pubkey.from_string(chain.bounty_address(job))
    rent = machine.minimum_balance_for_rent_exemption(BOUNTY_SIZE)
    assert machine.get_balance(bounty) == rent + job["policy"]["reward_lamports"]
    sub = register(vm)
    receipt = decode_submission(
        machine.get_account(Pubkey.from_string(chain.submission_address(job, sub["worker"]))).data
    )
    assert receipt["artifact_sha256"] == sub["artifact_sha256"]
    advance(vm, job["policy"]["deadline"])
    before = machine.get_balance(actors[2].pubkey())
    result, tx = send(vm, chain.spec("settle", job, sub), actors[1])
    success(result)
    assert machine.get_balance(actors[2].pubkey()) - before == job["policy"]["reward_lamports"]
    assert machine.get_balance(bounty) == rent
    state = decode_bounty(machine.get_account(bounty).data)
    assert state["state"] == 1 and state["winner"] == sub["worker"]
    assert state["receipt_sha256"] == sub["receipt_sha256"]
    assert isinstance(send(vm, chain.spec("settle", job, sub), actors[1])[0], FailedTransactionMetadata)
    advance(vm, job["policy"]["refund_after"])
    assert isinstance(send(vm, chain.spec("refund", job), actors[0])[0], FailedTransactionMetadata)


def test_wrong_validator_early_settlement_and_wrong_recipient_fail(vm):
    machine, chain, actors, job = vm
    success(send(vm, chain.spec("fund", job), actors[0])[0])
    sub = register(vm)
    assert isinstance(send(vm, chain.spec("settle", job, sub), actors[1])[0], FailedTransactionMetadata)
    advance(vm, job["policy"]["deadline"])
    wrong = copy.deepcopy(job)
    wrong["policy"]["validator"] = str(actors[3].pubkey())
    assert isinstance(send(vm, chain.spec("settle", wrong, sub), actors[3])[0], FailedTransactionMetadata)
    wrong_sub = {**sub, "worker": str(actors[4].pubkey())}
    assert isinstance(send(vm, chain.spec("settle", job, wrong_sub), actors[1])[0], FailedTransactionMetadata)
    assert isinstance(
        send(vm, chain.spec("settle", job, {**sub, "artifact_sha256": "d4" * 32}), actors[1])[0],
        FailedTransactionMetadata,
    )
    assert (
        decode_bounty(machine.get_account(Pubkey.from_string(chain.bounty_address(job))).data)["state"] == 0
    )


def test_refund_after_timeout_only_and_exact_balance(vm):
    machine, chain, actors, job = vm
    success(send(vm, chain.spec("fund", job), actors[0])[0])
    assert isinstance(send(vm, chain.spec("refund", job), actors[0])[0], FailedTransactionMetadata)
    advance(vm, job["policy"]["refund_after"])
    before = machine.get_balance(actors[0].pubkey())
    result, tx = send(vm, chain.spec("refund", job), actors[0])
    success(result)
    assert machine.get_balance(actors[0].pubkey()) - before == job["policy"]["reward_lamports"] - 5000
    assert (
        decode_bounty(machine.get_account(Pubkey.from_string(chain.bounty_address(job))).data)["state"] == 2
    )
    assert isinstance(send(vm, chain.spec("refund", job), actors[0])[0], FailedTransactionMetadata)


def test_duplicate_registration_and_post_deadline_registration_fail(vm):
    machine, chain, actors, job = vm
    success(send(vm, chain.spec("fund", job), actors[0])[0])
    sub = register(vm)
    assert isinstance(send(vm, chain.spec("register", job, sub), actors[2])[0], FailedTransactionMetadata)
    advance(vm, job["policy"]["deadline"])
    sub["worker"] = str(actors[3].pubkey())
    assert isinstance(send(vm, chain.spec("register", job, sub), actors[3])[0], FailedTransactionMetadata)


def test_prefunded_pda_is_not_permanently_blocked(vm):
    machine, chain, actors, job = vm
    ix = transfer(
        TransferParams(
            from_pubkey=actors[4].pubkey(),
            to_pubkey=Pubkey.from_string(chain.bounty_address(job)),
            lamports=machine.minimum_balance_for_rent_exemption(0),
        )
    )
    tx = Transaction.new_signed_with_payer([ix], actors[4].pubkey(), [actors[4]], machine.latest_blockhash())
    success(machine.send_transaction(tx))
    success(send(vm, chain.spec("fund", job), actors[0])[0])
    assert (
        decode_bounty(machine.get_account(Pubkey.from_string(chain.bounty_address(job))).data)["state"] == 0
    )


def test_unsigned_intent_rejects_server_instruction_swap():
    actors = [Keypair() for _ in range(3)]
    chain = Chain(str(actors[0].pubkey()))
    job = {
        "id": "test",
        "creator": str(actors[1].pubkey()),
        "policy_sha256": "aa" * 32,
        "policy": {
            "validator": str(actors[2].pubkey()),
            "deadline": 2000,
            "refund_after": 5600,
            "reward_lamports": 1_000_000,
        },
    }
    spec = chain.spec("fund", job)
    unsigned = chain.unsigned(spec, str(Hash.default()))
    chain.validate_unsigned(bytes(unsigned), spec)
    modified = {**spec, "data": spec["data"][:-1] + b"\xff"}
    with pytest.raises(ValueError):
        chain.validate_unsigned(bytes(chain.unsigned(modified, str(Hash.default()))), spec)


def transaction_fixture():
    actors = [Keypair() for _ in range(3)]
    chain = Chain(str(actors[0].pubkey()))
    job = {
        "id": "test",
        "creator": str(actors[1].pubkey()),
        "policy_sha256": "aa" * 32,
        "policy": {
            "validator": str(actors[2].pubkey()),
            "deadline": 2000,
            "refund_after": 5600,
            "reward_lamports": 1_000_000,
        },
    }
    spec = chain.spec("fund", job)
    tx = Transaction.new_signed_with_payer(
        [chain.instruction(spec)], actors[1].pubkey(), [actors[1]], Hash.default()
    )
    message = tx.message
    payload = {
        "transaction": {
            "signatures": [str(tx.signatures[0])],
            "message": {
                "accountKeys": [str(k) for k in message.account_keys],
                "header": json.loads(message.header.to_json()),
                "instructions": [
                    {
                        "programIdIndex": i.program_id_index,
                        "accounts": list(i.accounts),
                        "data": b58encode(i.data),
                    }
                    for i in message.instructions
                ],
            },
        },
        "meta": {"err": None, "fee": 5000},
    }
    return payload, str(tx.signatures[0]), spec


def test_finalized_transaction_exact_intent():
    payload, signature, spec = transaction_fixture()
    assert validate_transaction(payload, signature, spec) == payload


@pytest.mark.parametrize(
    "attack", ["extra-instruction", "wrong-payer", "wrong-program", "data", "failed", "fee", "duplicate-keys"]
)
def test_finalized_transaction_rejects_wrong_evidence(attack):
    value, signature, spec = transaction_fixture()
    message = value["transaction"]["message"]
    if attack == "extra-instruction":
        message["instructions"].append(message["instructions"][0])
    elif attack == "wrong-payer":
        message["accountKeys"][0] = str(Keypair().pubkey())
    elif attack == "wrong-program":
        message["instructions"][0]["programIdIndex"] = 0
    elif attack == "data":
        message["instructions"][0]["data"] = b58encode(b"bad")
    elif attack == "failed":
        value["meta"]["err"] = {"InstructionError": [0, "InvalidArgument"]}
    elif attack == "fee":
        value["meta"]["fee"] = 100001
    elif attack == "duplicate-keys":
        message["accountKeys"].append(message["accountKeys"][0])
    with pytest.raises(ValueError):
        validate_transaction(value, signature, spec)


@pytest.mark.parametrize("field,value", [("numRequiredSignatures", True), ("numReadonlySignedAccounts", False)])
def test_finalized_transaction_rejects_boolean_privilege_counts(field, value):
    payload, signature, spec = transaction_fixture()
    payload["transaction"]["message"]["header"][field] = value
    with pytest.raises(ValueError):
        validate_transaction(payload, signature, spec)


def test_finalized_transaction_rejects_writable_program_account():
    payload, signature, spec = transaction_fixture()
    message = payload["transaction"]["message"]
    old = message["accountKeys"][:]
    # Keep every intended instruction account's privileges while moving only
    # the invoked program into the writable prefix.
    message["accountKeys"] = [spec["payer"], spec["accounts"][1][0], spec["program"], spec["accounts"][2][0]]
    instruction = message["instructions"][0]
    instruction["accounts"] = [message["accountKeys"].index(old[i]) for i in instruction["accounts"]]
    instruction["programIdIndex"] = 2
    message["header"]["numReadonlyUnsignedAccounts"] = 1
    with pytest.raises(ValueError):
        validate_transaction(payload, signature, spec)

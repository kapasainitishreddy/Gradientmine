"""Creator refund directly from public account data, without the coordinator API."""

from __future__ import annotations
import base64
from pathlib import Path
from solders.hash import Hash
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from gradientmine.chain import Chain
from gradientmine.crypto import Identity, b58decode, canonical, validate_address
from gradientmine.store import atomic_write
from gradientmine.wire import decode_bounty


def refund_address(bounty_address, program_id, identity_path, rpc_url, out):
    validate_address(bounty_address)
    chain = Chain(program_id, rpc_url)
    chain.deployment()
    identity = Identity.load(Path(identity_path))
    account = chain.rpc.account(bounty_address)
    if not account or account["owner"] != program_id:
        raise ValueError("Bounty not found under the expected program")
    bounty = decode_bounty(base64.b64decode(account["data"][0], validate=True))
    expected, _ = Pubkey.find_program_address(
        [b"bounty", b58decode(bounty["creator"]), bytes.fromhex(bounty["job_key"])], chain.program
    )
    if str(expected) != bounty_address or bounty["creator"] != identity.address or bounty["state"] != 0:
        raise ValueError("Wrong bounty, wrong creator, or reward already paid/refunded")
    slot = chain.rpc.call("getSlot", [{"commitment": "finalized"}])
    now = chain.rpc.call("getBlockTime", [slot])
    if type(now) is not int or now < bounty["refund_after"]:
        raise ValueError("The immutable on-chain refund time has not passed")
    spec = {
        "payer": identity.address,
        "program": program_id,
        "accounts": [(identity.address, True, True), (bounty_address, False, True)],
        "data": b"\x03",
    }
    block = chain.rpc.call("getLatestBlockhash", [{"commitment": "finalized"}])["value"]
    tx = chain.unsigned(spec, str(Hash.from_string(block["blockhash"])))
    fee = chain.rpc.call(
        "getFeeForMessage", [base64.b64encode(bytes(tx.message)).decode(), {"commitment": "finalized"}]
    )["value"]
    if type(fee) is not int or not 0 <= fee <= 100000:
        raise ValueError("No acceptable fee quote; refusing refund transaction")
    tx.sign([Keypair.from_bytes(identity.solana_bytes())], tx.message.recent_blockhash)
    pending = {
        "signature": str(tx.signatures[0]),
        "transaction_base64": base64.b64encode(bytes(tx)).decode(),
        "last_valid_block_height": block["lastValidBlockHeight"],
    }
    atomic_write(
        Path(out),
        canonical(
            {
                "mode": "devnet",
                "action": "refund",
                "bounty": bounty_address,
                "pending": pending,
                "finalized": False,
            }
        ),
    )
    signature = chain.send_signed(pending)
    evidence = chain.rpc.transaction(signature, spec)
    after = chain.rpc.account(bounty_address)
    state = decode_bounty(base64.b64decode(after["data"][0], validate=True))
    if state["state"] != 2:
        raise ValueError("Refund state not finalized; retain the public transaction receipt")
    keys = evidence["transaction"]["message"]["accountKeys"]
    i = keys.index(identity.address)
    b = keys.index(bounty_address)
    meta = evidence["meta"]
    reward = bounty["reward_lamports"]
    if (
        meta["postBalances"][i] - meta["preBalances"][i] != reward - meta["fee"]
        or meta["preBalances"][b] - meta["postBalances"][b] != reward
    ):
        raise ValueError("Refund balance evidence differs from the committed reward")
    result = {
        "mode": "devnet",
        "action": "refund",
        "bounty": bounty_address,
        "program_id": program_id,
        "signature": signature,
        "reward_lamports": reward,
        "fee_lamports": meta["fee"],
        "finalized": True,
        "explorer": f"https://explorer.solana.com/tx/{signature}?cluster=devnet",
    }
    atomic_write(Path(out), canonical(result))
    return result

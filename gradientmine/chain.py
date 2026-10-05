"""Solana SDK boundary. Legacy transactions, Devnet genesis pinning, exact intent verification."""

from __future__ import annotations

import base64
import struct
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction

from .crypto import b58decode, b58encode, digest, validate_address
from .rpc import Rpc
from .wire import (
    BOUNTY_SIZE,
    SUBMISSION_SIZE,
    create_data,
    decode_bounty,
    decode_submission,
    job_key,
    registration_data,
    settlement_data,
)

SYSTEM = "11111111111111111111111111111111"


class Chain:
    def __init__(self, program_id, rpc_url="https://api.devnet.solana.com", rpc=None):
        validate_address(program_id)
        if program_id == SYSTEM:
            raise ValueError("The System Program is not a GradientMine deployment")
        self.program_id = program_id
        self.program = Pubkey.from_string(program_id)
        self.rpc = rpc or Rpc(rpc_url)

    def bounty_address(self, job):
        return str(
            Pubkey.find_program_address([b"bounty", b58decode(job["creator"]), job_key(job)], self.program)[0]
        )

    def submission_address(self, job, worker):
        return str(
            Pubkey.find_program_address(
                [b"submission", b58decode(self.bounty_address(job)), b58decode(worker)], self.program
            )[0]
        )

    def spec(self, action, job, sub=None):
        bounty = self.bounty_address(job)
        if action == "fund":
            payer = job["creator"]
            accounts = [(payer, True, True), (bounty, False, True), (SYSTEM, False, False)]
            data = create_data(job)
        elif action == "register" and sub:
            payer = sub["worker"]
            accounts = [
                (payer, True, True),
                (bounty, False, True),
                (self.submission_address(job, payer), False, True),
                (SYSTEM, False, False),
            ]
            data = registration_data(sub)
        elif action == "settle" and sub:
            payer = job["policy"]["validator"]
            if payer == sub["worker"]:
                raise ValueError("The named validator cannot be its own payout recipient")
            accounts = [
                (payer, True, True),
                (bounty, False, True),
                (sub["worker"], False, True),
                (self.submission_address(job, sub["worker"]), False, False),
            ]
            data = settlement_data(sub, sub["receipt_sha256"])
        elif action == "refund":
            payer = job["creator"]
            accounts = [(payer, True, True), (bounty, False, True)]
            data = b"\x03"
        else:
            raise ValueError("Unsupported chain action or missing submission")
        return {"payer": payer, "program": self.program_id, "accounts": accounts, "data": data}

    @staticmethod
    def instruction(spec):
        return Instruction(
            Pubkey.from_string(spec["program"]),
            spec["data"],
            [
                AccountMeta(Pubkey.from_string(address), signer, writable)
                for address, signer, writable in spec["accounts"]
            ],
        )

    def unsigned(self, spec, blockhash):
        message = Message.new_with_blockhash(
            [self.instruction(spec)], Pubkey.from_string(spec["payer"]), Hash.from_string(blockhash)
        )
        return Transaction.new_unsigned(message)

    def validate_unsigned(self, raw, spec):
        """Local worker refuses to blindly sign bytes supplied by a server."""
        tx = Transaction.from_bytes(raw)
        expected = self.unsigned(spec, str(tx.message.recent_blockhash))
        if bytes(tx) != bytes(expected):
            raise ValueError("Transaction differs from the locally reconstructed instruction intent")
        return tx

    def validate_signed(self, raw, spec):
        """Authenticate wallet-signed bytes and reject every non-intended instruction/account."""
        try:
            if not 100 <= len(raw) <= 1232:
                raise ValueError("Invalid Solana transaction size")
            tx = Transaction.from_bytes(raw)
            expected = self.unsigned(spec, str(tx.message.recent_blockhash))
            if bytes(tx.message) != bytes(expected.message) or len(tx.signatures) != 1:
                raise ValueError("Signed transaction differs from the exact intended message")
            tx.verify()
            if bytes(tx) != raw:
                raise ValueError("Noncanonical transaction encoding")
            return {"signature": str(tx.signatures[0]), "transaction_base64": base64.b64encode(raw).decode()}
        except Exception as exc:
            raise ValueError("Invalid signed transaction or instruction intent") from exc

    def broadcast_wallet(self, raw, spec):
        self.deployment()
        pending = self.validate_signed(raw, spec)
        signature = self.rpc.call(
            "sendTransaction",
            [
                pending["transaction_base64"],
                {
                    "encoding": "base64",
                    "skipPreflight": False,
                    "preflightCommitment": "finalized",
                    "maxRetries": 3,
                },
            ],
        )
        if signature != pending["signature"]:
            raise ValueError("RPC returned a different transaction signature")
        return {"signature": signature, "finalized": False, "instruction_checked": True}

    def deployment(self):
        genesis = self.rpc.require_devnet()
        account = self.rpc.account(self.program_id)
        if not account or not account.get("executable"):
            raise ValueError("Configured GradientMine program is not executable on this Devnet RPC")
        return {"genesis": genesis, "program_id": self.program_id, "executable": True}

    def verify_program(self, program_bytes):
        """Compare a built ELF with finalized deployed bytes and record upgrade trust.

        Upgradeable program allocations may contain zero padding after the ELF.
        Never strip the ELF's own trailing zero bytes before hashing it.
        """
        if not isinstance(program_bytes, bytes) or not program_bytes.startswith(b"\x7fELF"):
            raise ValueError("Expected the exact compiled SBF ELF bytes")
        if not 4 <= len(program_bytes) <= 10_000_000:
            raise ValueError("Unsupported SBF binary size")
        genesis = self.rpc.require_devnet()
        account = self.rpc.account(self.program_id)
        if not account or account.get("executable") is not True:
            raise ValueError("Configured program is not executable on finalized Devnet")
        upgradeable = "BPFLoaderUpgradeab1e11111111111111111111111"
        legacy = {"BPFLoader1111111111111111111111111111111111", "BPFLoader2111111111111111111111111111111111"}
        result = {"genesis": genesis, "program_id": self.program_id, "executable": True,
                  "loader": account.get("owner"), "programdata_address": None,
                  "deployment_slot": None, "upgrade_authority": None}
        try:
            if account["data"][1] != "base64":
                raise ValueError("Unsupported program account encoding")
            raw = base64.b64decode(account["data"][0], validate=True)
            if account.get("owner") == upgradeable:
                if len(raw) != 36 or struct.unpack_from("<I", raw)[0] != 2:
                    raise ValueError("Unrecognized upgradeable program state")
                address = b58encode(raw[4:36])
                stored = self.rpc.account(address)
                if not stored or stored.get("owner") != upgradeable or stored.get("executable") is not False:
                    raise ValueError("ProgramData is absent or owned by the wrong loader")
                if stored["data"][1] != "base64":
                    raise ValueError("Unsupported ProgramData encoding")
                raw = base64.b64decode(stored["data"][0], validate=True)
                if len(raw) < 45 or struct.unpack_from("<I", raw)[0] != 3 or raw[12] not in (0, 1):
                    raise ValueError("Unrecognized ProgramData state")
                result.update(programdata_address=address, deployment_slot=struct.unpack_from("<Q", raw, 4)[0],
                              upgrade_authority=b58encode(raw[13:45]) if raw[12] else None)
                raw = raw[45:]
            elif account.get("owner") not in legacy:
                raise ValueError("Unsupported program loader; exact binary verification unavailable")
            if raw[:len(program_bytes)] != program_bytes or any(raw[len(program_bytes):]):
                raise ValueError("Deployed program differs from the exact built ELF")
        except (KeyError, IndexError, TypeError, struct.error) as exc:
            raise ValueError("Malformed deployed program evidence") from exc
        result.update(program_sha256=digest(program_bytes), program_size_bytes=len(program_bytes),
                      upgrade_trust="Upgrade authority can replace the program" if result["upgrade_authority"]
                      else "No upgrade authority reported by this loader")
        return result

    def intent(self, action, job, sub=None):
        self.deployment()
        spec = self.spec(action, job, sub)
        block = self.rpc.call("getLatestBlockhash", [{"commitment": "finalized"}])["value"]
        tx = self.unsigned(spec, block["blockhash"])
        fee = self.rpc.call(
            "getFeeForMessage", [base64.b64encode(bytes(tx.message)).decode(), {"commitment": "finalized"}]
        )["value"]
        if type(fee) is not int or not 0 <= fee <= 100000:
            raise ValueError("RPC could not quote a supported fee; refusing transaction")
        rent = 0
        if action in {"fund", "register"}:
            rent = self.rpc.call(
                "getMinimumBalanceForRentExemption", [BOUNTY_SIZE if action == "fund" else SUBMISSION_SIZE]
            )
        return {
            "action": action,
            "chain": "solana:devnet",
            "program_id": self.program_id,
            "transaction_base64": base64.b64encode(bytes(tx)).decode(),
            "last_valid_block_height": block["lastValidBlockHeight"],
            "payer": spec["payer"],
            "accounts": [{"address": a, "signer": s, "writable": w} for a, s, w in spec["accounts"]],
            "instruction_base64": base64.b64encode(spec["data"]).decode(),
            "fee_lamports": fee,
            "rent_lamports": rent,
            "reward_lamports": job["policy"]["reward_lamports"] if action == "fund" else 0,
            "warning": "Devnet SOL has no monetary value. Rent stays in protocol accounts; no rent-close instruction yet.",
        }

    def sign_intent(self, intent, action, job, sub, identity):
        self.rpc.require_devnet()
        spec = self.spec(action, job, sub)
        if identity.address != spec["payer"] or intent["chain"] != "solana:devnet":
            raise ValueError("Wrong signing identity or chain")
        tx = self.validate_unsigned(base64.b64decode(intent["transaction_base64"], validate=True), spec)
        tx.sign([Keypair.from_bytes(identity.solana_bytes())], tx.message.recent_blockhash)
        return {
            "signature": str(tx.signatures[0]),
            "transaction_base64": base64.b64encode(bytes(tx)).decode(),
            "last_valid_block_height": intent["last_valid_block_height"],
        }

    def signed_settlement(self, job, sub, identity):
        return self.sign_intent(self.intent("settle", job, sub), "settle", job, sub, identity)

    def send_signed(self, pending):
        self.rpc.require_devnet()
        # Re-sending these identical signed bytes is idempotent on Solana.
        status = self.rpc.call(
            "getSignatureStatuses", [[pending["signature"]], {"searchTransactionHistory": True}]
        )["value"][0]
        if status:
            if status.get("err") is not None:
                raise ValueError(
                    "Previously submitted transaction failed. Inspect evidence before preparing a new attempt."
                )
            return pending["signature"]
        height = self.rpc.call("getBlockHeight", [{"commitment": "finalized"}])
        if height > pending["last_valid_block_height"]:
            raise ValueError(
                "Signed transaction expired before confirmation. Use the documented settlement recovery command; never assume payment."
            )
        result = self.rpc.call(
            "sendTransaction",
            [
                pending["transaction_base64"],
                {
                    "encoding": "base64",
                    "skipPreflight": False,
                    "preflightCommitment": "finalized",
                    "maxRetries": 3,
                },
            ],
        )
        if result != pending["signature"]:
            raise ValueError("RPC returned a different transaction signature")
        return result

    def read_bounty(self, job):
        account = self.rpc.account(self.bounty_address(job))
        if not account or account["owner"] != self.program_id:
            raise ValueError("Bounty account is absent or owned by a different program")
        data = decode_bounty(base64.b64decode(account["data"][0], validate=True))
        expected = {
            "creator": job["creator"],
            "validator": job["policy"]["validator"],
            "job_key": job_key(job).hex(),
            "policy_sha256": job["policy_sha256"],
            "deadline": job["policy"]["deadline"],
            "refund_after": job["policy"]["refund_after"],
            "reward_lamports": job["policy"]["reward_lamports"],
        }
        if any(data[k] != v for k, v in expected.items()):
            raise ValueError("On-chain bounty terms differ from the committed off-chain policy")
        return data, account

    def confirm(self, action, job, sub, signature):
        self.deployment()
        spec = self.spec(action, job, sub)
        evidence = self.rpc.transaction(signature, spec)
        bounty, account = self.read_bounty(job)
        if action == "fund":
            if bounty["state"] != 0:
                raise ValueError("Escrow is already terminal; cannot mark it open")
            rent = self.rpc.call("getMinimumBalanceForRentExemption", [BOUNTY_SIZE])
            if account["lamports"] < rent + job["policy"]["reward_lamports"]:
                raise ValueError("Escrow account does not hold the complete reward and rent")
        elif action == "register":
            registered = self.rpc.account(self.submission_address(job, sub["worker"]))
            if not registered or registered["owner"] != self.program_id:
                raise ValueError("No program-owned submission account")
            record = decode_submission(base64.b64decode(registered["data"][0], validate=True))
            for key, expected in [
                ("bounty", self.bounty_address(job)),
                ("worker", sub["worker"]),
                ("artifact_sha256", sub["artifact_sha256"]),
                ("manifest_sha256", sub["manifest_sha256"]),
            ]:
                if record[key] != expected:
                    raise ValueError("Registered submission commitment mismatch")
            if record["registered_at"] >= job["policy"]["deadline"]:
                raise ValueError("Submission was not registered before the deadline")
        elif action in {"settle", "refund"}:
            recipient = sub["worker"] if action == "settle" else job["creator"]
            if bounty["state"] != (1 if action == "settle" else 2):
                raise ValueError("The escrow does not show the expected terminal state")
            if action == "settle" and (
                bounty["winner"] != recipient or bounty["receipt_sha256"] != sub["receipt_sha256"]
            ):
                raise ValueError("Winning recipient or receipt differs from the intended settlement")
            keys = evidence["transaction"]["message"]["accountKeys"]
            index = keys.index(recipient)
            received = evidence["meta"]["postBalances"][index] - evidence["meta"]["preBalances"][index]
            expected = job["policy"]["reward_lamports"] - (
                evidence["meta"]["fee"] if recipient == spec["payer"] else 0
            )
            if received != expected:
                raise ValueError(
                    "Finalized transaction balance changes do not show the exact expected payout"
                )
        return {
            "signature": signature,
            "bounty_address": self.bounty_address(job),
            "explorer": f"https://explorer.solana.com/tx/{signature}?cluster=devnet",
            "state": bounty["state"],
        }

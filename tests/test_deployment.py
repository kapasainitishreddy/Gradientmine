import base64
import struct

import pytest
from solders.keypair import Keypair

from gradientmine.chain import Chain
from gradientmine.crypto import b58decode, digest
from gradientmine.wire import DEVNET_GENESIS


UPGRADEABLE = "BPFLoaderUpgradeab1e11111111111111111111111"


def deployed_program(*, authority=True):
    program, programdata, owner = [str(Keypair().pubkey()) for _ in range(3)]
    binary = b"\x7fELF" + b"compiled-program\x00\x00"
    metadata = struct.pack("<IQB", 3, 42, int(authority))
    metadata += b58decode(owner) if authority else bytes(32)
    accounts = {
        program: {"executable": True, "owner": UPGRADEABLE,
                  "data": [base64.b64encode(struct.pack("<I", 2) + b58decode(programdata)).decode(), "base64"]},
        programdata: {"executable": False, "owner": UPGRADEABLE,
                      "data": [base64.b64encode(metadata + binary + bytes(100)).decode(), "base64"]},
    }

    class Rpc:
        def require_devnet(self):
            return DEVNET_GENESIS

        def account(self, address):
            return accounts.get(str(address))

    return Chain(program, rpc=Rpc()), binary, accounts, programdata, owner


@pytest.mark.parametrize("authority", [True, False])
def test_verifies_exact_deployed_binary_and_upgrade_authority(authority):
    chain, binary, _, programdata, owner = deployed_program(authority=authority)
    result = chain.verify_program(binary)
    assert result["program_sha256"] == digest(binary)
    assert result["programdata_address"] == programdata
    assert result["deployment_slot"] == 42
    assert result["upgrade_authority"] == (owner if authority else None)
    assert result["program_id"] == chain.program_id
    assert result["genesis"] == DEVNET_GENESIS


@pytest.mark.parametrize("attack", ["binary", "padding", "owner", "programdata-owner", "tag", "authority-tag", "executable"])
def test_rejects_unverified_deployed_program(attack):
    chain, binary, accounts, programdata, _ = deployed_program()
    if attack == "binary":
        binary = binary[:-1] + b"different"
    elif attack == "padding":
        raw = base64.b64decode(accounts[programdata]["data"][0]) + b"unexpected"
        accounts[programdata]["data"][0] = base64.b64encode(raw).decode()
    elif attack == "owner":
        accounts[chain.program_id]["owner"] = str(Keypair().pubkey())
    elif attack == "programdata-owner":
        accounts[programdata]["owner"] = str(Keypair().pubkey())
    elif attack == "tag":
        raw = b"\x01\0\0\0" + base64.b64decode(accounts[chain.program_id]["data"][0])[4:]
        accounts[chain.program_id]["data"][0] = base64.b64encode(raw).decode()
    elif attack == "authority-tag":
        raw = bytearray(base64.b64decode(accounts[programdata]["data"][0]))
        raw[12] = 2
        accounts[programdata]["data"][0] = base64.b64encode(raw).decode()
    elif attack == "executable":
        accounts[chain.program_id]["executable"] = "true"
    with pytest.raises(ValueError):
        chain.verify_program(binary)

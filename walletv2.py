import json
from pathlib import Path

from typing import Any, Dict, Optional, Tuple

from tinyec.ec import SubGroup, Curve

from Crypto.Random.random import randint

from web3 import Web3


p = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F", 16)
n = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)
h = (p, n)

x = int("79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798", 16)
y = int("483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8", 16)
g = (x, y)

field = SubGroup(p, g, n, h)
curve = Curve(a=0, b=7, field=field, name="secp256k1")


class Wallet:
    def __init__(self) -> None:
        self.private_key = None  # type: Optional[int]
        self.public_key = None  # type: Any
        self.retreive_keys()
        self.address = self.retreive_address()

    def retreive_keys(self) -> Optional[Dict]:
        if self.private_key and self.public_key:
            print("Keys already exist")
            return {"private_key": self.private_key, "public_key": self.public_key}

        try:
            path = Path("wallet")
            path.mkdir(exist_ok=True)
            with open(path / ".keys", mode="r") as f:
                keys = json.load(f)
                private_key = keys["private_key"]
                public_key = private_key * curve.g
                self.private_key = private_key
                self.public_key = public_key
                return {"private_key": private_key, "public_key": public_key}
        except (IOError, IndexError):
            print("Loading wallet failed...")
        return None

    @staticmethod
    def save_keys(private_key: str) -> None:
        output = {"private_key": private_key}

        try:
            path = Path("wallet")
            path.mkdir(exist_ok=True)
            with open(path / ".keys", mode="w") as f:
                json.dump(output, f)
        except (IOError, IndexError):
            print("Saving keys failed...")

    def generate_keys(self) -> Tuple[int, Any]:
        if self.private_key and self.public_key:
            print(
                "Keys already exist. Not generating new ones and returning existing ones."
            )
            return self.private_key, self.public_key

        private_key = randint(1, n)
        public_key = private_key * curve.g
        self.private_key = private_key
        self.public_key = public_key
        return private_key, public_key

    def retreive_address(self) -> Optional[str]:
        try:
            path = Path("wallet")
            path.mkdir(exist_ok=True)
            with open(path / ".address", mode="r") as f:
                address = json.load(f)
                self.address = address["address"]
                return address
        except (IOError, IndexError):
            print("Retreiving address failed...")
        return None

    @staticmethod
    def save_address(address: str) -> None:
        output = {"address": address}
        try:
            path = Path("wallet")
            path.mkdir(exist_ok=True)
            with open(path / ".address", mode="w") as f:
                json.dump(output, f)
        except (IOError, IndexError):
            print("Saving address failed...")

    def generate_address(self) -> str:
        if self.address:
            print("Address already created. Returning existing address.")
            return self.address
        public_key_hex = (
            Web3.toHex(self.public_key.x)[2:] + Web3.toHex(self.public_key.y)[2:]  # type: ignore
        )
        address = Web3.keccak(hexstr=public_key_hex).hex()
        address = "0x" + address[-40:]
        address = Web3.toChecksumAddress(address)
        address = "MNRCoin" + address[2:]
        self.address = address
        return address

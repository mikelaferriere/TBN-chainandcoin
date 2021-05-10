"""

https://hackernoon.com/how-to-build-a-minimalistic-ethereum-wallet-in-python-part-1-rr4j32dp
"""
import logging

from tinyec.ec import SubGroup, Curve
from Crypto.Random.random import randint
from web3 import Web3

from typing import Optional

from transaction import Transaction

logger = logging.getLogger(__name__)


class Wallet:
    def __init__(self, test: bool = False) -> None:
        pHex = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F"
        nHex = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141"
        aHex = "0000000000000000000000000000000000000000000000000000000000000000"
        bHex = "0000000000000000000000000000000000000000000000000000000000000007"
        xHex = "79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798"
        yHex = "483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8"

        a = int(aHex, 16)
        b = int(bHex, 16)

        p = int(pHex, 16)
        self.n = int(nHex, 16)
        h = 1

        x = int(xHex, 16)
        y = int(yHex, 16)
        g = (x, y)

        # Assert that the (x, y) lies on the curve
        assert (y**2 % p == (x**3 + 7) % p)

        field = SubGroup(p, g, self.n, h)
        self.curve = Curve(a = a, b = b, field = field, name = 'secp256k1')

        self.private_key = None
        self.public_key = None
        self.address = None
        self.logged_in = False


    def init(self, private_key: Optional[int] = None) -> None:
        if not private_key:
            self.generate_private_key()
            self.generate_public_key()
            self.generate_address()
        else:
            self.private_key = private_key
            self.generate_public_key()
            self.generate_address()

    def generate_private_key(self) -> None:
        self.private_key = randint(1, self.n)

    def generate_public_key(self) -> str:
        public_key = self.private_key * self.curve.g
        self.public_key = public_key
        return public_key

    def generate_address(self) -> str:
        # Remove the `0x` from the from of the x and y hex values
        public_key_hex = Web3.toHex(self.public_key.x)[2:] + Web3.toHex(self.public_key.y)[2:]
        address = Web3.keccak(hexstr = public_key_hex).hex()
        print(address)
        address = address[-40:]
        address = Web3.toChecksumAddress(address)[2:]
        self.address = address
        return address

    def sign_transaction(self, sender: str, recipient: str, amount: float) -> str:
        """
        Sign a transaction and return the signature
        A signature is generated using the contents of the rest of the transaction. This means
        that the signature will always be able to be decoded and will match the transaction.
        """
        logger.info("Signing transaction")
        if self.private_key is None:
            message = "Unable to sign transaction without a private key"
            logger.error(message)
            raise ValueError(message)
        #
        # Add signing functionality
        #

        logger.debug("Transaction signed successfully")
        return ""

    @staticmethod
    def verify_transaction(transaction: Transaction) -> bool:
        """
        Verify signature of transaction. A transaction's signature must always be able to be
        verified because the contents of the transaction can never change. Any change in the
        transaction, will be a sign of nefarious actions.
        """
        logger.info("Verifying transaction")
        msg = f"{str(transaction.sender)}{str(transaction.recipient)}{str(transaction.amount)}"
        try:
            if transaction.signature is None:
                raise ValueError("Transaction signature is None")
            #
            # Add verify functionality
            #
            return False
        except (ValueError, TypeError) as e:
            logger.exception(e)
            return False

if __name__ == "__main__":
    w = Wallet()
    w.init()

    print("Private key:\n", w.private_key)
    print("Public key:\n", w.public_key)
    print("Address:\n", w.address)

    
    t = Transaction(
        sender=w.address,
        recipient="test",
        nonce=1,
        amount=0.5
    )
    t.signature = w.sign_transaction(w.address, "test", 0.5)

    result = w.verify_transaction(t)
    print(result)

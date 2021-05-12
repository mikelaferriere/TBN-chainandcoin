"""
https://pypi.org/project/ecdsa/
NOTE 1: There still needs to be some work with respect to securty, but this at least
        doesn't use ssh RSA, which is deprecated
NOTE 2: This library does not protect against side-channel attacks
"""
import logging
import hashlib
import json

from pathlib import Path
from typing import Any, Optional

from Crypto.Hash import keccak
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

import ecdsa

from generated.transaction_pb2 import Transaction

logger = logging.getLogger(__name__)


class Wallet:
    def __init__(self, test: bool = False) -> None:
        self.private_key = None  # type: Optional[ecdsa.SigningKey]
        self.public_key = None  # type: Optional[bytes]
        self.address = None  # type: Optional[str]
        self.nonce = 0
        self.logged_in = False

        if test:
            self.create_login("test", save=False)

    def set_is_logged_in(self) -> bool:
        """
        If the public and private keys have been generated, or unlocked via a password login,
        then the wallet is logged in.
        """
        logged_in = self.public_key is not None and self.private_key is not None
        message = "Successfully logged in" if logged_in else "Failed to login"
        logger.debug(message)
        self.logged_in = logged_in

        return logged_in

    def create_login(  # pylint: disable=too-many-locals
        self, passphrase: str, save: bool = True
    ) -> bool:
        """
        Initialize the wallet by generating new keys using the provided passphrase.
        Then save the keys locally so they can be recovered using the passphrase after the
        wallet is logout or closed.

        The wallet address is also set here. For now, the address is the same value as the
        public key.
        """

        salt_ = get_random_bytes(16)
        key = scrypt(passphrase, salt_, 32, N=2 ** 20, r=8, p=1)  # type: ignore

        try:
            self.__generate_keys()
            if not self.private_key:
                raise ValueError("Private key must exist after generating keys")
            private_key = self.private_key.to_string().hex()
            data = str(private_key).encode("utf-8")
            cipher = AES.new(key, AES.MODE_CBC)  # type: ignore
            ct_bytes = cipher.encrypt(pad(data, AES.block_size))

            salt = salt_.hex()  # type: ignore
            iv = cipher.iv.hex()  # type: ignore
            ct = ct_bytes.hex()

            output = {
                "salt": salt,
                "initialization_vector": iv,
                "encrypted_private_key": ct,
            }

            if save:
                path = Path("wallet")
                path.mkdir(exist_ok=True)
                with open(path / ".keys", mode="w") as f:
                    json.dump(output, f)
        except (IOError, IndexError):
            logger.error("Creating login for wallet failed...")
        except ValueError as e:
            logger.exception(e)

        address = self.generate_address()
        if save:
            Wallet.save_address(address)
        self.set_is_logged_in()
        return self.logged_in

    def login(self, passphrase: str) -> bool:
        """
        Using the passphrase provided, grab the private key from the saved location and
        attempt to decrypt it.

        If the key is decrypted, the public key is regenerated and both keys are saved in memory

        The wallet address is also retrieved from the local save.
        """
        if self.logged_in:
            logger.debug("Already logged in. No need to log in again")
            return True

        try:
            path = Path("wallet")
            path.mkdir(exist_ok=True)
            with open(path / ".keys", mode="r") as f:
                data = json.load(f)
                salt = data["salt"]
                iv = data["initialization_vector"]
                ct = data["encrypted_private_key"]

                salt = bytes.fromhex(salt)
                iv = bytes.fromhex(iv)
                ct = bytes.fromhex(ct)

                key = scrypt(passphrase, salt, 32, N=2 ** 20, r=8, p=1)  # type: ignore

                cipher = AES.new(key, AES.MODE_CBC, iv)  # type: ignore
                pt = bytes.fromhex(  # type: ignore
                    unpad(cipher.decrypt(ct), AES.block_size).decode("utf-8")
                )

                self.private_key = ecdsa.SigningKey.from_string(
                    pt,
                    curve=ecdsa.SECP256k1,
                    hashfunc=hashlib.sha256,  # the default is sha1
                )

            if not self.private_key:
                raise FileNotFoundError("Tried to login, but no key was found")
            vk = self.private_key.verifying_key
            public_key = vk.to_string()
            self.public_key = public_key
        except FileNotFoundError as e:
            logger.error(e)
            self.public_key = None
            self.private_key = None
        except (IOError, IndexError):
            logger.error("Retrieving keys from wallet failed...")
            self.public_key = None
            self.private_key = None
        except ValueError:
            logger.warning("Invalid Password. Try Again")
            self.public_key = None
            self.private_key = None

        self.set_is_logged_in()
        self.address = Wallet.load_address()
        return self.logged_in

    def __generate_keys(self) -> None:
        #
        # private key generation
        # curve secp256k1 is used in bitcoin and eth
        # the default is sha1, but we want to use sha256
        #

        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1, hashfunc=hashlib.sha256)
        self.private_key = sk

        #
        # public key generation
        #

        vk = sk.verifying_key
        public_key = vk.to_string()
        self.public_key = public_key

    def generate_address(self) -> str:
        if not self.public_key:
            raise ValueError("Public key must exist in order to generate an address")
        k = keccak.new(digest_bits=256)
        k.update(self.public_key)
        addr = k.digest()[-20:]
        address = "0x" + addr.hex()
        self.address = address
        return address

    @staticmethod
    def load_address() -> Optional[str]:
        """
        Retreive the address from the local saved location
        """
        path = Path("wallet")
        path.mkdir(exist_ok=True)
        path = path / ".address"
        logger.debug("Retreiving address from %s", path)

        try:
            with open(path, mode="r") as f:
                address = f.read()
                logger.debug("Address retreived")
                return address
        except (IOError, IndexError):
            logger.error("Retreiving address failed...")
        return None

    @staticmethod
    def save_address(address: str) -> None:
        """
        Save a given address to the local saved location
        """
        path = Path("wallet")
        path.mkdir(exist_ok=True)
        path = path / ".address"
        logger.debug("Saving address to %s", path)
        try:
            with open(path, mode="w") as f:
                f.write(address)
            logger.debug("Address saved")
        except (IOError, IndexError):
            logger.error("Saving address failed...")

    def sign_transaction(self, transaction: Any) -> str:
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

        tx = transaction.SerializeToString()
        signature = self.private_key.sign(tx)

        logger.debug("Transaction signed successfully")
        return signature.hex()

    @staticmethod
    def verify_transaction(tx: Any) -> bool:
        """
        Verify signature of transaction. A transaction's signature must always be able to be
        verified because the contents of the transaction can never change. Any change in the
        transaction, will be a sign of nefarious actions.
        """
        logger.info("Verifying transaction")
        try:
            message = Transaction(
                sender=tx.sender,
                recipient=tx.recipient,
                nonce=tx.nonce,
                amount=tx.amount,
                public_key=tx.public_key,
            ).SerializeToString()

            signature = bytes.fromhex(tx.signature)

            vk = ecdsa.VerifyingKey.from_string(
                bytes.fromhex(tx.public_key),
                curve=ecdsa.SECP256k1,
                hashfunc=hashlib.sha256,  # the default is sha1
            )
            result = vk.verify(signature, message)  # True

            return result
        except (ValueError, TypeError) as e:
            logger.exception(e)
            return False


# if __name__ == "__main__":
#     w = Wallet()
#     w.login("test")


#     t = Transaction(
#         sender=w.address,
#         recipient="test",
#         nonce=0,
#         amount=0.5,
#         public_key=w.public_key.hex()
#     )

#     t.signature = w.sign_transaction(t)
#     tx_hash = t.SerializeToString().hex()

#     result = w.verify_transaction(tx_hash)
#     print(result)

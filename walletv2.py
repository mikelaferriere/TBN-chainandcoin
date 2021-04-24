import binascii
from pathlib import Path

from typing import Optional

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from transaction import Transaction


class Wallet:
    def __init__(self, test: bool = False) -> None:
        self.public_key = None  # type: Optional[str]
        self.private_key = None  # type: RSA.RsaKey
        self.logged_in = False
        self.address = None  # type: Optional[str]
        if test:
            self.__generate_keys("test")
            self.private_key = RSA.import_key(self.private_key, passphrase="test")
            self.address = self.public_key
            self.set_is_logged_in()

    def set_is_logged_in(self) -> None:
        self.logged_in = self.public_key is not None and self.private_key is not None

    def __generate_keys(self, passphrase: str) -> None:
        key = RSA.generate(2048)
        encrypted_key = key.export_key(
            passphrase=passphrase,
            pkcs=8,
            protection="scryptAndAES128-CBC",
            format="DER",
        )

        self.private_key = encrypted_key
        self.public_key = binascii.hexlify(
            key.public_key().export_key(format="DER")
        ).decode("ascii")

    def create_login(self, passphrase: str) -> bool:
        try:
            self.__generate_keys(passphrase)

            path = Path("wallet")
            path.mkdir(exist_ok=True)
            with open(path / ".keys", mode="wb") as f:
                f.write(self.private_key)
                self.private_key = RSA.import_key(
                    self.private_key, passphrase=passphrase
                )
        except (IOError, IndexError):
            print("Creating login for wallet failed...")

        address = self.generate_address()
        self.save_address(address)
        self.set_is_logged_in()
        return self.logged_in

    def login(self, passphrase: str) -> bool:
        try:
            path = Path("wallet")
            path.mkdir(exist_ok=True)
            with open(path / ".keys", mode="rb") as f:
                encrypted_key = RSA.import_key(f.read(), passphrase=passphrase)
                self.private_key = encrypted_key
                self.public_key = binascii.hexlify(
                    encrypted_key.public_key().export_key(format="DER")
                ).decode("ascii")
        except (IOError, IndexError):
            print("Retreiving keys from wallet failed...")
        except ValueError:
            print("Invalid Password. Try Again")

        self.set_is_logged_in()
        self.retreive_address()
        return self.logged_in

    def retreive_address(self) -> Optional[str]:
        try:
            path = Path("wallet")
            path.mkdir(exist_ok=True)
            with open(path / ".address", mode="r") as f:
                self.address = f.read()
                return self.address
        except (IOError, IndexError):
            print("Retreiving address failed...")
        return None

    @staticmethod
    def save_address(address: str) -> None:
        try:
            path = Path("wallet")
            path.mkdir(exist_ok=True)
            with open(path / ".address", mode="w") as f:
                f.write(address)
        except (IOError, IndexError):
            print("Saving address failed...")

    def generate_address(self) -> str:
        if not self.public_key:
            raise ValueError(
                "Not able to create an address if no public key has been configured"
            )
        self.address = self.public_key
        return self.address

    # Sign a transaction and return the signature
    # RSA is a cryptography algorithm
    # binascii.hexlify is used to convert binary data to hexadecimal representation
    def sign_transaction(self, sender: str, recipient: str, amount: float) -> str:
        print("Signing transaction")
        signer = pkcs1_15.new(self.private_key)
        h = SHA256.new((str(sender) + str(recipient) + str(amount)).encode("utf8"))
        signature = signer.sign(h)
        return binascii.hexlify(signature).decode("ascii")

    # Verify signature of transaction
    @staticmethod
    def verify_transaction(transaction: Transaction) -> bool:
        print("Verifying transaction")
        verifier = pkcs1_15.new(RSA.importKey(binascii.unhexlify(transaction.sender)))
        h = SHA256.new(
            (
                str(transaction.sender)
                + str(transaction.recipient)
                + str(transaction.amount)
            ).encode("utf8")
        )
        try:
            if transaction.signature is None:
                raise ValueError("Transaction signature is None")
            verifier.verify(h, binascii.unhexlify(transaction.signature))
            return True
        except (ValueError, TypeError) as e:
            print(e)
            return False

import logging
import binascii
from pathlib import Path

from typing import Any, Optional

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

logger = logging.getLogger(__name__)


class Wallet:
    """
    A Crypto wallet implementation class. The wallet is capable of generating a set of
    private and public keys, as well as a wallet address. Currently, the address is
    just the public key. The address is used for creating transactions on the blockchain.
    """

    def __init__(self, test: bool = False) -> None:
        logger.debug("Initializing wallet")
        self.encrypted_private_key = None  # type: Optional[bytes]
        self.public_key = None  # type: Optional[str]
        self.private_key = None  # type: Optional[RSA.RsaKey]
        self.logged_in = False
        self.address = None  # type: Optional[str]
        self.nonce = 0

        if test:
            logger.debug("Initializing TEST wallet")
            self.__generate_keys("test")
            if not self.encrypted_private_key:
                raise ValueError("Encrypted private key must exist")
            self.private_key = RSA.import_key(
                self.encrypted_private_key, passphrase="test"
            )
            self.address = self.public_key
            self.set_is_logged_in()

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

    def __generate_keys(self, passphrase: str) -> None:
        """
        Private function to generate RSA private and public keys using a provided passphrase.
        The keys are then converted to HEX, to be more human readable.
        """
        logger.debug("Generating new keys")
        key = RSA.generate(2048)
        encrypted_key = key.export_key(
            passphrase=passphrase,
            pkcs=8,
            protection="scryptAndAES128-CBC",
            format="DER",
        )

        self.encrypted_private_key = encrypted_key
        self.public_key = binascii.hexlify(
            key.public_key().export_key(format="DER")
        ).decode("ascii")
        logger.debug("Successfully generated new keys")

    def create_login(self, passphrase: str) -> bool:
        """
        Initialize the wallet by generating new keys using the provided passphrase.
        Then save the keys locally so they can be recovered using the passphrase after the
        wallet is logout or closed.

        The wallet address is also set here. For now, the address is the same value as the
        public key.
        """
        try:
            self.__generate_keys(passphrase)

            path = Path("wallet")
            path.mkdir(exist_ok=True)
            if not self.encrypted_private_key:
                raise ValueError("Encrypted private key must exist")
            with open(path / ".keys", mode="wb") as f:
                f.write(self.encrypted_private_key)
                self.private_key = RSA.import_key(
                    self.encrypted_private_key, passphrase=passphrase
                )
        except (IOError, IndexError):
            logger.error("Creating login for wallet failed...")
        except ValueError as e:
            logger.exception(e)

        address = self.generate_address()
        self.save_address(address)
        self.set_is_logged_in()
        return self.logged_in

    def login(self, passphrase: str) -> bool:
        """
        Using the passphrase provided, grab the private key from the saved location and
        attempt to decrypt it.

        If the key is decrypted, the public key is regenerated and both keys are saved in memory

        The wallet address is also retreived from the local save.
        """
        if self.logged_in:
            logger.debug("Already logged in. No need to log in again")
            return True
        try:
            path = Path("wallet")
            path.mkdir(exist_ok=True)
            with open(path / ".keys", mode="rb") as f:
                encrypted_key = f.read()
                self.encrypted_private_key = encrypted_key
                self.private_key = RSA.import_key(encrypted_key, passphrase=passphrase)
                self.public_key = binascii.hexlify(
                    self.private_key.public_key().export_key(format="DER")
                ).decode("ascii")
        except (IOError, IndexError):
            logger.error("Retreiving keys from wallet failed...")
            self.public_key = None
            self.private_key = None
        except ValueError:
            logger.warning("Invalid Password. Try Again")
            self.public_key = None
            self.private_key = None

        self.set_is_logged_in()
        self.retreive_address()
        return self.logged_in

    def retreive_address(self) -> Optional[str]:
        """
        Retreive the address from the local saved location
        """
        if self.address is not None:
            logger.debug("Wallet address already generated")
            return self.address

        path = Path("wallet")
        path.mkdir(exist_ok=True)
        path = path / ".address"
        logger.debug("Retreiving address from %s", path)

        try:
            with open(path, mode="r") as f:
                self.address = f.read()
                logger.debug("Address retreived")
                return self.address
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

    def generate_address(self) -> str:
        """
        Generate a random wallet address. Currently, this is a static value identical to the
        public key
        """
        logger.info("Generating wallet address")
        if not self.public_key:
            raise ValueError(
                "Not able to create an address if no public key has been configured"
            )
        self.address = self.public_key
        return self.address

    def sign_transaction(self, sender: str, recipient: str, amount: float) -> str:
        """
        Sign a transaction and return the signature
        A signature is generated using the contents of the rest of the transaction. This means
        that the signature will always be able to be decoded and will match the transaction.

        RSA is a cryptography algorithm
        binascii.hexlify is used to convert binary data to hexadecimal representation
        """
        logger.info("Signing transaction")
        if self.private_key is None:
            message = "Unable to sign transaction without a private key"
            logger.error(message)
            raise ValueError(message)
        signer = pkcs1_15.new(self.private_key)
        h = SHA256.new((str(sender) + str(recipient) + str(amount)).encode("utf8"))
        signature = signer.sign(h)
        hex_sig = binascii.hexlify(signature).decode("ascii")
        logger.debug("Transaction signed successfully")
        return hex_sig

    @staticmethod
    def verify_transaction(transaction: Any) -> bool:
        """
        Verify signature of transaction. A transaction's signature must always be able to be
        verified because the contents of the transaction can never change. Any change in the
        transaction, will be a sign of nefarious actions.
        """
        logger.info("Verifying transaction")
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
            logger.debug("Transaction verified")
            return True
        except (ValueError, TypeError) as e:
            logger.exception(e)
            return False

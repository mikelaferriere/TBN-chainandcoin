"""
https://pypi.org/project/ecdsa/

NOTE 1: There still needs to be some work with respect to securty, but this at least
        doesn't use ssh RSA, which is deprecated

NOTE 2: This library does not protect against side-channel attacks


"""
import logging
import random

import binascii
import ecdsa
import hashlib

from Crypto.Hash import keccak

from typing import Optional

from transaction import Transaction

logger = logging.getLogger(__name__)


class Wallet:
    def __init__(self, test: bool = False) -> None:
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
        # curve secp256k1 is used in bitcoin and eth
        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.generated_private_key = sk

        self.private_key = sk.to_string()
        self.private_key_hex = self.private_key.hex()

    def generate_public_key(self) -> str:
        vk = self.generated_private_key.verifying_key
        public_key = vk.to_string()
        self.public_key = public_key
        return public_key

    def generate_address(self) -> str:
        # keccak_hash = keccak.new(digest_bits=256)
        # pub=bytearray.fromhex(self.public_key.hex())
        # keccak_hash.update(bytes(pub))

        # address = keccak_hash.hexdigest()
        # address = address[-40:]
        # address = "0x" + address
        #self.address = address

        address = self.public_key.hex()
        self.address = address
        return address

    def sign_transaction(self, transaction: Transaction) -> str:
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

        print("Transaction", transaction)
        print()
        
        tx = transaction.generate_tx_hash()

        print("Transaction Hash", tx)
        print()
        
        signature = self.generated_private_key.sign(tx)

        print("Signature", signature)
        print()
        logger.debug("Transaction signed successfully")
        return signature

    @staticmethod
    def verify_transaction(tx_hash: str) -> bool:
        """
        Verify signature of transaction. A transaction's signature must always be able to be
        verified because the contents of the transaction can never change. Any change in the
        transaction, will be a sign of nefarious actions.
        """
        logger.info("Verifying transaction")
        try:
            #
            # Add verify functionality
            #

            message = tx_hash

            tx_byte_list = Transaction.unwrap_tx_hash(bytes.fromhex(tx_hash))

            print("Transaction unwrapped")
            print()
            for t in tx_byte_list:
                print(t)

            print()
            print("Fixed unwrapped transaction")
            nonce = tx_byte_list[0]
            sender = tx_byte_list[1]
            recipient = tx_byte_list[2]
            amount = tx_byte_list[3]
            public_key = bytes.fromhex(sender)
            signature = ""#tx_byte_list[5]
            
            message = tx_hash
            
            vk = ecdsa.VerifyingKey.from_string(
                public_key,
                curve=ecdsa.SECP256k1,
                hashfunc=hashlib.sha256
            ) # the default is sha1
            result = vk.verify(sig, message) # True
            print(result)

            return False

            # vk = ecdsa.VerifyingKey.from_string(
            #     bytes.fromhex(public_key),
            #     curve=ecdsa.SECP256k1,
            #     hashfunc=sha256 # the default is sha1
            # )
            # return vk.verify(bytes.fromhex(transaction.signature), msg)
        except (ValueError, TypeError) as e:
            logger.exception(e)
            return False

if __name__ == "__main__":
    w = Wallet()
    w.init()

    # print("Private key:\n", w.private_key)
    # print("Public key:\n", w.public_key)
    # print("Address:\n", w.address)

    
    t = Transaction(
        sender=w.address,
        recipient="test",
        nonce=0,
        amount=0.5,
    )

    t.signature = w.sign_transaction(t)

    print(t)
    print()
    tx_hash = t.generate_tx_hash()

    print("Raw transaction hash w/ Signature", tx_hash)

    tx_hash = tx_hash.hex()
    print("Transaction Hash w/ Signature", tx_hash)
    print()
    
    result = w.verify_transaction(tx_hash)
    print(result)

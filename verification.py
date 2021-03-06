import logging
import hashlib

from typing import Callable, List

from block import Block, Header

from transaction import SignedRawTransaction
from wallet import Wallet

logger = logging.getLogger(__name__)


class Verification:
    @staticmethod
    def hash_bytes_256(b: bytes) -> str:
        """
        Hash a byte array and convert it to a string
        """
        return hashlib.sha256(b).hexdigest()

    @staticmethod
    def hash_block_header(header: Header) -> str:
        """
        First, convert the block header to an byte array
        Then hash the block using SHA256
        """
        hashable_block_header = header.SerializeToString()
        return Verification.hash_bytes_256(hashable_block_header)

    @staticmethod
    def hash_transaction(transaction: SignedRawTransaction) -> str:
        """
        First, convert the transaction to byte array
        Then hash the transaction using SHA256
        """
        hashable_transaction = transaction.SerializeToString()
        return Verification.hash_bytes_256(hashable_transaction)

    @staticmethod
    def valid_nonce(header: Header) -> bool:
        """
        Validates the Nonce: Does the hash(nonce, block) contain <difficulty> leading zeros?
        :param header: <Header> Block header
        :return: <bool> True if correct, False if not
        """
        guess = (
            str(header.transaction_merkle_root)
            + str(header.previous_hash)
            + str(header.nonce)
            + str(header.version)
        ).encode()
        guess_hash = Verification.hash_bytes_256(guess)
        return guess_hash[: header.difficulty] == "0" * header.difficulty

    @staticmethod
    def proof_of_work(header: Header) -> Header:
        """
        Simple Proof of Work Algorithm
          - Find a number 'p' such that hash(pp') contains leading {difficulty} zeros,
            where p is the previous p'
          - p is the previous nonce, and p' is the new nonce

        Essentially what is happening here is:
         1. Grab the last block on the chain
         2. Hash the last block
         3. Starting with 0, and incrementing infinitely, find a SHA256 value for the
             - open transactions
             - previous hash
             - nonce (incrementing number starting from 0 used in the mining process)
            where the result of the hash contains the {difficulty} number of leading 0's.
            I.E. If the difficulty is 4, then a valid nonce will only be found when the SHA256
                 hash contains 4 leading 0's.
        :param difficulty: <int>
        :return: <int>
        """
        logger.info(
            "Mining block for %s version and %s difficulty",
            header.version,
            header.difficulty,
        )
        while not Verification.valid_nonce(header):
            header.nonce += 1

        return header

    @classmethod
    def verify_chain(cls, blockchain: List[Block]) -> bool:
        """
        Determine if a given blockchain is valid
        :param chain: List[Block] A Blockchain
        :return: <bool> True if valid, False if not
        """

        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            logger.debug(
                "Checking index %s previous hash with the block hash of index %s",
                index,
                index - 1,
            )

            computed_previous_hash = cls.hash_block_header(blockchain[index - 1].header)
            if block.header.previous_hash != computed_previous_hash:
                logger.error(
                    "Previous block hashed not equal to previous hash stored in current block"
                )
                return False

            logger.debug(
                "Checking the Block hash for index %s is correct with the nonce attached",
                index,
            )
            if not cls.valid_nonce(block.header):
                logger.error("Proof of work is invalid")
                return False
        logger.info("Chain is valid")
        return True

    @staticmethod
    def verify_transaction(
        transaction: SignedRawTransaction,
        get_balance: Callable,
        get_last_tx_nonce: Callable,
        check_funds: bool = True,
    ) -> bool:
        """
        Verifies the transaction.

        If check_funds is True, ensure that the sender has enough coin (based on the
        transactions on the chain). Also make sure that the signature is the expected
        signature for the given transaction.

        If check_funds is False, just check that the signature is the expected signature
        for the given transaction
        """
        if check_funds:
            logger.debug(
                "Checking the sender's balance can cover the amount being transferred"
            )
            sender_balance = get_balance(transaction.details.sender)
            if sender_balance >= transaction.details.amount:
                logger.info("Sender has enough coin to create this transaction")

        return Wallet.verify_transaction(transaction, get_last_tx_nonce)

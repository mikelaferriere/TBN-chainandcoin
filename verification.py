import logging
import hashlib
import json

from typing import Callable, List

from block import Block
from transaction import Transaction
from walletv2 import Wallet

logger = logging.getLogger(__name__)


def hash_bytes_256(b: bytes) -> str:
    """
    Hash a byte array and convert it to a string
    """
    return hashlib.sha256(b).hexdigest()


class Verification:
    @staticmethod
    def hash_block(block: Block) -> str:
        """
        First, convert the block to an OrderedDict dictionary
        Then hash the block using SHA256
        """
        hashable_block = block.to_ordered_dict()
        return hash_bytes_256(json.dumps(hashable_block, sort_keys=True).encode())

    @staticmethod
    def valid_proof(
        proof: int, transactions: List[Transaction], previous_hash: str, difficulty: int
    ) -> bool:
        """
        Validates the Proof: Does the hash(proof, block) contain <difficulty> leading zeros?
        :param proof: <int> Current Proof
        :param transactions: List<Transaction> List of transactions in the block
        :param previous_hash: <str> hash of the previous block
        :param difficulty: <int> Difficulty of the proof of work
        :return: <bool> True if correct, False if not
        """

        guess = (
            str([tx.to_ordered_dict() for tx in transactions])
            + str(previous_hash)
            + str(proof)
        ).encode()
        guess_hash = hash_bytes_256(guess)
        return guess_hash[:difficulty] == "0" * difficulty

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
            if block.previous_hash != cls.hash_block(blockchain[index - 1]):
                logger.error(
                    "Previous block hashed not equal to previous hash stored in current block"
                )
                return False
            # We know that a correct block always includes the mining transaction
            # as the last transaction in the block. We also did not create the inital proof
            # including the mining transaction, so we need to exclude it in order to get a
            # valid proof
            block_transactions_sans_mining = block.transactions[:-1]
            if not cls.valid_proof(
                block.proof, block_transactions_sans_mining, block.previous_hash, 4
            ):
                logger.error("Proof of work is invalid")
                return False
        return True

    @staticmethod
    def verify_transaction(
        transaction: Transaction, get_balance: Callable, check_funds: bool = True
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
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(
                transaction
            )
        return Wallet.verify_transaction(transaction)

    @classmethod
    def verify_transactions(
        cls, open_transactions: List[Transaction], get_balance: Callable
    ):
        """
        Verifies all open & unprocessed transactions without checking sender's balance
        """
        return all(
            cls.verify_transaction(tx, get_balance, False) for tx in open_transactions
        )

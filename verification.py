import logging
import hashlib

from typing import Any, Callable, List

from walletv3 import Wallet

logger = logging.getLogger(__name__)


def hash_bytes_256(b: bytes) -> str:
    """
    Hash a byte array and convert it to a string
    """
    return hashlib.sha256(b).hexdigest()


class Verification:
    @staticmethod
    def hash_block(block: Any) -> str:
        """
        First, convert the block to an OrderedDict dictionary
        Then hash the block using SHA256
        """
        hashable_block = block.SerializeToString()
        return hash_bytes_256(hashable_block)

    @staticmethod
    def valid_nonce(
        nonce: int, transactions: List[Any], previous_hash: str, difficulty: int
    ) -> bool:
        """
        Validates the Nonce: Does the hash(nonce, block) contain <difficulty> leading zeros?
        :param nonce: <int> Current Nonce
        :param transactions: List<Transaction> List of transactions in the block
        :param previous_hash: <str> hash of the previous block
        :param difficulty: <int> Difficulty of the proof of work
        :return: <bool> True if correct, False if not
        """
        guess = (str(transactions) + str(previous_hash) + str(nonce)).encode()
        guess_hash = hash_bytes_256(guess)
        return guess_hash[:difficulty] == "0" * difficulty

    @staticmethod
    def proof_of_work(
        last_block: Any, open_transactions: List[Any], difficulty: int
    ) -> int:
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
        previous_hash = Verification.hash_block(last_block)

        nonce = 0
        while not Verification.valid_nonce(
            nonce, open_transactions, previous_hash, difficulty
        ):
            nonce += 1

        return nonce

    @classmethod
    def verify_chain(cls, blockchain: List[Any]) -> bool:
        """
        Determine if a given blockchain is valid
        :param chain: List[Block] A Blockchain
        :return: <bool> True if valid, False if not
        """

        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            logger.debug(
                "Checking index %s's previous hash with the block hash of index %s",
                index,
                index - 1,
            )
            if block.previous_hash != cls.hash_block(blockchain[index - 1]):
                logger.error(
                    "Previous block hashed not equal to previous hash stored in current block"
                )
                return False
            # We know that a correct block always includes the mining transaction
            # as the last transaction in the block. We also did not create the inital nonce
            # including the mining transaction, so we need to exclude it in order to get a
            # valid nonce
            block_transactions_sans_mining = block.transactions[:-1]

            logger.debug(
                "Checking the Block hash for index %s is correct with the nonce attached",
                index,
            )
            if not cls.valid_nonce(
                block.nonce, block_transactions_sans_mining, block.previous_hash, 4
            ):
                logger.error("Proof of work is invalid")
                return False
        logger.info("Chain is valid")
        return True

    @staticmethod
    def verify_transaction(
        transaction: Any, get_balance: Callable, check_funds: bool = True
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
            sender_balance = get_balance(transaction.sender)
            logger.info("Sender's balance: %s", sender_balance)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(
                transaction
            )
        return Wallet.verify_transaction(transaction)

    @classmethod
    def verify_transactions(cls, open_transactions: List[Any], get_balance: Callable):
        """
        Verifies all open & unprocessed transactions without checking sender's balance
        """
        return all(
            cls.verify_transaction(tx, get_balance, False) for tx in open_transactions
        )

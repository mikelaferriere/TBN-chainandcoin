"""
The blockchain (Really need to add a better description of what this is)
"""
from functools import reduce

from urllib.parse import urlparse
from uuid import UUID

from typing import Any, Dict, List, Optional, Set, Tuple

import logging
import requests

from google.protobuf.timestamp_pb2 import Timestamp

from generated.block_pb2 import Block
from generated.transaction_pb2 import Transaction
from verification import Verification
from walletv2 import Wallet

logger = logging.getLogger(__name__)

MINING_REWARD = 10


class Blockchain:  # pylint: disable=too-many-instance-attributes
    """
    This class manages the chain of blocks, open transactions and the node on which it's running
      chain_identifier : <uuid>
          Unique Identifier for this particular node
      chain: <List[Block]>
          The list of blocks
      __open_transactions (private): <List<Transaction]>
          The list of transactions that have not yet been committed in a block to the blockchain
      difficulty : <int> optional
          The difficulty for mining
      address : <str>
          Wallet address that transfers initiated from this node will be used as the recipient
    """

    def __init__(
        self, address: str, node_id: UUID, difficulty: int = 4, version: str = "0.1"
    ) -> None:
        # Generate a globally unique UUID for this node
        self.chain_identifier = node_id
        self.__open_transactions = []  # type: List[Any]
        self.nodes = set()  # type: Set[Any]
        self.difficulty = difficulty
        self.address = address
        self.version = version

        # Create the 'genesis' block. This is the inital block.
        genesis_block = Block(
            index=0,
            timestamp=Timestamp().GetCurrentTime(),  # type: ignore
            transaction_count=0,
            transactions=[],
            nonce=100,
            previous_hash="",
            difficulty=difficulty,
            version=version,
        )

        self.chain = [genesis_block]

    @property
    def chain(self) -> List[Any]:
        """
        This turns the chain attribute into a property with a getter (the method below)
        and a setter (@chain.setter)

        chain[:] returns a copy so we only get a copy of the reference of the objects,
        so we can't directly change the value
        """
        return self.__chain[:]

    @chain.setter
    def chain(self, val: List[Any]) -> None:
        """
        Setter function to directly set the value of the chain. This is only used when
        re-aligning the chain with the rest of the network, and setting up the genesis block.
        """
        self.__chain = val

    @property
    def chain_length(self) -> int:
        """
        Return the length of the current chain
        """
        return len(self.__chain)

    def add_block_to_chain(self, block: Any) -> None:
        """
        Adds the current block to the chain. By this time, it has been fully verified and
        the chain will be valid once it is added
        """
        self.__chain.append(block)

    @property
    def get_open_transactions(self) -> List[Any]:
        """
        Return a copy of the list of transactions that have not yet been mined
        """
        return self.__open_transactions[:]

    @property
    def last_block(self) -> Any:
        """
        Returns the last block in the chain
        """
        return self.__chain[-1]

    @property
    def next_index(self) -> int:
        """
        Returns the index for the next block
        """
        return len(self.__chain)

    def pretty_chain(self) -> List[Dict]:
        """
        Returns the full Blockchain in a nicely formatted string
        :return: <str>
        """

        return [c.SerializeToString().hex() for c in self.chain]

    def __broadcast_transaction(self, transaction: Any) -> None:
        """
        Broadcast the current transaction to all nodes on the network that this node
        is aware of.

        This ensures synchronicity across all nodes on the network.
        """
        for node in self.nodes:
            url = f"{node}/broadcast-transaction"
            try:
                response = requests.post(
                    url,
                    json={"transaction": transaction.SerializeToString().hex()},
                )
                if response.status_code == 400 or response.status_code == 500:
                    logger.error(
                        "Transaction declined, needs resolving: %s", response.json()
                    )
            except requests.exceptions.ConnectionError:
                continue

    def __broadcast_block(self, block: Any) -> None:
        """
        Broadcast the current block to all nodes on the network that this node
        is aware of.

        This block has already been validated and approved

        This ensures synchronicity across all nodes on the network.
        """
        for node in self.nodes:
            url = f"{node}/broadcast-block"
            try:
                response = requests.post(
                    url, json={"block": block.SerializeToString().hex()}
                )
                if response.status_code == 400 or response.status_code == 500:
                    logger.error("Block declined, needs resolving: %s", response.json())
            except requests.exceptions.ConnectionError:
                continue

    # Calculate and return the balance of the user
    def get_balance(self, sender: str = None) -> Optional[float]:
        """
        Calculate the current balance of the sender according to the amount of
        transactions on the chain.
        """
        if not sender:
            if not self.address:
                return None
            participant = self.address
        else:
            participant = sender

        # Fetch a list of all sent coin amounts for the given person
        # (empty lists are returned if the person was NOT the sender)
        #
        # This fetches sent amounts of transactions that were already included in
        # blocks of the blockchain
        tx_sender = [
            [tx.amount for tx in block.transactions if tx.sender == participant]
            for block in self.chain
        ]

        logger.debug("Sender's sent tx on the chain: %s", tx_sender)

        # Fetch a list of all sent coin amounts for the given person
        # (empty lists are returned if the person was NOT the sender)
        #
        # This fetches sent amounts of open transactions
        open_tx_sender = [
            tx.amount for tx in self.get_open_transactions if tx.sender == participant
        ]
        tx_sender.append(open_tx_sender)

        logger.debug("Sender's sent tx in open transactions: %s", tx_sender)

        amount_sent = reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
            if len(tx_amt) > 0.0
            else tx_sum + 0.0,
            tx_sender,
            0.0,
        )

        logger.debug("Sender's total sent: %s", amount_sent)

        # This fetches received coin amounts of transactions that were already included
        # in blocks of the blockchain
        #
        # We ignore open transactions here because you shouldn't be able to spend coins
        # before the transaction was confirmed + included in a block
        tx_recipient = [
            [tx.amount for tx in block.transactions if tx.recipient == participant]
            for block in self.chain
        ]

        logger.debug("Sender's received tx on the chain: %s", tx_recipient)

        amount_received = reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
            if len(tx_amt) > 0.0
            else tx_sum + 0.0,
            tx_recipient,
            0.0,
        )

        logger.debug("Sender's total received: %s", amount_received)
        logger.debug("Sender's balance: %s", (amount_received - amount_sent))

        # Return the total balance
        return amount_received - amount_sent

    def add_transaction(self, transaction: Any, is_receiving: bool = False) -> int:
        """
        Creates a new transaction to go into the next mined Block
        :param transaction: <Transaction>
            A single Transaction
        :param is_receiving: Optional <bool>
            Use to determine if the transaction was created
            by this node or another on the network
        :return: <int>
            The index of the Block that will hold this transaction
        """

        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            if not is_receiving:
                self.__broadcast_transaction(transaction)
        else:
            raise ValueError(
                "The sender does not have enough coin to make this "
                "transaction. We may want to change this to not raise "
                "an exception later, but for now, we should break."
            )

        return self.last_block.index + 1

    def proof_of_work(self, difficulty: int) -> int:
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
        last_block = self.last_block
        previous_hash = Verification.hash_block(last_block)

        nonce = 0
        while not Verification.valid_nonce(
            nonce, self.get_open_transactions, previous_hash, difficulty
        ):
            nonce += 1

        return nonce

    def mine_block(
        self, address: Optional[str] = None, difficulty: Optional[int] = None
    ) -> Optional[Any]:
        """
        The current node runs the mining protocol, and depending on the difficulty, this
        could take a lot of processing power.

        Once the nonce is discovered, or "mined", the reward transaction is created.

        Then all of the open transactions are validated and verified, ensuring that
        the senders in all of the transactions have enough coin to conduct the transaction.

        Once the transactions are validated, the reward block is added to the list of
        open transactions. This is because Mining transactions do not need to be validated
        since they are created by the node itself.

        The block is then added directy to the node's chain and the open_transactions is
        cleared and ready for a new block to be mined

        Finally, the new block is broadcasted to all connected nodes.
        """
        if not address:
            address = self.address

        if not address:
            return None

        difficulty = difficulty if difficulty is not None else self.difficulty

        last_block = self.last_block

        # Hash the last Block so we can compare it to the stored value
        previous_hash = Verification.hash_block(last_block)

        # We run the PoW algorithm to get the next nonce
        nonce = self.proof_of_work(difficulty)

        # Create the transaction that will be rewarded to the miners for their work
        # The sender is "0" or "Mining" to signify that this node has mined a new coin.
        reward_transaction = Transaction(
            sender="0", recipient=address, amount=MINING_REWARD
        )

        # Copy transactions instead of manipulating the original open_transactions list
        # This ensures that if for some reason the mining should fail,
        # we don't have the reward transaction stored in the pending transactions
        copied_open_transactions = self.get_open_transactions
        for tx in copied_open_transactions:
            if not Wallet.verify_transaction(tx):
                return None

        copied_open_transactions.append(reward_transaction)
        block = Block(
            index=self.next_index,
            timestamp=Timestamp().GetCurrentTime(),  # type: ignore
            transaction_count=len(copied_open_transactions),
            transactions=copied_open_transactions,
            nonce=nonce,
            previous_hash=previous_hash,
            difficulty=difficulty,
            version=self.version,
        )

        # Add the block to the node's chain
        self.add_block_to_chain(block)

        # Reset the open list of transactions
        self.__open_transactions = []

        self.__broadcast_block(block)

        return block

    def add_block(self, block: Any) -> Tuple[bool, Optional[str]]:
        """
        When a new block is received via a broadcast, the receiving nodes must validate the
        block to make sure it is valid, and then add it to their chains.

        This also makes sure that there are not open transactions on any of the nodes
        that match a transaction in the broadcasted block. This is some safety to ensure that
        there is not double spending.
        """
        if not Verification.valid_nonce(
            block.nonce, block.transactions[:-1], block.previous_hash, 4
        ):
            return False, "Nonce is not valid"
        if not Verification.hash_block(self.last_block) == block.previous_hash:
            return (
                False,
                "Hash of last block does not equal previous hash in the current block",
            )
        self.add_block_to_chain(block)

        # Alway work off a copy as to not disrupt the current list of open transactions
        stored_transactions = self.__open_transactions[:]
        for itx in block.transactions:
            for opentx in stored_transactions:
                if (
                    opentx.sender == itx.sender
                    and opentx.recipient == itx.recipient
                    and opentx.amount == itx.amount
                    and opentx.signature == itx.signature
                ):
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        logger.warning("Item was already removed: %s", opentx)
        return True, "success"

    def register_node(self, address: str) -> None:
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        if not parsed_url.scheme:
            raise ValueError("Must provide scheme (http/https) in node uri")
        self.nodes.add(f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}")

    def resolve_conflicts(self) -> bool:
        """
        This is our Consensus Algorithm. It resolves conflicts by replacing our chain with
        the longest one in the network.

        :return: <bool> True if our chain was replaces, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f"{node}/chain")

            if response.ok:
                length = response.json()["length"]
                chain_hashes = response.json()["chain"]

                chain = []

                for b in chain_hashes:
                    block = Block()
                    block.ParseFromString(bytes.fromhex(b))
                    chain.append(block)

                # Check if the length is longer and the chain is valid
                if length > max_length and Verification.verify_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

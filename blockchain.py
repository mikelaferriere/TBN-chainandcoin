"""
The blockchain (Really need to add a better description of what this is)
"""
from functools import reduce

from datetime import datetime

from urllib.parse import urlparse
from uuid import UUID

from typing import List, Optional, Set, Tuple

import tempfile
import shutil
import logging
import requests

from block import Block, Header
from transaction import Details, FinalTransaction, SignedRawTransaction, get_merkle_root
from verification import Verification
from wallet import Wallet

logger = logging.getLogger(__name__)

MINING_REWARD = 10


class Blockchain:  # pylint: disable=too-many-instance-attributes
    """
    This class manages the chain of blocks, open transactions and the node on which it's running
      chain_identifier : <uuid>
          Unique Identifier for this particular node
      chain: <List[Block]>
          The list of blocks
      __open_transactions (private): <List[FinalTransaction]>
          The list of transactions that have not yet been committed in a block to the blockchain
      difficulty : <int> optional
          The difficulty for mining
      address : <str>
          Wallet address that transfers initiated from this node will be used as the recipient
    """

    def __init__(
        self,
        address: str,
        node_id: UUID,
        is_test: bool = False,
        *,
        difficulty: int = 4,
        version: int = 1,
        timestamp: Optional[datetime] = None,
    ) -> None:
        # Generate a globally unique UUID for this node
        self.chain_identifier = node_id
        self.__open_transactions = []  # type: List[FinalTransaction]
        self.nodes = set()  # type: Set[str]
        self.difficulty = difficulty
        self.address = address
        self.version = version
        self.data_location = "data" if not is_test else f"{tempfile.tempdir}/blockchain"
        if is_test:
            try:
                shutil.rmtree(self.data_location)
            except Exception:
                pass

        # Create the 'genesis' block. This is the inital block.
        header = Header(
            timestamp=timestamp if timestamp is not None else datetime.utcnow(),
            transaction_merkle_root=get_merkle_root([]),
            nonce=100,
            previous_hash="",
            difficulty=difficulty,
            version=version,
        )

        self.chain = [
            Block(
                index=0,
                block_hash=Verification.hash_block_header(header),
                size=len(str(header)),
                header=header,
                transaction_count=0,
                transactions=[],
            )
        ]

        self.load_data()

    @property
    def chain(self) -> List[Block]:
        """
        This turns the chain attribute into a property with a getter (the method below)
        and a setter (@chain.setter)

        chain[:] returns a copy so we only get a copy of the reference of the objects,
        so we can't directly change the value
        """
        return self.__chain[:]

    @chain.setter
    def chain(self, val: List[Block]) -> None:
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

    def add_block_to_chain(self, block: Block) -> None:
        """
        Adds the current block to the chain. By this time, it has been fully verified and
        the chain will be valid once it is added
        """
        self.__chain.append(block)

    @property
    def get_open_transactions(self) -> List[FinalTransaction]:
        """
        Return a copy of the list of transactions that have not yet been mined
        """
        return self.__open_transactions[:]

    @property
    def last_block(self) -> Block:
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

    def pretty_chain(self) -> List[str]:
        """
        Returns the full Blockchain in a nicely formatted string
        :return: <str>
        """

        return [b.block_hash for b in self.chain]

    def save_data(self) -> None:
        try:
            for transaction in self.get_open_transactions:
                FinalTransaction.SaveTransaction(
                    self.data_location, transaction, "open"
                )

            for block in self.chain:
                Block.SaveBlock(self.data_location, block)
        except Exception as e:
            logger.exception(e)

    def load_data(self) -> None:
        try:
            txs = FinalTransaction.LoadTransactions(self.data_location, "open")
            if txs:
                self.__open_transactions = txs

            chain = Block.LoadBlocks(self.data_location)
            if chain:
                # Ensure that the chain is sorted by index
                chain.sort(key=lambda x: x.index, reverse=False)

                self.chain = chain
        except Exception as e:
            logger.exception(e)

    def __broadcast_transaction(self, transaction: SignedRawTransaction) -> None:
        """
        Broadcast the current transaction to all nodes on the network that this node
        is aware of.

        This ensures synchronicity across all nodes on the network.
        """
        for node in self.nodes:
            url = f"{node}/broadcast-transaction"
            try:
                logging.debug("Broadcasting new transaction %s to %s", transaction, url)
                response = requests.post(
                    url,
                    json={"transaction": transaction.SerializeToHex()},
                )
                if response.status_code == 400 or response.status_code == 500:
                    logger.error(
                        "Transaction declined, needs resolving: %s", response.json()
                    )
            except requests.exceptions.ConnectionError:
                continue

    def __broadcast_block(self, block: Block) -> None:
        """
        Broadcast the current block to all nodes on the network that this node
        is aware of.

        This block has already been validated and approved

        This ensures synchronicity across all nodes on the network.
        """
        logger.debug("Broadcasting blocks to following nodes: %s", self.nodes)
        for node in self.nodes:
            url = f"{node}/broadcast-block"
            logger.debug("Broadcasting new block %s to %s", block, url)
            try:
                response = requests.post(url, json={"block": block.SerializeToHex()})
                if response.status_code == 400 or response.status_code == 500:
                    logger.error("Block declined, needs resolving: %s", response.json())
            except requests.exceptions.ConnectionError:
                continue

    def get_last_tx_nonce(
        self, tx: SignedRawTransaction, type_: str, exclude: bool
    ) -> Optional[int]:
        """
        Get the last sender's transactions
        """

        all_transactions = FinalTransaction.LoadTransactions(self.data_location, type_)
        participant = tx.details.sender

        txns = [
            t.signed_transaction
            for t in all_transactions
            if t.signed_transaction.details.sender == participant
        ]
        txns.sort(key=lambda t: t.details.nonce, reverse=False)

        # When getting the correct nonce, exclude the current transacation when this is done via
        # mining, since these have already been verified, so the nonce of tx will always be in
        # txns
        if exclude:
            txns = list(filter(lambda t: t != tx, txns))

        nonces = [t.details.nonce for t in txns]
        return nonces[0] if nonces else None

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

        all_transactions = FinalTransaction.LoadAllTransactions(self.data_location)

        # Fetch a list of all sent coin amounts for the given person
        # (empty lists are returned if the person was NOT the sender)

        # This fetches sent amounts of transactions that were already included in
        # blocks of the blockchain
        tx_sender = [
            [
                tx.signed_transaction.details.amount
                for tx in all_transactions
                if tx.signed_transaction.details.sender == participant
            ]
        ]

        logger.debug("Sender's sent transactions on the chain: %s", tx_sender)

        amount_sent = reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
            if len(tx_amt) > 0.0
            else tx_sum + 0.0,
            tx_sender,
            0.0,
        )

        logger.debug("Sender's total coin sent: %s", amount_sent)

        # This fetches received coin amounts of transactions that were already included
        # in blocks of the blockchain
        #
        # We ignore open transactions here because you shouldn't be able to spend coins
        # before the transaction was confirmed + included in a block
        tx_recipient = [
            [
                tx.signed_transaction.details.amount
                for tx in all_transactions
                if tx.signed_transaction.details.recipient == participant
            ]
        ]

        logger.debug("Sender's received transactions on the chain: %s", tx_recipient)

        amount_received = reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
            if len(tx_amt) > 0.0
            else tx_sum + 0.0,
            tx_recipient,
            0.0,
        )

        logger.debug("Sender's total coin received: %s", amount_received)
        logger.debug("Sender's balance: %s", (amount_received - amount_sent))

        # Return the total balance
        return amount_received - amount_sent

    def add_transaction(
        self, transaction: SignedRawTransaction, is_receiving: bool = False
    ) -> int:
        """
        Creates a new transaction to go into the next mined Block
        :param transaction: <SignedRawTransaction>
            A single Transaction
        :param is_receiving: Optional <bool>
            Use to determine if the transaction was created
            by this node or another on the network
        :return: <int>
            The index of the Block that will hold this transaction
        """

        if Verification.verify_transaction(
            transaction, self.get_balance, self.get_last_tx_nonce
        ):
            final_tx = FinalTransaction(
                transaction_hash=Verification.hash_transaction(transaction),
                transaction_id=Verification.hash_transaction(transaction),
                signed_transaction=transaction,
            )

            self.__open_transactions.append(final_tx)
            self.save_data()

            if not is_receiving:
                self.__broadcast_transaction(transaction)
        else:
            raise ValueError(
                "The sender does not have enough coin to make this "
                "transaction. We may want to change this to not raise "
                "an exception later, but for now, we should break."
            )
        return self.last_block.index + 1

    def mine_block(
        self,
        address: Optional[str] = None,
        difficulty: Optional[int] = None,
        version: Optional[int] = None,
    ) -> Optional[Block]:
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
        version = version if version is not None else self.version
        last_block = self.last_block
        transaction_merkle_root = get_merkle_root(
            [tx.signed_transaction for tx in self.get_open_transactions]
        )
        previous_hash = Verification.hash_block_header(last_block.header)

        block_header = Header(
            version=version,
            difficulty=difficulty,
            timestamp=datetime.utcnow(),
            transaction_merkle_root=transaction_merkle_root,
            previous_hash=previous_hash,
            nonce=0,
        )

        # We run the PoW algorithm to get the next nonce and return an updated block_header
        block_header = Verification.proof_of_work(block_header)

        # Create the transaction that will be rewarded to the miners for their work
        # The sender is "0" or "Mining" to signify that this node has mined a new coin.
        reward_signed = SignedRawTransaction(
            details=Details(
                sender="0",
                recipient=address,
                nonce=0,
                amount=MINING_REWARD,
                timestamp=datetime.utcnow(),
                public_key="coinbase",
            ),
            signature="coinbase",
        )

        reward_transaction = FinalTransaction(
            transaction_hash=Verification.hash_transaction(reward_signed),
            transaction_id=Verification.hash_transaction(reward_signed),
            signed_transaction=reward_signed,
        )

        # Copy transactions instead of manipulating the original open_transactions list
        # This ensures that if for some reason the mining should fail,
        # we don't have the reward transaction stored in the pending transactions
        copied_open_transactions = self.get_open_transactions
        for tx in copied_open_transactions:
            if not Wallet.verify_transaction(
                tx.signed_transaction, self.get_last_tx_nonce, exclude_from_open=True
            ):
                return None

        FinalTransaction.SaveTransaction(
            self.data_location, reward_transaction, "mining"
        )
        self.__broadcast_transaction(reward_transaction.signed_transaction)

        copied_open_transactions.append(reward_transaction)

        block = Block(
            index=self.next_index,
            header=block_header,
            block_hash=Verification.hash_block_header(block_header),
            size=len(str(block_header)),
            transaction_count=len(copied_open_transactions),
            transactions=[t.transaction_hash for t in copied_open_transactions],
        )

        # Add the block to the node's chain
        self.add_block_to_chain(block)

        # Reset the open list of transactions
        logger.info("Moving open transaction to confirmed storage")
        FinalTransaction.MoveOpenTransactions(self.data_location)
        self.__open_transactions = []
        self.save_data()

        self.__broadcast_block(block)

        return block

    def add_block(self, block: Block) -> Tuple[bool, Optional[str]]:
        """
        When a new block is received via a broadcast, the receiving nodes must validate the
        block to make sure it is valid, and then add it to their chains.

        This also makes sure that there are not open transactions on any of the nodes
        that match a transaction in the broadcasted block.
        """
        if not Verification.valid_nonce(block.header):
            return False, "Nonce is not valid"
        if (
            not Verification.hash_block_header(self.last_block.header)
            == block.header.previous_hash
        ):
            return (
                False,
                "Hash of last block does not equal previous hash in the current block",
            )
        self.add_block_to_chain(block)

        # Always work off a copy as to not disrupt the current list of open transactions
        stored_transactions = self.__open_transactions[:]
        for itx in block.transactions:
            for opentx in stored_transactions:
                if opentx.transaction_hash == itx:
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        logger.warning("Item was already removed: %s", opentx)

        self.save_data()
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
        full_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        self.nodes.add(full_url)
        logger.debug("Registered node: %s", full_url)

    def resolve_conflicts(self) -> bool:
        """
        This is our Consensus Algorithm. It resolves conflicts by replacing our chain with
        the longest one in the network.

        :return: <bool> True if our chain was replaces, False if not
        """

        logger.debug("Resolving conflicts between the nodes if applicable")

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        current_chain_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f"{node}/chain")

            if response.ok:
                length = response.json()["length"]
                chain_hashes = response.json()["chain"]

                chain = []

                for b in chain_hashes:
                    response = requests.get(f"{node}/block/{b}")
                    if response.ok:
                        chain.append(Block.parse_raw(response.json()))

                if (
                    length == 1
                    and current_chain_length == 1
                    and Verification.verify_chain(chain)
                ):
                    logger.debug("Chain's are both 1 length so preferring neighbour's")
                    current_chain_length = length
                    new_chain = chain

                # Ensure that the chain is sorted by index
                chain.sort(key=lambda x: x.index, reverse=False)

                # Check if the length is longer and the chain is valid
                if length > current_chain_length:
                    logger.debug("Neighbour's chain is longer than ours")
                    logger.debug("Verifying neighbour's chain")
                    if Verification.verify_chain(chain):
                        logger.debug("Neighbour's chain successfully verified")
                        current_chain_length = length
                        new_chain = chain
                    else:
                        logger.warning("Neighbour's chain failed verified")

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            logger.info("Replacing our chain with neighbour's chain")
            self.chain = new_chain
        else:
            logger.info("Keeping this node's chain. Now making sure its saved")

        self.save_data()
        return new_chain is not None and len(new_chain) > 0

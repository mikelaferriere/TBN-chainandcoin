from time import time
from urllib.parse import urlparse
from uuid import uuid4

from typing import Any, Dict, List, Optional, Set

import hashlib
import json
import requests

from block import Block
from transaction import Transaction


class Blockchain:
    """
    The blockchain
    """

    def __init__(self, difficulty: int = 4) -> None:
        # Generate a globally unique UUID for this node
        self.chain_identifier = str(uuid4()).replace("-", "")
        self.chain = []  # type: List[Block]
        self.current_transactions = []  # type: List[Transaction]
        self.nodes = set()  # type: Set[Any]
        self.difficulty = difficulty

        # Create the 'genesis' block. This is the inital block.
        if not self.chain:
            self.new_block(proof=0, previous_hash="0")

    def pretty_chain(self) -> List[Dict]:
        """
        Returns the full Blockchain in a nicely formatted string
        :return: <str>
        """

        return [c.dict() for c in self.chain]

    @staticmethod
    def calculate_hash(block: Block) -> str:
        """
        Creates a sha-256 hash of a Block
        :param block: <Block> Block
        :return: <str>
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block.to_ordered_dict(), sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Block:
        # Returns the last block in the chain
        return self.chain[-1]

    @property
    def pending_transactions(self) -> List[Transaction]:
        return self.current_transactions

    def new_block(self, proof: int, previous_hash: Optional[str] = None) -> Block:
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of the previous Block
        :return: <Block> New Block
        """

        block = Block(
            index=len(self.chain) + 1,
            timestamp=time(),
            transactions=self.current_transactions,
            proof=proof,
            previous_hash=previous_hash or self.calculate_hash(self.last_block),
        )

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def __broadcast_new_transaction(
        self, transaction: Transaction, is_receiving: bool
    ) -> None:
        for node in self.nodes:
            if not is_receiving:
                url = "http://{}/broadcast-transaction".format(node)
                try:
                    response = requests.post(
                        url,
                        json={
                            "sender": transaction.sender,
                            "recipient": transaction.recipient,
                            "amount": transaction.amount,
                            "signature": transaction.signature,
                        },
                    )
                    if response.status_code == 400 or response.status_code == 500:
                        print("Transaction declined, needs resolving")
                except requests.exceptions.ConnectionError:
                    continue

    def new_transaction(
        self, transaction: Transaction, is_receiving: bool = False
    ) -> int:
        """
        Creates a new transaction to go into the next mined Block
        :param transaction: <Transaction> A single Transaction
        :param is_receiving: Optional <bool> Use to determine if the transaction was created
                                             by this node or a another on the network
        :return: <int> The index of the Block that will hold this transaction
        """

        self.current_transactions.append(transaction)
        self.__broadcast_new_transaction(transaction, is_receiving)

        return self.last_block.index + 1

    @staticmethod
    def valid_proof(proof: int, block: Block, difficulty: int) -> bool:
        """
        Validates the Proof: Does the hash(proof, block) contain 4 leading zeros?
        :param proof: <int> Current Proof
        :param block: <Block> Previous Block
        :return: <bool> True if correct, False if not
        """

        str_block = json.dumps(block.to_ordered_dict())
        guess = f"{str_block}-{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == "0" * difficulty

    def proof_of_work(self, last_block: Block, difficulty: Optional[int]) -> int:
        """
        Simple Proof of Work Algorithm
          - Find a number 'p' such that hash(pp') contains leading 4 zeros,
            where p is the previous p'
          - p is the previous proof, and p' is the new proof
        :param last_block: <Block>
        :param difficulty: Optional <int>
        :return: <int>
        """

        difficulty = difficulty if difficulty is not None else self.difficulty

        proof = 0
        while self.valid_proof(proof, last_block, difficulty) is False:
            proof += 1

        return proof

    def __broadcast_new_block(self, block: Block) -> None:
        for node in self.nodes:
            url = "http://{}/broadcast-block".format(node)
            try:
                response = requests.post(
                    url, json={"block": json.dumps(block.to_ordered_dict())}
                )
                if response.status_code == 400 or response.status_code == 500:
                    print("Block declined, needs resolving")
            except requests.exceptions.ConnectionError:
                continue

    def mine(self, miner_address: str, difficulty: Optional[int] = None) -> None:
        # We run the PoW algorithm to get the next proof
        last_block = self.last_block
        proof = self.proof_of_work(last_block, difficulty)

        # Forge the new Block by adding it to the chain
        previous_hash = self.calculate_hash(last_block)
        block = self.new_block(proof, previous_hash)

        self.__broadcast_new_block(block)
        # We must receive a reward for finding the proof
        # The sender is "0" to signify that this node has minded a new coin.
        self.new_transaction(Transaction(sender="0", recipient=miner_address, amount=1))

    def register_node(self, address: str) -> None:
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain: List[Block]) -> bool:
        """
        Determine if a given blockchain is valid
        :param chain: List[Block] A Blockchain
        :return: <bool> True if valid, False if note
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f"{last_block}")
            print(f"{block}")
            print("\n------------\n")

            # Check that the hash of the block is correct
            if block.previous_hash != self.calculate_hash(last_block):
                return False

            # Check that the PoW is correct
            if not self.valid_proof(block.proof, block, self.difficulty):
                return False

            last_block = block
            current_index += 1

        return True

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
            response = requests.get(f"http://{node}/chain")

            if response.ok:
                length = response.json()["length"]
                chain = response.json()["chain"]

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

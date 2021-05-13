from datetime import datetime
from typing import Any, List
from pydantic import BaseModel

from google.protobuf.timestamp_pb2 import Timestamp

from transaction import Transaction
from generated import block_pb2


class Block(BaseModel):
    """
    index : <int> The location of the block in the chain (0 indexed)
    timestamp : <datetime> The datetime, with zone, including milliseconds
    transaction_count : <int> Count of transactions
    transactions : <List[Transaction]> A list of the transactions in the block
    nonce : <int> The number used in mining
    previous_hash: <str> The hash of the block with [index - 1] (it's immediate ancestor)
    difficulty : <int> The difficulty for the mining process
    version : <str> Version for the Blockchain
    """

    index: int
    transaction_count: int
    transactions: List[Transaction]
    nonce: int
    previous_hash: str
    difficulty: int
    version: str
    timestamp: datetime

    def SerializeToString(self) -> bytes:
        timestamp = Timestamp()
        timestamp.FromDatetime(self.timestamp)

        b = block_pb2.Block(
            index=self.index,
            timestamp=timestamp,
            transaction_count=self.transaction_count,
            transactions=[t.ToProtobuf() for t in self.transactions],
            nonce=self.nonce,
            previous_hash=self.previous_hash,
            difficulty=self.difficulty,
            version=self.version,
        )

        return b.SerializeToString()

    @staticmethod
    def ParseFromString(block_bytes: bytes) -> Any:
        b = block_pb2.Block()
        b.ParseFromString(block_bytes)

        transactions = b.transactions if b.transaction_count > 0 else []

        return Block(
            index=b.index,
            timestamp=b.timestamp.ToDatetime(),
            transaction_count=b.transaction_count,
            transactions=[Transaction.ParseFromString(t) for t in transactions],
            nonce=b.nonce,
            previous_hash=b.previous_hash,
            difficulty=b.difficulty,
            version=b.version,
        )

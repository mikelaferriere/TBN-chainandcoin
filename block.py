from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel

from google.protobuf.timestamp_pb2 import Timestamp

from transaction import Transaction
from generated import block_pb2


class Header(BaseModel):
    """
    version : <int> Version for the Blockchain for Miners to know if they need to upgrade
    previous_hash: <str> The hash of the block header with [index - 1] (it's immediate ancestor)
    transaction_merkle_root : <str> A merkle root of all the transactions
    timestamp : <datetime> The datetime, with zone, including milliseconds
    difficulty : <int> The difficulty for the mining process
    nonce : <int> The number used in mining
    """

    version: int
    previous_hash: str
    transaction_merkle_root: str
    timestamp: datetime
    difficulty: int
    nonce: int

    def ToProtobuf(self) -> Any:
        return block_pb2.Header(
            version=self.version,
            previous_hash=self.previous_hash,
            transaction_merkle_root=self.transaction_merkle_root,
            timestamp=self.timestamp,
            difficulty=self.difficulty,
            nonce=self.nonce,
        )

    @staticmethod
    def FromProtobuf(header: Any) -> Header:
        timestamp = datetime.strptime(
            header.timestamp.ToJsonString(), "%Y-%m-%dT%H:%M:%SZ"
        )

        return Header(
            version=header.version,
            previous_hash=header.previous_hash,
            transaction_merkle_root=header.transaction_merkle_root,
            timestamp=timestamp,
            difficulty=header.difficulty,
            nonce=header.nonce,
        )

    def SerializeToString(self) -> bytes:
        timestamp = Timestamp()
        timestamp.FromDatetime(self.timestamp)

        header = block_pb2.Header(
            version=self.version,
            previous_hash=self.previous_hash,
            transaction_merkle_root=self.transaction_merkle_root,
            timestamp=timestamp,
            difficulty=self.difficulty,
            nonce=self.nonce,
        )

        return header.SerializeToString()

    def SerializeToHex(self) -> str:
        return self.SerializeToString().hex()

    @staticmethod
    def ParseFromString(header_bytes: bytes) -> Header:
        header = block_pb2.Header()
        header.ParseFromString(header_bytes)

        return Header(
            version=header.version,
            previous_hash=header.previous_hash,
            transaction_merkle_root=header.transaction_merkle_root,
            timestamp=header.timestamp.ToDatetime(),
            nonce=header.nonce,
            difficulty=header.difficulty,
        )

    @staticmethod
    def ParseFromHex(header_hex: str) -> Header:
        return Header.ParseFromString(bytes.fromhex(header_hex))


class Block(BaseModel):
    """
    index : <int> The location of the block in the chain (0 indexed)
    header : <Header> Block's header information
    transaction_count : <int> Count of transactions
    transactions : <List[Transaction]> A list of the transactions in the block
    block_hash : <optional str> Hash of the current block header
    size : <optional float> The size of the block (KB or MB)
    """

    index: int
    header: Header
    transaction_count: int
    transactions: List[Transaction]
    block_hash: Optional[str] = None
    size: Optional[int] = 0

    def SerializeToString(self) -> bytes:
        timestamp = Timestamp()
        timestamp.FromDatetime(self.header.timestamp)

        block = block_pb2.Block(
            index=self.index,
            size=self.size,
            block_hash=self.block_hash,
            header=block_pb2.Header(
                version=self.header.version,
                previous_hash=self.header.previous_hash,
                transaction_merkle_root=self.header.transaction_merkle_root,
                timestamp=timestamp,
                nonce=self.header.nonce,
                difficulty=self.header.difficulty,
            ),
            transaction_count=self.transaction_count,
            transactions=[t.ToProtobuf() for t in self.transactions],
        )

        return block.SerializeToString()

    def SerializeToHex(self) -> str:
        return self.SerializeToString().hex()

    @staticmethod
    def ParseFromString(block_bytes: bytes) -> Block:
        block = block_pb2.Block()
        block.ParseFromString(block_bytes)

        return Block(
            index=block.index,
            size=block.size,
            block_hash=block.block_hash,
            header=Header.FromProtobuf(block.header),
            transaction_count=block.transaction_count,
            transactions=[Transaction.FromProtobuf(t) for t in block.transactions],
        )

    @staticmethod
    def ParseFromHex(block_hex: str) -> Block:
        return Block.ParseFromString(bytes.fromhex(block_hex))

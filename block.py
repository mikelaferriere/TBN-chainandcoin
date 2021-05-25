from __future__ import annotations

from pathlib import Path

from datetime import datetime
from typing import Any, List
from pydantic import BaseModel

from google.protobuf.timestamp_pb2 import Timestamp

from generated import block_pb2

from storage import Storage


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
        try:
            # This format only exists in testing specifically.
            timestamp = datetime.strptime(
                header.timestamp.ToJsonString(), "%Y-%m-%dT%H:%M:%SZ"
            )
        except ValueError:
            timestamp = datetime.strptime(
                header.timestamp.ToJsonString(), "%Y-%m-%dT%H:%M:%S.%fZ"
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
    transactions : <List[str]> A list of the transactions in the block
    block_hash : <optional str> Hash of the current block header
    size : <optional float> The size of the block (KB or MB)
    """

    index: int
    header: Header
    transaction_count: int
    transactions: List[str] = []
    block_hash: str
    size: int

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
            transactions=self.transactions,
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
            transactions=list(block.transactions),
        )

    @staticmethod
    def ParseFromHex(block_hex: str) -> Block:
        return Block.ParseFromString(bytes.fromhex(block_hex))

    @staticmethod
    def LoadBlocks(data_location: str) -> List[Block]:
        block_storage = Storage(Path(data_location))
        block_files = block_storage.list_files(Path("blocks"))
        blocks = []
        for f in block_files:
            b = block_storage.read_string(Path(f"blocks/{f}"))
            if not b:
                raise ValueError("Found a file in block folder that was not a block")

            blocks.append(Block.ParseFromHex(b))
        return blocks

    @staticmethod
    def SaveBlock(data_location: str, block: Block) -> None:
        block_storage = Storage(Path(data_location) / "blocks")
        block_storage.save(Path(block.block_hash), block.SerializeToHex())

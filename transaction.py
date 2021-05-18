from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel

import merkletools

from generated import transaction_pb2


class Transaction(BaseModel):
    """
    sender : <str> The sender of the transaction
    recipient : <str> The recipient of the transaction
    amount : <float> The amount of coin being transferred
    nonce : <int> A ever-incrementing value in order to ensure that each transaction
                  that is confirmed onto the block must have a nonce + 1 of the previously
                  confirmed transaction for this sender. This is imperative to ensure that
                  confirmed transactions can't be replayed over and over again to drain the
                  sender's coin. This is a fix for 'double-spending'.
    signature : optional <str> The signature of the transaction to prove that the sender 'signed'
                               off on the transaction.
    public_key : optional <str> The public key for the sender in order to verify that they were
                                the ones to create this transaction.

                                TODO: This should be included in the hash in a different,
                                      more secure way later.
    """

    sender: str
    recipient: str
    amount: float
    nonce: int
    public_key: Optional[str]
    signature: Optional[str]

    def ToProtobuf(self) -> Any:
        return transaction_pb2.Transaction(
            sender=self.sender,
            recipient=self.recipient,
            amount=self.amount,
            nonce=self.nonce,
            public_key=self.public_key,
            signature=self.signature,
        )

    @staticmethod
    def FromProtobuf(transaction: Any) -> Transaction:
        return Transaction(
            sender=transaction.sender,
            recipient=transaction.recipient,
            amount=transaction.amount,
            nonce=transaction.nonce,
            public_key=transaction.public_key if transaction.public_key else None,
            signature=transaction.signature if transaction.signature else None,
        )

    def SerializeToString(self) -> bytes:
        t = self.ToProtobuf()
        return t.SerializeToString()

    def SerializeToHex(self) -> str:
        return self.SerializeToString().hex()

    @staticmethod
    def ParseFromString(transaction_bytes: bytes) -> Transaction:
        t = transaction_pb2.Transaction()
        t.ParseFromString(transaction_bytes)

        return Transaction(
            sender=t.sender,
            recipient=t.recipient,
            amount=t.amount,
            nonce=t.nonce,
            public_key=t.public_key if t.public_key else None,
            signature=t.signature if t.signature else None,
        )

    @staticmethod
    def ParseFromHex(transaction_hex: str) -> Transaction:
        return Transaction.ParseFromString(bytes.fromhex(transaction_hex))

    @staticmethod
    def convert_to_merkle(transactions: List[Transaction]) -> merkletools.MerkleTools:
        mt = merkletools.MerkleTools(hash_type="sha256")

        mt.add_leaf([t.SerializeToHex() for t in transactions])
        mt.make_tree()

        return mt

    @staticmethod
    def get_merkle_root(transactions: List[Transaction]) -> str:
        merkle = Transaction.convert_to_merkle(transactions).get_merkle_root()
        return merkle if merkle is not None else ""

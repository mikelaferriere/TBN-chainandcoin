from __future__ import annotations

import logging

from datetime import datetime
from typing import Any, List, Optional
from pathlib import Path
from pydantic import BaseModel

import merkletools

from google.protobuf.timestamp_pb2 import Timestamp

from generated import transaction_pb2
from storage import Storage

logger = logging.getLogger(__name__)


def convert_to_merkle(
    transactions: List[SignedRawTransaction],
) -> merkletools.MerkleTools:
    mt = merkletools.MerkleTools(hash_type="sha256")

    mt.add_leaf([t.SerializeToHex() for t in transactions])
    mt.make_tree()

    return mt


def get_merkle_root(transactions: List[SignedRawTransaction]) -> str:
    merkle = convert_to_merkle(transactions).get_merkle_root()
    return merkle if merkle is not None else ""


class Details(BaseModel):
    """
    A raw version of a transaction that has not yet been signed or confirmed

    sender : <str> The sender of the transaction
    recipient : <str> The recipient of the transaction
    amount : <float> The amount of coin being transferred
    nonce : <int> A ever-incrementing value in order to ensure that each transaction
                  that is confirmed onto the block must have a nonce + 1 of the previously
                  confirmed transaction for this sender. This is imperative to ensure that
                  confirmed transactions can't be replayed over and over again to drain the
                  sender's coin. This is a fix for 'double-spending'.
    public_key : <str> The public key for the sender in order to verify that they were
                       the ones to create this transaction.

                       TODO: This should be included in the hash in a different,
                             more secure way later.
    """

    sender: str
    recipient: str
    amount: float
    nonce: int
    timestamp: datetime
    public_key: str

    def ToProtobuf(self) -> Any:
        timestamp = Timestamp()
        timestamp.FromDatetime(self.timestamp)

        return transaction_pb2.Details(
            sender=self.sender,
            recipient=self.recipient,
            amount=self.amount,
            nonce=self.nonce,
            timestamp=timestamp,
            public_key=self.public_key,
        )

    @staticmethod
    def FromProtobuf(d: Any) -> Details:
        try:
            # This format only exists in testing specifically.
            timestamp = datetime.strptime(
                d.timestamp.ToJsonString(), "%Y-%m-%dT%H:%M:%SZ"
            )
        except ValueError:
            timestamp = datetime.strptime(
                d.timestamp.ToJsonString(), "%Y-%m-%dT%H:%M:%S.%fZ"
            )

        return Details(
            sender=d.sender,
            recipient=d.recipient,
            amount=d.amount,
            nonce=d.nonce,
            timestamp=timestamp,
            public_key=d.public_key,
        )

    def SerializeToString(self) -> bytes:
        d = self.ToProtobuf()
        return d.SerializeToString()


class SignedRawTransaction(BaseModel):
    """
    A raw version of a signed transaction, ready to be hashed and validated into a block

    details: <Details> The unsigned version of the transaction
    signature : <str> The signature of the unsigned_transaction to prove that the sender 'signed'
                      off on the transaction.
    """

    details: Details
    signature: str

    def ToProtobuf(self) -> Any:
        return transaction_pb2.SignedRawTransaction(
            details=self.details.ToProtobuf(),
            signature=self.signature,
        )

    @staticmethod
    def FromProtobuf(transaction: Any) -> SignedRawTransaction:
        return SignedRawTransaction(
            details=transaction.details,
            signature=transaction.signature,
        )

    def SerializeToString(self) -> bytes:
        t = self.ToProtobuf()
        return t.SerializeToString()

    def SerializeToHex(self) -> str:
        return self.SerializeToString().hex()

    @staticmethod
    def ParseFromString(transaction_bytes: bytes) -> SignedRawTransaction:
        t = transaction_pb2.SignedRawTransaction()
        t.ParseFromString(transaction_bytes)

        details = Details.FromProtobuf(t.details)
        return SignedRawTransaction(
            details=details,
            signature=t.signature,
        )

    @staticmethod
    def ParseFromHex(transaction_hex: str) -> SignedRawTransaction:
        return SignedRawTransaction.ParseFromString(bytes.fromhex(transaction_hex))


class FinalTransaction(BaseModel):
    """
    A final version of a SignedRawTransaction, with transaction hash and id, ready to be
    validated into a block. This is the version that can be saved (in hex value) to the
    node's storage for lookup later.

    The transaction hash will be added to the list of transactions in the block.

    transaction_hash : <str> sha256 hash of the SignedRawTransaction
    transaction_id : <str> id of the transaction (will match transaction_hash until more
                           transaction types are added to the blockchain)
    signed_transaction : <SignedRawTransaction> the details of the transaction
    """

    transaction_hash: str
    transaction_id: str
    signed_transaction: SignedRawTransaction

    @staticmethod
    def LoadTransactions(data_location: str, type_: str) -> List[FinalTransaction]:
        accepted_types = ["open", "confirmed", "mining"]
        if type_ not in accepted_types:
            raise ValueError(f"{type_} is not a supported transaction type")

        folder_name = f"{type_}_transactions"
        storage = Storage(Path(data_location))
        tx_files = storage.list_files(Path(folder_name))
        logger.debug("Found transactions: %s", tx_files)
        txs = []
        for f in tx_files:
            tx = storage.read_string(Path(folder_name) / f)
            if not tx:
                raise ValueError(
                    f"Found a file in {folder_name} folder that was not a transaction"
                )

            logger.debug("Found transaction: %s", f)
            txs.append(
                FinalTransaction(
                    transaction_hash=f,
                    transaction_id=f,
                    signed_transaction=SignedRawTransaction.ParseFromHex(tx),
                )
            )
        return txs

    @staticmethod
    def LoadAllTransactions(data_location: str) -> List[FinalTransaction]:
        all_txs = []
        for type_ in ["open", "confirmed", "mining"]:
            for tx in FinalTransaction.LoadTransactions(data_location, type_):
                all_txs.append(tx)
        return all_txs

    @staticmethod
    def FindTransaction(
        data_location: str, transaction_hash: str
    ) -> Optional[FinalTransaction]:
        storage = Storage(Path(data_location))
        for type_ in ["open", "confirmed", "mining"]:
            tx = storage.read_string(Path(f"{type_}_transactions") / transaction_hash)
            if tx is None:
                continue
            return FinalTransaction(
                transaction_hash=transaction_hash,
                transaction_id=transaction_hash,
                signed_transaction=SignedRawTransaction.ParseFromHex(tx),
            )
        return None

    @staticmethod
    def SaveTransaction(
        data_location: str, transaction: FinalTransaction, type_: str
    ) -> None:
        accepted_types = ["open", "mining"]
        if type_ not in accepted_types:
            raise ValueError(f"{type_} is not a supported transaction type")

        storage = Storage(Path(data_location) / f"{type_}_transactions")
        storage.save(
            Path(transaction.transaction_hash),
            transaction.signed_transaction.SerializeToHex(),
        )

    @staticmethod
    def MoveOpenTransactions(data_location: str) -> None:
        storage = Storage(Path(data_location))
        open_tx = storage.list_files(Path("open_transactions"))
        for tx in open_tx:
            storage.move_file(
                Path(data_location) / "open_transactions" / tx,
                Path(data_location) / "confirmed_transactions" / tx,
            )

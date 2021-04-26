from datetime import datetime

from typing import Any, Dict, List
from collections import OrderedDict

from pydantic import BaseModel

from transaction import Transaction


class Block(BaseModel):
    index: int
    timestamp: datetime
    transactions: List[Transaction]
    proof: int
    previous_hash: str

    def to_ordered_dict(self) -> Dict:
        """
        The order must be the same every single time. This is important because the hash
        will change if the order is different and it's imperative for the hash to be consistent
        """
        return dict(
            OrderedDict(
                [
                    ("index", self.index),
                    ("proof", self.proof),
                    ("previous_hash", self.previous_hash),
                    ("timestamp", self.date_to_string(self.timestamp)),
                    ("transactions", [t.to_ordered_dict() for t in self.transactions]),
                ]
            )
        )

    @staticmethod
    def date_of_string(date: str) -> datetime:
        return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f%z")

    @staticmethod
    def date_to_string(date: datetime) -> str:
        return datetime.strftime(date, "%Y-%m-%dT%H:%M:%S.%f%z")

    @staticmethod
    def generate_from_dict(block_dict: Dict) -> Any:
        return Block(
            proof=int(block_dict["proof"]),
            previous_hash=block_dict["previous_hash"],
            timestamp=Block.date_of_string(block_dict["timestamp"]),
            index=block_dict["index"],
            transactions=[
                Transaction(
                    sender=tx["sender"],
                    recipient=tx["recipient"],
                    signature=tx["signature"],
                    amount=tx["amount"],
                )
                for tx in block_dict["transactions"]
            ],
        )

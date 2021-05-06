from collections import OrderedDict
from typing import Dict, Optional
from pydantic import BaseModel


class Transaction(BaseModel):
    sender: str
    recipient: str
    amount: float
    nonce: int
    signature: Optional[str] = None

    def to_ordered_dict(self) -> Dict:
        """
        Converts the transaction into a hashable OrderedDict and then into a dictionary
        """
        return dict(
            OrderedDict(
                [
                    ("sender", self.sender),
                    ("recipient", self.recipient),
                    ("amount", self.amount),
                    ("nonce", self.nonce),
                    ("signature", self.signature),
                ]
            )
        )

from collections import OrderedDict
from typing import Dict, Optional
from pydantic import BaseModel


class Transaction(BaseModel):
    sender: str
    recipient: str
    amount: int
    signature: Optional[str] = "no_signature_provided"

    def dict(self) -> Dict:
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'signature': self.signature
        }

    # Converts the transaction into a hashable OrderedDict
    def to_ordered_dict(self):
        return OrderedDict([('sender', self.sender), ('recipient', self.recipient), ('amount', self.amount), ('signature', self.signature)])


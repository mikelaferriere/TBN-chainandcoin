import base64
from collections import OrderedDict
from typing import Dict, Optional
from pydantic import BaseModel

import rlp
import binascii

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

    def generate_tx_hash(self) -> str:
        args = [
            str(self.nonce).encode('ascii'),
            str("break").encode("ascii"),
            self.sender.encode('ascii'),
            str("break").encode("ascii"),
            self.recipient.encode('ascii'),
            str("break").encode("ascii"),
            str(self.amount).encode('ascii'),
            str("break").encode("ascii"),
        ]
        if self.signature is not None:
            args.append(self.signature)
        return rlp.rlp_encode(args)

    @staticmethod
    def unwrap_tx_hash(hash: bytes):
        decoded_rlp = rlp.rlp_decode(hash)
        return decoded_rlp

from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from pytz import timezone

from typing import Dict, List

from transaction import Transaction

from collections import OrderedDict

class Block(BaseModel):
    index: int
    timestamp: datetime
    transactions: List[Transaction]
    proof: int
    previous_hash: str

    def dict(self) -> Dict:
        """
        Overriding the `dict()` function so the order is the same every single time. This
        is important because the hash will change if the order is different and it's imperative
        for the hash to be consistent
        """
        return dict(OrderedDict([
            ('index', self.index),
            ('proof', self.proof),
            ('previous_hash', self.previous_hash),
            ('timestamp', date_to_string(self.timestamp)),
            ('transactions', [t.dict() for t in self.transactions]),
        ]))
        
def date_of_string(date: str) -> datetime:
    return datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f%z")

def date_to_string(date: datetime) -> str:
    return datetime.strftime(date, "%Y-%m-%d %H:%M:%S.%f%z")

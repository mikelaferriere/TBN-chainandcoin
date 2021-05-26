from datetime import datetime

from transaction import Details, SignedRawTransaction, convert_to_merkle
from wallet import Wallet


def test_merkle_happy_path():
    w1 = Wallet(test=True)
    w2 = Wallet(test=True)
    transactions = [
        SignedRawTransaction(
            details=Details(
                sender=w1.address,
                recipient=w2.address,
                amount=4.5,
                nonce=0,
                timestamp=datetime.utcnow(),
                public_key=w1.public_key.hex(),
            ),
            signature="sig",
        ),
        SignedRawTransaction(
            details=Details(
                sender=w2.address,
                recipient=w1.address,
                amount=1.87,
                nonce=0,
                timestamp=datetime.utcnow(),
                public_key=w2.public_key.hex(),
            ),
            signature="sig",
        ),
    ]

    m = convert_to_merkle(transactions)
    assert m.is_ready
    print(m.get_merkle_root())
    print(m.get_proof(0))
    SignedRawTransaction.ParseFromHex(m.get_proof(0)[0]["right"])
    print(m.get_proof(1))
    SignedRawTransaction.ParseFromHex(m.get_proof(1)[0]["left"])

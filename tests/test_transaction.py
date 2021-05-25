from datetime import datetime
import ecdsa

from transaction import Details, SignedRawTransaction
from wallet import Wallet


def test_transaction_to_protobuf_and_back():
    timestamp = datetime.utcfromtimestamp(0)

    t = SignedRawTransaction(
        details=Details(
            sender="test",
            recipient="test2",
            amount=4.5,
            nonce=0,
            timestamp=timestamp,
            public_key="pub_key",
        ),
        signature="sig",
    )
    t_hex = t.SerializeToHex()

    assert (
        t_hex
        == "0a230a04746573741205746573743219000000000000124020002a0032077075625f6b65791203736967"
    )

    parsed_t = SignedRawTransaction.ParseFromHex(t_hex)

    assert parsed_t == t


def test_transaction_with_signature_to_protobuf_and_back():
    w = Wallet(test=True)
    w2 = Wallet(test=True)

    timestamp = datetime.utcfromtimestamp(0)

    d = Details(
        sender=w.address,
        recipient=w2.address,
        amount=4.5,
        nonce=0,
        timestamp=timestamp,
        public_key=w.public_key.hex(),
    )

    t = w.sign_transaction(d)

    t_hex = t.SerializeToHex()

    parsed_t = SignedRawTransaction.ParseFromHex(t_hex)

    assert parsed_t == t
    assert w.verify_transaction(t)


def test_transaction_fails_validation():
    w = Wallet(test=True)
    w2 = Wallet(test=True)

    timestamp = datetime.utcfromtimestamp(0)

    d = Details(
        sender=w.address,
        recipient=w2.address,
        amount=4.5,
        nonce=0,
        timestamp=timestamp,
        public_key=w.public_key.hex(),
    )

    t = w.sign_transaction(d)

    t_hex = t.SerializeToHex()

    parsed_t = SignedRawTransaction.ParseFromHex(t_hex)

    assert parsed_t == t
    assert w.verify_transaction(t)

    t.details.amount = 2.5
    try:
        w.verify_transaction(t)
        raise Exception("Expected to fail but did not")
    except ecdsa.keys.BadSignatureError:
        assert True

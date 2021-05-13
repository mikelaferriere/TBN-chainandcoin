import ecdsa

from transaction import Transaction
from wallet import Wallet


def test_transaction_to_protobuf_and_back():
    t = Transaction(
        sender="test",
        recipient="test2",
        amount=4.5,
        nonce=0,
        public_key="pub_key",
        signature=None,
    )
    t_hex = t.SerializeToString().hex()

    assert t_hex == "0a0474657374120574657374321d00009040280032077075625f6b6579"

    parsed_t = Transaction.ParseFromString(bytes.fromhex(t_hex))

    assert parsed_t == t


def test_transaction_with_signature_to_protobuf_and_back():
    w = Wallet(test=True)
    w2 = Wallet(test=True)

    t = Transaction(
        sender=w.address,
        recipient=w2.address,
        amount=4.5,
        nonce=0,
        public_key=w.public_key.hex(),
        signature=None,
    )

    signature = w.sign_transaction(t)
    t.signature = signature

    t_hex = t.SerializeToString().hex()

    parsed_t = Transaction.ParseFromString(bytes.fromhex(t_hex))

    assert parsed_t == t
    assert signature == t.signature
    assert w.verify_transaction(t)


def test_transaction_fails_validation():
    w = Wallet(test=True)
    w2 = Wallet(test=True)

    t = Transaction(
        sender=w.address,
        recipient=w2.address,
        amount=4.5,
        nonce=0,
        public_key=w.public_key.hex(),
        signature=None,
    )

    signature = w.sign_transaction(t)
    t.signature = signature

    t_hex = t.SerializeToString().hex()

    parsed_t = Transaction.ParseFromString(bytes.fromhex(t_hex))

    assert parsed_t == t
    assert signature == t.signature
    assert w.verify_transaction(t)

    t.amount = 2.5
    try:
        w.verify_transaction(t)
        raise Exception("Expected to fail but did not")
    except ecdsa.keys.BadSignatureError:
        assert True

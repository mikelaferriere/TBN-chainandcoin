from generated.transaction_pb2 import Transaction  # type: ignore
from walletv2 import Wallet


def test_transaction_to_protobuf_and_back():
    t = Transaction(sender="test", recipient="test2", amount=4.5)

    t_hex = t.SerializeToString().hex()

    assert t_hex == "0a0474657374120574657374321d00009040"

    parsed_t = Transaction()
    parsed_t.ParseFromString(bytes.fromhex(t_hex))

    assert parsed_t == t


def test_transaction_with_signature_to_protobuf_and_back():
    w = Wallet(test=True)
    w2 = Wallet(test=True)

    t = Transaction(sender=w.address, recipient=w2.address, amount=4.5)

    signature = w.sign_transaction(w.address, w2.address, 4.5)
    t.signature = signature

    t_hex = t.SerializeToString().hex()

    parsed_t = Transaction()
    parsed_t.ParseFromString(bytes.fromhex(t_hex))

    assert parsed_t == t
    assert signature == t.signature
    assert w.verify_transaction(t)


def test_transaction_fails_validation():
    w = Wallet(test=True)
    w2 = Wallet(test=True)

    t = Transaction(sender=w.address, recipient=w2.address, amount=4.5)

    signature = w.sign_transaction(w.address, w2.address, 4.5)
    t.signature = signature

    t_hex = t.SerializeToString().hex()

    parsed_t = Transaction()
    parsed_t.ParseFromString(bytes.fromhex(t_hex))

    assert parsed_t == t
    assert signature == t.signature
    assert w.verify_transaction(t)

    t.amount = 2.5
    assert not w.verify_transaction(t)

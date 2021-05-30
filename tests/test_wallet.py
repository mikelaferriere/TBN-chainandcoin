from datetime import datetime
from uuid import uuid4

from blockchain import Blockchain
from custom_exceptions import InvalidNonceError
from transaction import Details
from wallet import Wallet


def test_multiple_transaction_happy_path():
    node_id = uuid4()
    w = Wallet(test=True)
    w2 = Wallet(test=True)
    chain = Blockchain(w.address, node_id, difficulty=1, is_test=True)
    chain.mine_block()

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
    chain.add_transaction(t)

    d.nonce = 1
    t2 = w.sign_transaction(d)
    chain.add_transaction(t2)


def test_nonce_should_be_exactly_previous_plus_1():
    node_id = uuid4()
    w = Wallet(test=True)
    w2 = Wallet(test=True)
    chain = Blockchain(w.address, node_id, difficulty=1, is_test=True)
    chain.mine_block()

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

    chain.add_transaction(t)
    try:
        d.nonce = 2
        t2 = w.sign_transaction(d)
        chain.add_transaction(t2)
        raise ValueError("Double spending transaction should fail, but didn't")
    except InvalidNonceError:
        pass


def test_double_spending_fails():
    node_id = uuid4()
    w = Wallet(test=True)
    w2 = Wallet(test=True)
    chain = Blockchain(w.address, node_id, difficulty=1, is_test=True)
    chain.mine_block()

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

    chain.add_transaction(t)
    try:
        chain.add_transaction(t)
        raise ValueError("Double spending transaction should fail, but didn't")
    except InvalidNonceError:
        pass

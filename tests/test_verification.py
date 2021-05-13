from datetime import datetime

from block import Block
from transaction import Transaction
from verification import Verification


def test_block_hash_happy_path():
    timestamp = datetime.fromtimestamp(0)

    block = Block(
        index=0,
        timestamp=timestamp,
        transaction_count=0,
        transactions=[],
        nonce=100,
        previous_hash="",
        difficulty=4,
        version="0.1",
    )

    # Just asserting that an error is not thrown when hashing the block
    Verification.hash_block(block)


def test_block_hash_mutliple_transaction_field_order_doesnt_matter():
    timestamp = datetime.fromtimestamp(0)

    block = Block(
        index=0,
        timestamp=timestamp,
        transaction_count=2,
        transactions=[
            Transaction(
                sender="test",
                recipient="test2",
                amount=5.0,
                nonce=0,
                signature=None,
                public_key="pub_key",
            ),
            Transaction(
                sender="test2",
                recipient="test",
                amount=2.5,
                nonce=0,
                signature=None,
                public_key="pub_key",
            ),
        ],
        nonce=100,
        previous_hash="",
        difficulty=4,
        version="0.1",
    )

    first_hash = Verification.hash_block(block)

    block = Block(
        index=0,
        timestamp=timestamp,
        transaction_count=2,
        transactions=[
            Transaction(
                recipient="test2",
                amount=5.0,
                sender="test",
                nonce=0,
                signature=None,
                public_key="pub_key",
            ),
            Transaction(
                amount=2.5,
                sender="test2",
                signature=None,
                nonce=0,
                recipient="test",
                public_key="pub_key",
            ),
        ],
        nonce=100,
        previous_hash="",
        difficulty=4,
        version="0.1",
    )

    second_hash = Verification.hash_block(block)

    assert first_hash == second_hash


def test_correct_nonce():
    timestamp = datetime.fromtimestamp(0)

    block_one = Block(
        index=0,
        timestamp=timestamp,
        transaction_count=0,
        transactions=[],
        nonce=100,
        previous_hash="",
        difficulty=4,
        version="0.1",
    )

    previous_hash = Verification.hash_block(block_one)

    open_transactions = [
        Transaction(
            sender="test2",
            recipient="test",
            amount=2.5,
            nonce=0,
            signature=None,
            public_key="pub_key",
        )
    ]

    nonce = Verification.proof_of_work(block_one, open_transactions, 4)

    timestamp = datetime.fromtimestamp(1)

    block_two = Block(
        index=1,
        timestamp=timestamp,
        transaction_count=len(open_transactions),
        transactions=open_transactions,
        nonce=nonce,
        previous_hash=previous_hash,
        difficulty=4,
        version="0.1",
    )

    assert Verification.valid_nonce(
        block_two.nonce, block_two.transactions, block_two.previous_hash, 4
    )

from datetime import datetime

from block import Block, Header
from transaction import Transaction
from verification import Verification


def test_all_values_result_in_64_characters():

    short_str = "a short string"

    assert len(short_str) < 64
    assert len(Verification.hash_bytes_256(short_str.encode("utf-8"))) == 64

    long_str = (
        "a longer than 64 character string in order to test to make sure that"
        "the result of the hash is still only 64 characters exactly"
    )

    assert len(long_str) > 64
    assert len(Verification.hash_bytes_256(long_str.encode("utf-8"))) == 64


def test_block_hash_happy_path():
    timestamp = datetime.utcfromtimestamp(0)

    block = Block(
        index=0,
        header=Header(
            timestamp=timestamp,
            transaction_merkle_root="",
            nonce=100,
            previous_hash="",
            difficulty=4,
            version=1,
        ),
        transaction_count=0,
        transactions=[],
    )

    # Just asserting that an error is not thrown when hashing the block
    Verification.hash_block(block)


def test_block_hash_mutliple_transaction_field_order_doesnt_matter():
    timestamp = datetime.utcfromtimestamp(0)

    transactions = [
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
    ]

    tx_merkle_root = Transaction.get_merkle_root(transactions)

    block = Block(
        index=0,
        header=Header(
            timestamp=timestamp,
            transaction_merkle_root=tx_merkle_root,
            nonce=100,
            previous_hash="",
            difficulty=4,
            version=1,
        ),
        transaction_count=2,
        transactions=transactions,
    )

    first_hash = Verification.hash_block(block)

    block = Block(
        index=0,
        header=Header(
            timestamp=timestamp,
            transaction_merkle_root=tx_merkle_root,
            nonce=100,
            previous_hash="",
            difficulty=4,
            version=1,
        ),
        transaction_count=2,
        transactions=transactions,
    )

    second_hash = Verification.hash_block(block)

    assert first_hash == second_hash


def test_correct_nonce():
    timestamp = datetime.utcfromtimestamp(0)

    block_one = Block(
        index=0,
        header=Header(
            timestamp=timestamp,
            transaction_merkle_root="",
            nonce=100,
            previous_hash="",
            difficulty=4,
            version=1,
        ),
        transaction_count=0,
        transactions=[],
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

    block_header = Header(
        version=1,
        difficulty=4,
        timestamp=datetime.utcfromtimestamp(1),
        transaction_merkle_root=Transaction.get_merkle_root(open_transactions),
        previous_hash=previous_hash,
        nonce=0,
    )

    block_header = Verification.proof_of_work(block_header)

    block_two = Block(
        index=1,
        header=block_header,
        transaction_count=len(open_transactions),
        transactions=open_transactions,
    )

    assert Verification.valid_nonce(block_two.header)

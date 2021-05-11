from google.protobuf.timestamp_pb2 import Timestamp

from generated.block_pb2 import Block
from generated.transaction_pb2 import Transaction
from verification import Verification


def test_block_hash_happy_path():
    timestamp = Timestamp()
    timestamp.GetCurrentTime()

    block = Block(
        index=0,
        timestamp=timestamp,
        transactions=[],
        nonce=100,
        previous_hash="",
    )

    # Just asserting that an error is not thrown when hashing the block
    Verification.hash_block(block)


def test_block_hash_mutliple_transaction_field_order_doesnt_matter():
    timestamp = Timestamp()
    timestamp.GetCurrentTime()

    block = Block(
        index=0,
        timestamp=timestamp,
        transactions=[
            Transaction(
                sender="test", recipient="test2", amount=5.0, nonce=0, signature=""
            ),
            Transaction(
                sender="test2", recipient="test", amount=2.5, nonce=0, signature=""
            ),
        ],
        nonce=100,
        previous_hash="",
    )

    first_hash = Verification.hash_block(block)

    block = Block(
        index=0,
        timestamp=timestamp,
        transactions=[
            Transaction(
                recipient="test2", amount=5.0, sender="test", nonce=0, signature=""
            ),
            Transaction(
                amount=2.5, sender="test2", signature="", nonce=0, recipient="test"
            ),
        ],
        nonce=100,
        previous_hash="",
    )

    second_hash = Verification.hash_block(block)

    assert first_hash == second_hash


def test_correct_nonce():
    timestamp = Timestamp()
    timestamp.GetCurrentTime()

    block_one = Block(
        index=0,
        timestamp=timestamp,
        transactions=[],
        nonce=100,
        previous_hash="",
    )

    previous_hash = Verification.hash_block(block_one)

    open_transactions = [
        Transaction(sender="test2", recipient="test", amount=2.5, nonce=0, signature="")
    ]

    nonce = Verification.proof_of_work(block_one, open_transactions, 4)

    timestamp.GetCurrentTime()

    block_two = Block(
        index=1,
        timestamp=timestamp,
        transactions=open_transactions,
        nonce=nonce,
        previous_hash=previous_hash,
    )

    assert Verification.valid_nonce(
        block_two.nonce, block_two.transactions, block_two.previous_hash, 4
    )

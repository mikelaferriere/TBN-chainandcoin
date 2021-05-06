from time import time

from block import Block
from transaction import Transaction
from verification import Verification


def test_block_hash_happy_path():
    block = Block(
        index=0,
        timestamp=0,
        transactions=[],
        nonce=100,
        previous_hash="",
    )

    hash_ = Verification.hash_block(block)


def test_block_hash_mutliple_transaction_field_order_doesnt_matter():
    block = Block(
        index=0,
        timestamp=0,
        transactions=[
            Transaction(sender="test", recipient="test2", amount=5.0, signature=""),
            Transaction(sender="test2", recipient="test", amount=2.5, signature=""),
        ],
        nonce=100,
        previous_hash="",
    )

    first_hash = Verification.hash_block(block)

    block = Block(
        index=0,
        timestamp=0,
        transactions=[
            Transaction(recipient="test2", amount=5.0, sender="test", signature=""),
            Transaction(amount=2.5, sender="test2", signature="", recipient="test"),
        ],
        nonce=100,
        previous_hash="",
    )

    second_hash = Verification.hash_block(block)

    assert first_hash == second_hash


def test_correct_nonce():
    block_one = Block(
        index=0,
        timestamp=0,
        transactions=[],
        nonce=100,
        previous_hash="",
    )

    previous_hash = Verification.hash_block(block_one)

    open_transactions = [
        Transaction(sender="test2", recipient="test", amount=2.5, signature="")
    ]

    nonce = Verification.proof_of_work(block_one, open_transactions, 4)

    block_two = Block(
        index=1,
        timestamp=time(),
        transactions=open_transactions,
        nonce=nonce,
        previous_hash=previous_hash,
    )

    assert Verification.valid_nonce(
        block_two.nonce, block_two.transactions, block_two.previous_hash, 4
    )

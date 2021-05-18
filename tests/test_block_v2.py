from datetime import datetime

from block import BlockV2
from block import Header
from transaction import Transaction


def test_block_format():
    timestamp = datetime.utcfromtimestamp(0).timestamp()
    transactions = []

    BlockV2(
        index=0,
        header=Header(
            version=1,
            previous_hash="",
            timestamp=timestamp,
            transaction_merkle_root=Transaction.get_merkle_root(transactions),
            difficulty=4,
            nonce=100,
        ),
        transaction_count=len(transactions),
        transactions=transactions,
    )


def test_block_to_protobuf_and_back():
    timestamp = datetime.utcfromtimestamp(0)
    transactions = []

    header = Header(
        version=1,
        previous_hash="",
        timestamp=timestamp,
        transaction_merkle_root=Transaction.get_merkle_root(transactions),
        difficulty=4,
        nonce=100,
    )

    block = BlockV2(
        index=0,
        header=header,
        transaction_count=len(transactions),
        transactions=transactions,
    )

    p_block = block.SerializeToHex()
    assert p_block == "08001000220c080112001a002200280430642800"

    og_block = BlockV2.ParseFromHex(p_block)

    assert og_block == BlockV2(
        index=0,
        block_hash="",
        size=0,
        header=Header(
            version=1,
            previous_hash="",
            timestamp=timestamp,
            transaction_merkle_root=Transaction.get_merkle_root(transactions),
            difficulty=4,
            nonce=100,
        ),
        transaction_count=len(transactions),
        transactions=transactions,
    )


def test_block_to_protobuf_and_back_with_transactions():
    timestamp = datetime.utcfromtimestamp(0)
    transactions = [
        Transaction(
            sender="test",
            recipient="test2",
            amount=4.5,
            nonce=0,
            public_key="pub_key",
            signature=None,
        )
    ]

    header = Header(
        version=1,
        previous_hash="",
        timestamp=timestamp,
        transaction_merkle_root=Transaction.get_merkle_root(transactions),
        difficulty=4,
        nonce=100,
    )

    block = BlockV2(
        index=0,
        header=header,
        transaction_count=len(transactions),
        transactions=transactions,
    )

    p_block = block.SerializeToHex()
    assert (
        p_block
        == "08001000224e080112001a42306130343734363537333734313230353734363537333734333231393030303030303030303030303132343032383030333230373730373536323566366236353739220028043064280132210a047465737412057465737432190000000000001240280032077075625f6b6579"  # noqa: E501
    )

    og_block = BlockV2.ParseFromHex(p_block)

    assert og_block == BlockV2(
        index=0,
        block_hash="",
        size=0,
        header=Header(
            version=1,
            previous_hash="",
            timestamp=timestamp,
            transaction_merkle_root=Transaction.get_merkle_root(transactions),
            difficulty=4,
            nonce=100,
        ),
        transaction_count=len(transactions),
        transactions=transactions,
    )

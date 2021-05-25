from datetime import datetime

from block import Block
from block import Header
from transaction import Details, FinalTransaction, SignedRawTransaction, get_merkle_root


def test_block_format():
    timestamp = datetime.utcfromtimestamp(0)
    transactions = []

    Block(
        index=0,
        block_hash="",
        size=0,
        header=Header(
            version=1,
            previous_hash="",
            timestamp=timestamp,
            transaction_merkle_root=get_merkle_root(transactions),
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
        transaction_merkle_root=get_merkle_root(transactions),
        difficulty=4,
        nonce=100,
    )

    block = Block(
        index=0,
        block_hash="",
        size=0,
        header=header,
        transaction_count=len(transactions),
        transactions=transactions,
    )

    p_block = block.SerializeToHex()
    assert p_block == "080010001a00220c080112001a002200280430642800"

    og_block = Block.ParseFromHex(p_block)

    assert og_block == Block(
        index=0,
        block_hash="",
        size=0,
        header=Header(
            version=1,
            previous_hash="",
            timestamp=timestamp,
            transaction_merkle_root=get_merkle_root(transactions),
            difficulty=4,
            nonce=100,
        ),
        transaction_count=len(transactions),
        transactions=transactions,
    )


def test_block_to_protobuf_and_back_with_transactions():
    timestamp = datetime.utcfromtimestamp(0)
    transactions = [
        FinalTransaction(
            transaction_hash="tx_hash_1",
            transaction_id="tx_hash_1",
            signed_transaction=SignedRawTransaction(
                details=Details(
                    sender="test",
                    recipient="test2",
                    amount=4.5,
                    nonce=0,
                    timestamp=timestamp,
                    public_key="pub_key",
                ),
                signature="sig",
            ),
        )
    ]

    header = Header(
        version=1,
        previous_hash="",
        timestamp=timestamp,
        transaction_merkle_root=get_merkle_root(
            [t.signed_transaction for t in transactions]
        ),
        difficulty=4,
        nonce=100,
    )

    block = Block(
        index=0,
        block_hash="",
        size=0,
        header=header,
        transaction_count=len(transactions),
        transactions=[t.transaction_hash for t in transactions],
    )

    p_block = block.SerializeToHex()
    assert (
        p_block
        == "080010001a002260080112001a543061323330613034373436353733373431323035373436353733373433323139303030303030303030303030313234303230303032613030333230373730373536323566366236353739313230333733363936372200280430642801320974785f686173685f31"  # noqa: E501
    )

    og_block = Block.ParseFromHex(p_block)

    assert og_block == Block(
        index=0,
        block_hash="",
        size=0,
        header=Header(
            version=1,
            previous_hash="",
            timestamp=timestamp,
            transaction_merkle_root=get_merkle_root(
                [t.signed_transaction for t in transactions]
            ),
            difficulty=4,
            nonce=100,
        ),
        transaction_count=len(transactions),
        transactions=[t.transaction_hash for t in transactions],
    )

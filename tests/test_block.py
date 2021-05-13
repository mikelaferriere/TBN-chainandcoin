from datetime import datetime
from uuid import uuid4

from block import Block
from blockchain import Blockchain
from wallet import Wallet


def test_block_format():
    node_id = uuid4()
    w = Wallet(test=True)
    chain = Blockchain(w.address, node_id)

    timestamp = datetime.fromtimestamp(0)
    genesis_block = chain.last_block
    genesis_block.timestamp = timestamp

    assert genesis_block == Block(
        index=0,
        nonce=100,
        previous_hash="",
        timestamp=timestamp,
        transaction_count=0,
        transactions=[],
        difficulty=4,
        version="0.1",
    )


def test_block_to_protobuf_and_back():
    node_id = uuid4()
    w = Wallet(test=True)
    chain = Blockchain(w.address, node_id)

    timestamp = datetime.fromtimestamp(0)
    genesis_block = chain.last_block
    genesis_block.timestamp = timestamp

    assert genesis_block == Block(
        index=0,
        nonce=100,
        previous_hash="",
        timestamp=timestamp,
        transaction_count=0,
        transactions=[],
        difficulty=4,
        version="0.1",
    )

    p_genesis_block = genesis_block.SerializeToString().hex()
    assert p_genesis_block == "0800120b08b0f3feffffffffffff0118002864320038044203302e31"

    og_genesis_block = Block.ParseFromString(bytes.fromhex(p_genesis_block))

    assert og_genesis_block == Block(
        index=0,
        nonce=100,
        previous_hash="",
        timestamp=timestamp,
        transaction_count=0,
        transactions=[],
        difficulty=4,
        version="0.1",
    )

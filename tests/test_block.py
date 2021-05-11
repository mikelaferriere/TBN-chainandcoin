from uuid import uuid4

from generated.block_pb2 import Block  # type: ignore
from blockchain import Blockchain
from wallet import Wallet


def test_block_format():
    node_id = uuid4()
    w = Wallet(test=True)
    chain = Blockchain(w.address, node_id)

    genesis_block = chain.last_block

    assert genesis_block == Block(
        index=0, nonce=100, previous_hash="", difficulty=4, version="0.1"
    )


def test_block_to_protobuf_and_back():
    node_id = uuid4()
    w = Wallet(test=True)
    chain = Blockchain(w.address, node_id)

    genesis_block = chain.last_block

    assert genesis_block == Block(
        index=0, nonce=100, previous_hash="", difficulty=4, version="0.1"
    )

    p_genesis_block = genesis_block.SerializeToString().hex()
    assert p_genesis_block == "286438044203302e31"

    og_genesis_block = Block()
    og_genesis_block.ParseFromString(bytes.fromhex(p_genesis_block))

    assert og_genesis_block == Block(
        index=0, nonce=100, previous_hash="", difficulty=4, version="0.1"
    )

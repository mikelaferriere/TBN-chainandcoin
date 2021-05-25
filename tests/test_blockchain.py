from datetime import datetime
from uuid import uuid4

from blockchain import Blockchain
from transaction import Details
from verification import Verification
from wallet import Wallet


def test_blockchain_constructor():
    Blockchain("node_id", "private_key")


def test_mining_block():
    node_id = uuid4()
    w = Wallet(test=True)
    chain = Blockchain(w.address, node_id, is_test=True)
    assert Verification.verify_chain(chain.chain)
    chain.mine_block()
    assert Verification.verify_chain(chain.chain)
    chain.mine_block()
    assert Verification.verify_chain(chain.chain)


def test_mining_block_with_open_transactions():
    timestamp = datetime.utcfromtimestamp(0)
    node_id = uuid4()
    w1 = Wallet(test=True)
    w2 = Wallet(test=True)

    chain = Blockchain(w1.address, node_id, is_test=True)

    tx_details_1 = Details(
        sender=w1.address,
        recipient=w2.address,
        nonce=0,
        amount=0.5,
        timestamp=timestamp,
        public_key=w1.public_key.hex(),
    )
    transaction_1 = w1.sign_transaction(tx_details_1)

    tx_details_2 = Details(
        sender=w2.address,
        recipient=w1.address,
        nonce=0,
        amount=0.5,
        timestamp=timestamp,
        public_key=w2.public_key.hex(),
    )
    transaction_2 = w2.sign_transaction(tx_details_2)

    assert Verification.verify_chain(chain.chain)
    # Need to give the w1 at least 1.0 coin in their balance
    chain.mine_block()
    assert Verification.verify_chain(chain.chain)
    chain.add_transaction(transaction_1, is_receiving=True)
    chain.mine_block()
    assert Verification.verify_chain(chain.chain)
    chain_transactions = []
    for block in chain.chain:
        for tx in block.transactions:
            chain_transactions.append(tx)
    assert Verification.hash_transaction(transaction_1) in chain_transactions
    chain.add_transaction(transaction_2, is_receiving=True)
    chain.mine_block()
    chain_transactions = []
    for block in chain.chain:
        for tx in block.transactions:
            chain_transactions.append(tx)
    assert Verification.hash_transaction(transaction_2) in chain_transactions


def test_broadcasting_block():
    timestamp = datetime.utcfromtimestamp(0)
    node_id = uuid4()
    w1 = Wallet(test=True)
    w2 = Wallet(test=True)

    chain1 = Blockchain(w1.address, node_id, is_test=True)
    chain2 = Blockchain(w2.address, node_id, is_test=True)

    chain2.chain = chain1.chain
    assert chain1.chain == chain2.chain

    tx_details_1 = Details(
        sender=w1.address,
        recipient=w2.address,
        nonce=0,
        amount=0.5,
        timestamp=timestamp,
        public_key=w1.public_key.hex(),
    )
    transaction_1 = w1.sign_transaction(tx_details_1)

    assert Verification.verify_chain(chain1.chain)
    b = chain1.mine_block()

    result, _ = chain2.add_block(b)
    assert result

    assert Verification.verify_chain(chain1.chain)
    assert Verification.verify_chain(chain2.chain)

    chain1.add_transaction(transaction_1, is_receiving=True)
    chain2.add_transaction(transaction_1, is_receiving=True)
    chain1.mine_block()
    chain2.add_block(chain1.last_block)

    assert Verification.verify_chain(chain1.chain)
    assert Verification.verify_chain(chain2.chain)

    assert chain1.chain == chain2.chain


def test_not_enough_coin():
    timestamp = datetime.utcfromtimestamp(0)
    node_id = uuid4()
    w = Wallet(test=True)
    w2 = Wallet(test=True)
    chain = Blockchain(w.address, node_id, is_test=True)
    tx_details = Details(
        sender=w.address,
        recipient=w2.address,
        nonce=0,
        amount=2995.0,
        timestamp=timestamp,
        public_key=w.public_key.hex(),
    )
    transaction = w.sign_transaction(tx_details)

    assert Verification.verify_chain(chain.chain)
    try:
        chain.add_transaction(transaction, is_receiving=True)
        assert "This was expected to throw a ValueError exception but didn't"
    except ValueError:
        pass

from uuid import uuid4

from blockchain import Blockchain
from generated.transaction_pb2 import Transaction  # type: ignore
from verification import Verification
from wallet import Wallet


def test_blockchain_constructor():
    Blockchain("node_id", "private_key")


def test_mining_block():
    node_id = uuid4()
    w = Wallet(test=True)
    chain = Blockchain(w.address, node_id)
    assert Verification.verify_chain(chain.chain)
    chain.mine_block()
    assert Verification.verify_chain(chain.chain)
    chain.mine_block()
    assert Verification.verify_chain(chain.chain)


def test_mining_block_with_open_transactions():
    node_id = uuid4()
    w1 = Wallet(test=True)
    w2 = Wallet(test=True)

    chain = Blockchain(w1.address, node_id)

    transaction_1 = Transaction(
        sender=w1.address,
        recipient=w2.address,
        nonce=0,
        amount=0.5,
        public_key=w1.public_key.hex(),
    )
    transaction_1.signature = w1.sign_transaction(transaction_1)

    transaction_2 = Transaction(
        sender=w2.address,
        recipient=w1.address,
        nonce=0,
        amount=0.5,
        public_key=w2.public_key.hex(),
    )
    transaction_2.signature = w2.sign_transaction(transaction_2)

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
    assert transaction_1 in chain_transactions
    chain.add_transaction(transaction_2, is_receiving=True)
    chain.mine_block()
    chain_transactions = []
    for block in chain.chain:
        for tx in block.transactions:
            chain_transactions.append(tx)
    assert transaction_2 in chain_transactions


def test_not_enough_coin():
    node_id = uuid4()
    w = Wallet(test=True)
    w2 = Wallet(test=True)
    chain = Blockchain(w.address, node_id)
    transaction = Transaction(
        sender=w.address,
        recipient=w2.address,
        nonce=0,
        amount=0.5,
        public_key=w.public_key.hex(),
    )
    transaction.signature = w.sign_transaction(transaction)

    assert Verification.verify_chain(chain.chain)
    try:
        chain.add_transaction(transaction, is_receiving=True)
        assert "This was expected to throw a ValueError exception but didn't"
    except ValueError:
        pass

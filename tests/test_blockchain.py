from uuid import uuid4

from blockchain import Blockchain
from transaction import Transaction
from verification import Verification
from wallet import Wallet


def test_blockchain_constructor():
    Blockchain("node_id", "private_key")


def test_mining_block():
    node_id = uuid4()
    node_id_str = str(node_id)
    w = Wallet(node_id)
    private_key, public_key = w.generate_keys()
    chain = Blockchain(node_id_str, public_key)
    assert Verification.verify_chain(chain.chain)
    chain.mine_block()
    assert Verification.verify_chain(chain.chain)
    chain.mine_block()
    assert Verification.verify_chain(chain.chain)


def test_mining_block_with_open_transactions():
    node_id = uuid4()
    node_id_str = str(node_id)
    w1 = Wallet(node_id)
    w2 = Wallet(node_id)
    w1.create_keys()
    w2.create_keys()

    transaction_1 = Transaction(
        sender=w1.public_key, recipient=w2.public_key, signature="", amount=1.5
    )

    signature_1 = w1.sign_transaction(w1.public_key, w2.public_key, 1.5)
    transaction_1.signature = signature_1

    transaction_2 = Transaction(
        sender=w2.public_key, recipient=w1.public_key, signature="newsig", amount=0.5
    )

    signature_2 = w2.sign_transaction(w2.public_key, w1.public_key, 0.5)
    transaction_2.signature = signature_2

    chain = Blockchain(node_id_str, w1.public_key)
    assert Verification.verify_chain(chain.chain)
    # Need to give the public_key_1 at least 1.0 coin in their balance
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

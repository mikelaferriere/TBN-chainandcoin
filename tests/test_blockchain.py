from uuid import uuid4

from blockchain import Blockchain
from transaction import Transaction
from verification import Verification
from walletv2 import Wallet


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

    transaction_1 = Transaction(sender=w1.address, recipient=w2.address, amount=1.5)

    print(w1.private_key)
    signature_1 = w1.sign_transaction(w1.address, w2.address, 1.5)
    transaction_1.signature = signature_1

    transaction_2 = Transaction(sender=w2.address, recipient=w1.address, amount=0.5)

    signature_2 = w2.sign_transaction(w2.address, w1.address, 0.5)
    transaction_2.signature = signature_2

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

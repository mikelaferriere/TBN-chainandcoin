# Blockchain README

This initial implementation is a pretty simple straightforward representation of a blockchain.
It uses Proof of Work (PoW), which means that it can be mined and uses machine power to validate
and create the chain. We may want to later use Proof of Stake (PoS) which should reduce
transaction fees, time and energy, but requires people to believe in the product before any it
produces any value.


# Install Blockchain deps
```
make pip
```

# Play with the node

Currently, the blockchain can be run a couple different ways.

It can be run by itself, as a a singleton. This will create a local blockchain, where no
network syncing occurs, and you will be able to create and mine without worry about
transaction validity.

It can also be run synced with the network masternode. This will first pull down the chain
from the network, and then your node will sync with the masternode when you create new
transactions and/or mine new blocks.


# Start the node
```
$ python3 node_console.py
```

**NOTE: The first thing that the console will ask you is for your wallet password. If you have not
created a wallet yet, read through and follow the steps in WALLET.md**

After you have logged into your wallet, you will be asked to sync or not sync your chain with
the network.

After you decide your syncing option, you will be presented with a variety of options to
interact with the blockchain. Have Fun!


## Mining

Mining is the act of adding a block to the blockchain. It will always create a new block with
a sender "0", and the recipient is the miners address. The amount is currently 1 coin. Any
pending transactions are also committed to the chain in the Block


## Interesting Notes

1. Notice, that if you check the chain after you create a new transaction, your transaction
   will not appear in the chain. This is because we are using PoW, so we need the miners to
   "validate"the transaction. So don't forget to mine the block after you create a new transaction.

2. You will not be able to create a transaction if you do not have the balance to do so. For now,
   you can just mine a block first, which will award you 1 coin.

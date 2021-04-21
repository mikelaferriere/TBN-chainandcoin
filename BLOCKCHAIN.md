# Blockchain README

This initial implementation is a pretty simple straightforward representation of a blockchain.
It uses Proof of Work (PoW), which means that it can be mined and uses machine power to validate
and create the chain. We may want to later use Proof of Stake (PoS) which should reduce
transaction fees, but requires people to believe in the product before any it produces any value.



# Install Blockchain deps
```
make pip
```

# Run blockchain node
```
make run
```


# Play with the node

Currently, the blockchain is a singleton initated when the node is started. This will probably
change down the line, but it is more than enough to go on for the initial prototype.

There are a few things to do with the chain once the node is running. By running `make run`,
the api will be running on `http://localhost:5000`

**NOTE: I pipe the curl command to `jq` in order to format the output into something human
readable**


## Check the chain

We can observe the chain at any given time by running:
```
$ curl localhost:5000/chain | jq .
```

## Add a new transaction to the chain

Adding a new transaction is a POST which requires 3 fields; sender, recipient, and amount.

```
$ curl -X POST -H "Content-Type: application/json" localhost:5000/transactions/new -d '{"sender": "newuser", "recipient": "otheruser", "amount": 5}' | jq .
```

**NOTE: When making POST requests, don't forget to add `-H "Content-Type: application/json"`
to the header.**


Notice, that if you check the chain after you create a new transaction, your transaction
will not appear in the chain. This is because we are using PoW, so we need the miners to "validate"
the transaction. So lets mine the block onto the chain!

## Mining

Mining is the act of adding a block to the blockchain. It will always create a new block with
a sender "0", and the recipient is the miners address. The amount is currently 1 coin. Any
pending transactions are also committed to the chain in the Block

```
$ curl -XPOST -H "Content-Type: application/json" localhost:5000/mine -d '{"miner_address": "SomeAddress"}' | jq .
```

If you mine when there is no pending transactions, you can expect a response like:
```
{
  "index": 4,
  "message": "New Block Forged",
  "previous_hash": "24d2855558ca38df196d97b6065a5fa9f4c9d0e6ec8df3ee6935452df2a3cb87",
  "proof": 119678,
  "transactions": [
    {
      "amount": 1,
      "recipient": "SomeAddress",
      "sender": "0"
    }
  ]
}
```

If there is a pending transaction waiting to be approved, it will be reflected in the 'transactions'
field:
```
{
  "index": 5,
  "message": "New Block Forged",
  "previous_hash": "71819302f451146072fa507dd5b28bdfe546c0ad37adf3f0cbfddb733ac08b4d",
  "proof": 146502,
  "transactions": [
    {
      "amount": 5,
      "recipient": "otheruser2",
      "sender": "newuser"
    },
    {
      "amount": 1,
      "recipient": "322e032121e145b5a2c6934813f1c106",
      "sender": "0"
    }
  ]
}
```

## Adding more nodes

If there is only one node running, that makes this centralized, which defeats the purpose.
Adding nodes creates a decentralized operation where all the nodes work together to create
a long, valid blockchain.

To add a node, spin up another node on a different port (lets say 5001). Now you should have
a node running on port 5000, and a node running on port 5001.

Lets add the node on port 5001, to the node on port 5000.

```
curl -XPOST -H "Content-Type: application/json" localhost:5000/nodes/register -d '{"nodes": ["http://localhost:5001"]}' | jq .
```
You will see that the node has been added:
```
{
  "message": "New nodes have been added",
  "total_nodes": [
    "localhost:5001"
  ]
}
```

## Creating a consensus between the nodes

Creating a consensus means that all of the nodes are at the exact same point in the chain.
When running the consensus, the node with the longest chain will win and be the authoritator.

**NOTE: This part I'm not quite sure about when it should run? Maybe before each transaction? Or mine?**

```
curl localhost:5000/nodes/resolve | jq .
```

Responding with:
```
{
  "chain": [
    {
      "index": 1,
      "previous_hash": 1,
      "proof": 100,
      "timestamp": 1618316154.1092823,
      "transactions": []
    },
    {
      "index": 2,
      "previous_hash": "e303f232bcefc82e9947c649999fd407e26fea0c058e12c5930feb124760bb11",
      "proof": 35293,
      "timestamp": 1618316710.5260475,
      "transactions": [
        {
          "amount": 1,
          "recipient": "322e032121e145b5a2c6934813f1c106",
          "sender": "0"
        }
      ]
    },
    {
      "index": 3,
      "previous_hash": "d39d04ce4feb4f16b47d4b848e32e71969e2b41404898142021fc6b9a3d4e5cc",
      "proof": 35089,
      "timestamp": 1618316721.8000474,
      "transactions": [
        {
          "amount": 5,
          "recipient": "otheruser2",
          "sender": "newuser"
        },
        {
          "amount": 1,
          "recipient": "322e032121e145b5a2c6934813f1c106",
          "sender": "0"
        }
      ]
    },
    {
      "index": 4,
      "previous_hash": "24d2855558ca38df196d97b6065a5fa9f4c9d0e6ec8df3ee6935452df2a3cb87",
      "proof": 119678,
      "timestamp": 1618316768.5888228,
      "transactions": [
        {
          "amount": 1,
          "recipient": "322e032121e145b5a2c6934813f1c106",
          "sender": "0"
        }
      ]
    },
    {
      "index": 5,
      "previous_hash": "71819302f451146072fa507dd5b28bdfe546c0ad37adf3f0cbfddb733ac08b4d",
      "proof": 146502,
      "timestamp": 1618316815.34439,
      "transactions": [
        {
          "amount": 5,
          "recipient": "otheruser2",
          "sender": "newuser"
        },
        {
          "amount": 1,
          "recipient": "322e032121e145b5a2c6934813f1c106",
          "sender": "0"
        }
      ]
    }
  ],
  "message": "Our chain is authoritative"
}
```

We are authoritative because the node on 5001 hasn't had any transactions.

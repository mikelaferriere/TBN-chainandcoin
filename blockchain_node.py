"""
API to interact with the blockchain.
"""
import logging
import getpass
import os
import json

from uuid import uuid4
from flask import Flask, jsonify, request

from block import Block
from blockchain import Blockchain
from transaction import Transaction
from walletv2 import Wallet


logging.basicConfig(level=logging.INFO)

# Instantiate the node
app = Flask(__name__)
node_id = uuid4()

IS_MASTERNODE = os.getenv("MASTERNODE") is not None

w = Wallet()

# Instantiate the Blockchain
blockchain = None


@app.route("/mine", methods=["POST"])
def mine():
    values = request.get_json()

    # Check for required fields
    required = ["miner_address"]
    if not all(k in values for k in required):
        return "Missing values", 400

    blockchain.mine_block(values["miner_address"])

    response = {
        "message": "New Block Forged",
        "block": blockchain.last_block.to_ordered_dict(),
    }

    return jsonify(response), 200


@app.route("/transactions/new", methods=["POST"])
def new_transaction():
    values = request.get_json()

    # Check for required fields
    required = ["sender", "recipient", "amount", "signature"]
    if not all(k in values for k in required):
        return "Missing values", 400

    # Create a new Transaction
    index = blockchain.add_transaction(
        Transaction(
            sender=values["sender"],
            recipient=values["recipient"],
            amount=values["amount"],
            signature=values["signature"],
        )
    )

    response = {"message": f"Transaction will be added to Block {index}"}
    return jsonify(response), 201


@app.route("/transactions/pending", methods=["GET"])
def pending_transaction():
    """
    Returns any of the open transactions on the node

    Methods
    -----
    GET

    Returns application/json
    -----
    Return code : 201
    Response :
      transactions : List[Transaction]
    """
    # Get pending Transactions
    pending = [p.to_ordered_dict() for p in blockchain.get_open_transactions]
    return jsonify(pending), 201


@app.route("/chain", methods=["GET"])
def full_chain():
    """
    Returns the entire chain along with its length

    Methods
    -----
    GET

    Returns application/json
    -----
    Return code : 200
    Response :
      chain : List[Block]
      length : int
    """
    response = {"chain": blockchain.pretty_chain(), "length": len(blockchain.chain)}
    return jsonify(response), 200


@app.route("/nodes", methods=["GET"])
def get_nodes():
    """
    Returns all the nodes that this node is aware of

    Methods
    -----
    GET

    Returns application/json
    -----
    Return code : 201
    Response :
      message : str
      total_nodes : List[str]
    """
    response = {
        "message": "All nodes.",
        "total_nodes": list(blockchain.nodes),
    }

    return jsonify(response), 201


@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    """
    Registers a new node to the list of nodes.
    Returns all the nodes that this node is aware of

    Methods
    -----
    POST

    Parameters
    -----
      nodes : List[uri]

    Returns application/json
    -----
    Return code : 201
    Response :
      message : str
      total_nodes : List[str]
    """
    values = request.get_json()

    nodes = values.get("nodes")
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        "message": "New nodes have been added",
        "total_nodes": list(blockchain.nodes),
    }

    return jsonify(response), 201


# POST - Broadcast Mined Block Information to Peer Nodes
@app.route("/broadcast-block", methods=["POST"])
def broadcast_block():
    """
    Broadcasts a new block to all the nodes
    Returns a status message

    Methods
    -----
    POST

    Parameters
    -----
      block : Block as Dict

    Returns application/json
    -----
    Return code : 201, 400, 409, 500
    Response :
      message : str
    """
    values = request.get_json()
    if not values:
        response = {"message": "No data found."}
        return jsonify(response), 400
    if "block" not in values:
        response = {"message": "Some data is missing."}
        return jsonify(response), 400
    block_dict = json.loads(values["block"])
    block = Block.generate_from_dict(block_dict)
    if block.index == blockchain.last_block.index + 1:
        added, message = blockchain.add_block(block)
        if added:
            response = {"message": "Block added"}
            return jsonify(response), 201
        response = {"message": "Block seems invalid: " + message}
        return jsonify(response), 500
    if block.index > blockchain.chain[-1].index:
        response = {
            "message": "Incoming block index higher than last block on current chain"
        }
        return jsonify(response), 500
    response = {"message": "Blockchain seems to be shorter, block not added"}
    return jsonify(response), 409


# POST - Broadcast Transaction Information to Peer Nodes
@app.route("/broadcast-transaction", methods=["POST"])
def broadcast_transaction():
    """
    Broadcasts a new transaction to all the nodes
    Returns a status message

    Methods
    -----
    POST

    Parameters
    -----
      sender : str
      recipient : str
      amount : float
      signature : str

    Returns application/json
    -----
    Return code : 201, 400, 500
    Response :
      message : str
      transaction : optional Transaction as Dict
    """
    values = request.get_json()
    if not values:
        response = {"message": "No data found."}
        return jsonify(response), 400
    required = ["sender", "recipient", "amount", "signature"]
    if not all(key in values for key in required):
        response = {"message": "Some data is missing."}
        return jsonify(response), 400
    success = blockchain.add_transaction(
        Transaction(
            sender=values["sender"],
            recipient=values["recipient"],
            amount=values["amount"],
            signature=values["signature"],
        ),
        is_receiving=True,
    )
    if success:
        response = {
            "message": "Successfully added transaction.",
            "transaction": {
                "sender": values["sender"],
                "recipient": values["recipient"],
                "amount": values["amount"],
                "signature": values["signature"],
            },
        }
        return jsonify(response), 201
    response = {"message": "Creating a transaction failed."}
    return jsonify(response), 500


if __name__ == "__main__":
    address = "MASTERNODE"
    if not IS_MASTERNODE:
        password = getpass.getpass()
        result = w.login(password)
        if not result:
            raise ValueError("Unable to configure wallet for blockchain integration")

        if not w.address:
            raise ValueError(
                "Must configure a wallet address in order to interact with the blockchain"
            )
        address = w.address

    blockchain = Blockchain(address, node_id)

    if not blockchain:
        raise ValueError("Unabled to initialize blockchain")

    if not IS_MASTERNODE:
        logging.info("Connecting to MASTERNODE")
        blockchain.register_node("https://sedrik.life/blockchain")

        logging.info("Syncing with the network")
        blockchain.resolve_conflicts()

        logging.info("Synced with the network")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))

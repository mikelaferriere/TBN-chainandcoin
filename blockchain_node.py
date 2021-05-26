"""
API to interact with the blockchain.
"""
import logging
import getpass
import os

from uuid import uuid4
from flask import Flask, jsonify, request
from flask_cors import CORS

from blockchain import Blockchain
from block import Block
from transaction import Details, FinalTransaction, SignedRawTransaction
from util.logging0 import configure_logging
from verification import Verification
from wallet import Wallet

configure_logging()


def create_app(
    test=False, _test_config=None
):  # pylint: disable=too-many-locals,too-many-statements

    # Instantiate the node
    app = Flask(__name__)
    CORS(app)

    node_id = uuid4()

    IS_MASTERNODE = os.getenv("MASTERNODE") is not None

    w = Wallet()

    # Instantiate the Blockchain
    blockchain = None

    address = "MASTERNODE"
    if not test and not IS_MASTERNODE:
        password = getpass.getpass()
        result = w.login(password)
        if not result:
            raise ValueError("Unable to configure wallet for blockchain integration")

        if not w.address:
            raise ValueError(
                "Must configure a wallet address in order to interact with the blockchain"
            )
        address = w.address

    timestamp = None if not test else 0
    blockchain = Blockchain(address, node_id, is_test=test, timestamp=timestamp)

    if not blockchain:
        raise ValueError("Unabled to initialize blockchain")

    if not test and not IS_MASTERNODE:
        logging.info("Connecting to MASTERNODE")
        blockchain.register_node("https://sedrik.life/blockchain")

        logging.info("Syncing with the network")
        blockchain.resolve_conflicts()

        logging.info("Synced with the network")

    #                                                #
    #                 ENDPOINTS                      #
    #                                                #

    @app.route("/mine", methods=["POST"])
    def mine():  # pylint: disable=unused-variable
        values = request.get_json()

        # Check for required fields
        required = ["miner_address"]
        if not values or not all(k in values for k in required):
            return "Missing values", 400

        blockchain.mine_block(values["miner_address"])

        block = blockchain.last_block

        response = {
            "message": "New Block Forged",
            "block": block.dict(),
        }

        return jsonify(response), 200

    @app.route("/transactions/new", methods=["POST"])
    def new_transaction():  # pylint: disable=unused-variable
        values = request.get_json()

        # Check for required fields
        required = ["transaction"]
        if not values or not all(k in values for k in required):
            return "Missing values", 400

        details = values["transaction"]["details"]
        # Create a new Transaction

        index = blockchain.add_transaction(
            SignedRawTransaction(
                details=Details(
                    sender=details["sender"],
                    recipient=details["recipient"],
                    amount=details["amount"],
                    nonce=details["nonce"],
                    timestamp=details["timestamp"],
                    public_key=details["public_key"],
                ),
                signature=values["transaction"]["signature"],
            )
        )

        response = {"message": f"Transaction will be added to Block {index}"}
        return jsonify(response), 201

    @app.route("/transactions/pending", methods=["GET"])
    def pending_transaction():  # pylint: disable=unused-variable
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
        pending = [t.transaction_hash for t in blockchain.get_open_transactions]
        return jsonify(pending), 201

    @app.route("/chain", methods=["GET"])
    def full_chain():  # pylint: disable=unused-variable
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

    @app.route("/block/<block_hash>", methods=["GET"])
    def block_by_hash(block_hash):  # pylint: disable=unused-variable
        """
        Returns a cleartext block by its hash

        Methods
        -----
        GET

        Returns application/json
        -----
        Return code : 200
        Response :
        chain : Block
        """
        solved_block = Block.FindBlock(blockchain.data_location, block_hash)
        if solved_block:
            block = Block.ParseFromHex(solved_block)
            return jsonify(block.json()), 200
        return jsonify({"error": f"No block found with hash {block_hash}"}), 404

    @app.route("/transactions/<transaction_hash>", methods=["GET"])
    def transaction_by_hash(transaction_hash):  # pylint: disable=unused-variable
        """
        Returns a cleartext transaction by its hash

        Methods
        -----
        GET

        Returns application/json
        -----
        Return code : 200
        Response :
        tx : SignedRawTransaction
        """
        #
        # Find tx in storage by hash
        #
        transaction = SignedRawTransaction.ParseFromHex(transaction_hash)
        return jsonify(transaction.json()), 200

    @app.route("/nodes", methods=["GET"])
    def get_nodes():  # pylint: disable=unused-variable
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
    def register_nodes():  # pylint: disable=unused-variable
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
    def broadcast_block():  # pylint: disable=unused-variable
        """
        Broadcasts a new block to all the nodes
        Returns a status message

        Methods
        -----
        POST

        Parameters
        -----
        block : Block as hex

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
        block = Block.ParseFromHex(values["block"])
        if block.index == blockchain.last_block.index + 1:
            added, message = blockchain.add_block(block)
            if added:
                response = {"message": "Block added"}
                return jsonify(response), 201
            response = {"message": "Block seems invalid: " + message}
            return jsonify(response), 500
        if block.index > blockchain.last_block.index:
            response = {
                "message": "Incoming block index higher than last block on current chain"
            }
            return jsonify(response), 500
        response = {"message": "Blockchain seems to be shorter, block not added"}
        return jsonify(response), 409

    # POST - Broadcast Transaction Information to Peer Nodes
    @app.route("/broadcast-transaction", methods=["POST"])
    def broadcast_transaction():  # pylint: disable=unused-variable
        """
        Broadcasts a new transaction to all the nodes
        Returns a status message

        Methods
        -----
        POST

        Parameters
        -----
        transaction : SignedRawTransaction as hex

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
        required = ["transaction"]
        if not all(key in values for key in required):
            response = {"message": "Some data is missing."}
            return jsonify(response), 400
        t = SignedRawTransaction.ParseFromHex(values["transaction"])
        try:
            if t.signature == "coinbase":
                # This is a mining transaction, so just save it
                tx = FinalTransaction(
                    transaction_hash=Verification.hash_transaction(t),
                    transaction_id=Verification.hash_transaction(t),
                    signed_transaction=t,
                )
                FinalTransaction.SaveMiningTransaction(blockchain.data_location, tx)
                response = {
                    "message": "Successfully saved mining transaction.",
                    "transaction": values["transaction"],
                }
                return jsonify(response), 201
            block_index = blockchain.add_transaction(t, is_receiving=True)
            response = {
                "message": "Successfully added transaction.",
                "transaction": values["transaction"],
                "block": block_index,
            }
            return jsonify(response), 201
        except ValueError as e:
            response = {"message": "Creating a transaction failed.", "error": str(e)}
        return jsonify(response), 500

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))

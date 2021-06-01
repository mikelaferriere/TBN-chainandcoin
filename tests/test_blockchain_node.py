# flake8: noqa

import json
import shutil

import flask_unittest
from flask.testing import FlaskClient

from blockchain_node import create_app
from tests.const import TRANSACTION, TRANSACTION_HASH


class TestBase(flask_unittest.AppClientTestCase):
    maxDiff = None

    def create_app(self):
        """Create and configure a new app instance for each test."""
        app = create_app(test=True)

        # create the database and load test data
        with app.app_context():

            # Yield the app
            """
            This can be outside the `with` block too, but we need to
            call `close_db` before exiting current context
            Otherwise windows will have trouble removing the temp file
            that doesn't happen on unices though, which is nice
            """
            yield app

        ## Cleanup temp file
        try:
            shutil.rmtree(f"{tempfile.tempdir}/blockchain")
        except Exception:
            pass


class TestNodeChain(TestBase):
    def test_chain_response(self, _, client):
        rv = client.get("/chain")
        self.assertStatus(rv, 200)


class TestNodeNodes(TestBase):
    def test_nodes_response(self, _, client):
        rv = client.get("/nodes")
        self.assertStatus(rv, 201)

    def test_nodes_register(self, _, client):
        rv = client.post("/nodes/register", json={"nodes": ["https://google.com"]})
        self.assertStatus(rv, 201)
        self.assertJsonEqual(
            rv,
            {
                "message": "New nodes have been added",
                "total_nodes": ["https://google.com"],
            },
        )


class TestNodeMining(TestBase):
    def test_mining_missing_address(self, _, client):
        rv = client.post("/mine")
        self.assertStatus(rv, 400)

        rv = client.post("/mine", json={})
        self.assertStatus(rv, 400)

    def test_mining_success(self, _, client):
        rv = client.post(
            "/mine", json={"miner_address": TRANSACTION["details"]["sender"]}
        )
        self.assertStatus(rv, 200)


class TestNodeTransaction(TestBase):
    def test_new_transaction_missing_data(self, _, client):
        rv = client.post("/transactions/new")
        self.assertStatus(rv, 400)

        rv = client.post("/transactions/new", json={})
        self.assertStatus(rv, 400)

    def test_new_transaction_success(self, _, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        rv = client.post("/transactions/new", json={"transaction": TRANSACTION})

    def test_pending_transaction(self, _, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        rv = client.post("/transactions/new", json={"transaction": TRANSACTION})
        self.assertStatus(rv, 201)

        rv = client.get("/transactions/pending")
        self.assertJsonEqual(
            rv, ["3e0cf83c951ffcff548e0414581ce562b626265eaa2cae5e154d2a404ce3ddee"]
        )

    def test_by_transaction_hash(self, _, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        client.post("/transactions/new", json={"transaction": TRANSACTION})
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})

        rv = client.get(
            "/transaction/3e0cf83c951ffcff548e0414581ce562b626265eaa2cae5e154d2a404ce3ddee"
        )

        t = {
            "transaction_hash": "3e0cf83c951ffcff548e0414581ce562b626265eaa2cae5e154d2a404ce3ddee",
            "transaction_id": "3e0cf83c951ffcff548e0414581ce562b626265eaa2cae5e154d2a404ce3ddee",
            "signed_transaction": TRANSACTION,
        }
        self.assertJsonEqual(rv, {"transaction": json.dumps(t), "type": "confirmed"})

    def test_broadcast_transaction_happy_path(self, _, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        rv = client.post(
            "/broadcast-transaction",
            json={"transaction": TRANSACTION_HASH, "type": "open"},
        )
        self.assertStatus(rv, 201)
        self.assertJsonEqual(
            rv,
            {
                "message": "Successfully added transaction.",
                "transaction": TRANSACTION_HASH,
                "block": 2,
            },
        )


class TestNodeBlock(TestBase):
    def test_block_by_hash(self, _, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        client.post("/transactions/new", json={"transaction": TRANSACTION})
        rv = client.post(
            "/mine", json={"miner_address": TRANSACTION["details"]["sender"]}
        )
        block = rv.json["block"]
        rv = client.get("/block/" + json.loads(block)["block_hash"])

        self.assertJsonEqual(rv, block)


class TestNodeBroadcastBlock(TestBase):
    def test_happy_path(self, _, client):
        rv = client.post(
            "/broadcast-block",
            json={
                "block": "08011000225a08011240306361613265323333356136376463666261303566363463356637643965396538653161376436383937663432623565643266363831363035613366313932621a00220c0899ef97850610b0cbd7c5012804308ac8042801323a0a0130122a3078336530373165386438613433623264653661636133656138633862333163633238663734313066611900000000000024402800"
            },
        )
        self.assertStatus(rv, 201)
        self.assertJsonEqual(rv, {"message": "Block added"})


class TestNodeBroadcastBlockFailures(TestBase):
    def test_lower_index(self, _, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        rv = client.post(
            "/broadcast-block",
            json={
                "block": "08011000225a08011240656532353230613132646164376164623234666433346332663733316439633465326533356131666535383333333431376132303864376537343737646437641a00220c08fd829485061080869ced02280430dddc012801323a0a0130122a3078336530373165386438613433623264653661636133656138633862333163633238663734313066611900000000000024402800"
            },
        )
        self.assertStatus(rv, 409)
        self.assertJsonEqual(
            rv, {"message": "Blockchain seems to be shorter, block not added"}
        )

    def test_incoming_index_too_high(self, _, client):
        rv = client.post(
            "/broadcast-block",
            json={
                "block": "08031000225908011240386663643066343963323137333135323464636662643061323633373961613630306437373263626461313139333935353839646361316334326530366361331a00220c08b3ba97850610f0fbe08603280430f7342801323a0a0130122a3078336530373165386438613433623264653661636133656138633862333163633238663734313066611900000000000024402800"
            },
        )
        self.assertJsonEqual(
            rv,
            {"message": "Incoming block index higher than last block on current chain"},
        )
        self.assertStatus(rv, 500)

    def test_previous_hash_mismatch(self, _, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        rv = client.post(
            "/broadcast-block",
            json={
                "block": "08031000225908011240386663643066343963323137333135323464636662643061323633373961613630306437373263626461313139333935353839646361316334326530366361331a00220c08b3ba97850610f0fbe08603280430f7342801323a0a0130122a3078336530373165386438613433623264653661636133656138633862333163633238663734313066611900000000000024402800"
            },
        )
        self.assertJsonEqual(
            rv,
            {
                "message": (
                    "Block seems invalid: Hash of last block does not equal previous "
                    "hash in the current block"
                )
            },
        )
        self.assertStatus(rv, 500)

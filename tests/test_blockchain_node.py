# flake8: noqa

import json

import flask_unittest
from flask.testing import FlaskClient

from blockchain_node import create_app
from tests.const import BLOCK_HASH, TRANSACTION, TRANSACTION_HASH


class TestBase(flask_unittest.ClientTestCase):
    pass


class TestNodeChain(TestBase):
    app = create_app(test=True)

    def setUp(self, client: FlaskClient):
        # Make sure client is passed in correctly and has correct type
        self.assertTrue(client is not None)
        self.assertTrue(isinstance(client, FlaskClient))

    def tearDown(self, client: FlaskClient):
        # Make sure client is passed in correctly and has correct type
        self.assertTrue(client is not None)
        self.assertTrue(isinstance(client, FlaskClient))

    def test_chain_response(self, client):
        rv = client.get("/chain")
        self.assertStatus(rv, 200)


class TestNodeNodes(TestBase):
    app = create_app(test=True)

    def setUp(self, client: FlaskClient):
        # Make sure client is passed in correctly and has correct type
        self.assertTrue(client is not None)
        self.assertTrue(isinstance(client, FlaskClient))

    def tearDown(self, client: FlaskClient):
        # Make sure client is passed in correctly and has correct type
        self.assertTrue(client is not None)
        self.assertTrue(isinstance(client, FlaskClient))

    def test_nodes_response(self, client):
        rv = client.get("/nodes")
        self.assertStatus(rv, 201)

    def test_nodes_register(self, client):
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
    app = create_app(test=True)

    def setUp(self, client: FlaskClient):
        # Make sure client is passed in correctly and has correct type
        self.assertTrue(client is not None)
        self.assertTrue(isinstance(client, FlaskClient))

    def tearDown(self, client: FlaskClient):
        # Make sure client is passed in correctly and has correct type
        self.assertTrue(client is not None)
        self.assertTrue(isinstance(client, FlaskClient))

    def test_mining_missing_address(self, client):
        rv = client.post("/mine")
        self.assertStatus(rv, 400)

        rv = client.post("/mine", json={})
        self.assertStatus(rv, 400)

    def test_mining_success(self, client):
        rv = client.post(
            "/mine", json={"miner_address": TRANSACTION["details"]["sender"]}
        )
        self.assertStatus(rv, 200)


class TestNodeTransaction(TestBase):
    app = create_app(test=True)

    def setUp(self, client: FlaskClient):
        # Make sure client is passed in correctly and has correct type
        self.assertTrue(client is not None)
        self.assertTrue(isinstance(client, FlaskClient))

    def tearDown(self, client: FlaskClient):
        # Make sure client is passed in correctly and has correct type
        self.assertTrue(client is not None)
        self.assertTrue(isinstance(client, FlaskClient))

    def test_new_transaction_missing_data(self, client):
        rv = client.post("/transactions/new")
        self.assertStatus(rv, 400)

        rv = client.post("/transactions/new", json={})
        self.assertStatus(rv, 400)

    def test_new_transaction_success(self, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        rv = client.post("/transactions/new", json={"transaction": TRANSACTION})
        self.assertStatus(rv, 201)

    def test_pending_transaction(self, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        rv = client.post("/transactions/new", json={"transaction": TRANSACTION})
        self.assertStatus(rv, 201)

        rv = client.get("/transactions/pending")
        self.assertJsonEqual(
            rv, ["3e0cf83c951ffcff548e0414581ce562b626265eaa2cae5e154d2a404ce3ddee"]
        )

    def test_by_transaction_hash(self, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        client.post("/transactions/new", json={"transaction": TRANSACTION})
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})

        rv = client.get("/transactions/" + TRANSACTION_HASH)
        self.assertJsonEqual(rv, json.dumps(TRANSACTION))

    def test_broadcast_transaction_happy_path(self, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        rv = client.post(
            "/broadcast-transaction", json={"transaction": TRANSACTION_HASH}
        )
        self.assertStatus(rv, 201)
        self.assertJsonEqual(
            rv,
            {
                "message": "Successfully added transaction.",
                "transaction": TRANSACTION_HASH,
            },
        )


class TestNodeBlock(TestBase):
    app = create_app(test=True)

    def setUp(self, client: FlaskClient):
        # Make sure client is passed in correctly and has correct type
        self.assertTrue(client is not None)
        self.assertTrue(isinstance(client, FlaskClient))

    def tearDown(self, client: FlaskClient):
        # Make sure client is passed in correctly and has correct type
        self.assertTrue(client is not None)
        self.assertTrue(isinstance(client, FlaskClient))

    def test_block_by_hash(self, client):
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        client.post("/transactions/new", json={"transaction": TRANSACTION})
        client.post("/mine", json={"miner_address": TRANSACTION["details"]["sender"]})
        rv = client.get("/block/" + BLOCK_HASH)

        self.assertJsonEqual(
            rv,
            {
                "header": {
                    "difficulty": 4,
                    "nonce": 4485,
                    "previous_hash": "e8eac1c3e88a9c4a256471541aeee273998d7e5ff7cd780b222181c1ab802937",
                    "transaction_merkle_root": "0ac0010a2a30786539343532333833303835363235366134336530613534366334353634303630333130333437336212047465737419cdcccccccccc004020002a800164656338643463623263626438663739326538343136653638653932663463366335386261356236656438666663323961383962386461363735666334396138656638653239383962653965623033626133383432343463643164643335363465656137616563363038613333376137656461663734323366613934326636311280016634613030303263346638323138373638663835336664336337316238323564656561313864613634336435366635346565653464303335366466616135636135393439343631393461383362633635376338326561393631623463646636303665363136333138383334323239633031343563633933626234336562663437",
                    "version": 1,
                },
                "index": 2,
                "transaction_count": 2,
                "transactions": [
                    "bc4b43442a2a0431bf5939bcaf59461ad01b0877b8f9ccf2fc38573f4a5662ed",
                    "160de79ef9a8ca77d832cf513c5958a6cc2a430517d03191089809dc3a83a92f",
                ],
            },
        )


class TestNodeBroadcastBlock(flask_unittest.ClientTestCase):
    app = create_app(test=True)

    def test_happy_path(self, client):
        rv = client.post(
            "/broadcast-block",
            json={
                "block": "08011000225a08011240306361613265323333356136376463666261303566363463356637643965396538653161376436383937663432623565643266363831363035613366313932621a00220c0899ef97850610b0cbd7c5012804308ac8042801323a0a0130122a3078336530373165386438613433623264653661636133656138633862333163633238663734313066611900000000000024402800"
            },
        )
        self.assertStatus(rv, 201)
        self.assertJsonEqual(rv, {"message": "Block added"})


class TestNodeBroadcastBlockFailures(flask_unittest.ClientTestCase):
    app = create_app(test=True)

    def test_lower_index(self, client):
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

    def test_incoming_index_too_high(self, client):
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

    def test_previous_hash_mismatch(self, client):
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

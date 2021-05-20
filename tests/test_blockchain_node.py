# flake8: noqa

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
        rv = client.post("/mine", json={"miner_address": TRANSACTION["sender"]})
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
        client.post("/mine", json={"miner_address": TRANSACTION["sender"]})
        rv = client.post("/transactions/new", json=TRANSACTION)
        self.assertStatus(rv, 201)

    def test_pending_transaction(self, client):
        client.post("/mine", json={"miner_address": TRANSACTION["sender"]})
        rv = client.post("/transactions/new", json=TRANSACTION)
        self.assertStatus(rv, 201)

        rv = client.get("/transactions/pending")
        self.assertJsonEqual(rv, [TRANSACTION])

    def test_by_transaction_hash(self, client):
        client.post("/mine", json={"miner_address": TRANSACTION["sender"]})
        client.post("/transactions/new", json=TRANSACTION)
        client.post("/mine", json={"miner_address": TRANSACTION["sender"]})

        rv = client.get("/transactions/" + TRANSACTION_HASH)
        self.assertJsonEqual(rv, TRANSACTION)

    def test_broadcast_transaction_happy_path(self, client):
        client.post("/mine", json={"miner_address": TRANSACTION["sender"]})
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
        client.post("/mine", json={"miner_address": TRANSACTION["sender"]})
        client.post("/transactions/new", json=TRANSACTION)
        client.post("/mine", json={"miner_address": TRANSACTION["sender"]})

        rv = client.get("/block/" + BLOCK_HASH)

        self.assertJsonEqual(
            rv,
            {
                "header": {
                    "difficulty": 4,
                    "nonce": 72490,
                    "previous_hash": "c65f499ea16147eda79176097c3a0db87eabc54b091434a38d099e04bb5f5397",
                    "transaction_merkle_root": "0a2a307833653037316538643861343362326465366163613365613863386233316363323866373431306661122a307831623731636261383837646464386132336561343334643830323230626361396364383439363135190000000000001240228001653431653332353562363962336639333936363731663635333763363434313635653637373234386266353733383737346532313832393364643936386435306164373765323563386234643930323538626639343566343936656465666633346363316364666138303666653531363066363438653330623932646564653828003280013235653633613661646637373762306661383437336131643038363036653764353966333164396637396661663630386238396564396638376534316533363333623338336165316339633430386330313035666235343438366633373638613264633930383336303836333039616434343831303764306330396461366163",
                    "version": 1,
                },
                "index": 2,
                "transaction_count": 2,
                "transactions": [
                    "0a2a307833653037316538643861343362326465366163613365613863386233316363323866373431306661122a307831623731636261383837646464386132336561343334643830323230626361396364383439363135190000000000001240228001653431653332353562363962336639333936363731663635333763363434313635653637373234386266353733383737346532313832393364643936386435306164373765323563386234643930323538626639343566343936656465666633346363316364666138303666653531363066363438653330623932646564653828003280013235653633613661646637373762306661383437336131643038363036653764353966333164396637396661663630386238396564396638376534316533363333623338336165316339633430386330313035666235343438366633373638613264633930383336303836333039616434343831303764306330396461366163",
                    "0a0130122a3078336530373165386438613433623264653661636133656138633862333163633238663734313066611900000000000024402800",
                ],
            },
        )


class TestNodeBroadcastBlock(flask_unittest.ClientTestCase):
    app = create_app(test=True)

    def test_happy_path(self, client):
        rv = client.post(
            "/broadcast-block",
            json={
                "block": "08011000225a08011240656532353230613132646164376164623234666433346332663733316439633465326533356131666535383333333431376132303864376537343737646437641a00220c08fd829485061080869ced02280430dddc012801323a0a0130122a3078336530373165386438613433623264653661636133656138633862333163633238663734313066611900000000000024402800"
            },
        )
        self.assertStatus(rv, 201)
        self.assertJsonEqual(rv, {"message": "Block added"})


class TestNodeBroadcastBlockFailures(flask_unittest.ClientTestCase):
    app = create_app(test=True)

    def test_lower_index(self, client):
        client.post("/mine", json={"miner_address": TRANSACTION["sender"]})
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
        rv = client.get("/chain")
        print(rv.json)
        rv = client.post("/broadcast-block", json={"block": BLOCK_HASH})
        self.assertJsonEqual(
            rv,
            {"message": "Incoming block index higher than last block on current chain"},
        )
        self.assertStatus(rv, 500)

    def test_previous_hash_mismatch(self, client):
        rv = client.post("/broadcast-block", json={"block": BLOCK_HASH})
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

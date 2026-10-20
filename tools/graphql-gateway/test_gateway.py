import unittest
from pathlib import Path

import gateway

HERE = Path(__file__).resolve().parent
CORPUS = HERE.parent / "compliance-report" / "testdata" / "corpus.jsonl"


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.events = gateway.load_events(CORPUS)

    def test_documented_example_queries(self):
        out = gateway.execute(self.events, '{ events(type: "score", limit: 3) { wallet score ledger } }')
        self.assertEqual(len(out["events"]), 3)
        self.assertTrue(all(set(r) == {"wallet", "score", "ledger"} for r in out["events"]))
        n = gateway.execute(self.events, '{ eventCount(type: "heartbeat") }')["eventCount"]
        self.assertEqual(n, sum(e["type"] == "heartbeat" for e in self.events))

    def test_deep_query_rejected(self):
        q = "{ events(limit: 1) { related(limit: 1) { related(limit: 1) { ledger } } } }"
        with self.assertRaisesRegex(gateway.GatewayError, "depth"):
            gateway.execute(self.events, q)

    def test_complex_query_rejected(self):
        q = "{ events(limit: 100) { related(limit: 100) { ledger } } }"
        with self.assertRaisesRegex(gateway.GatewayError, "complexity"):
            gateway.execute(self.events, q)

    def test_no_write_operations(self):
        for q in ('mutation { events { ledger } }', 'subscription { events { ledger } }',
                  '{ setScore(wallet: "x") }'):
            with self.assertRaises(gateway.GatewayError):
                gateway.execute(self.events, q)
        self.assertNotIn("Mutation", gateway.sdl())
        self.assertNotIn("Subscription", gateway.sdl())

    def test_schema_in_sync(self):
        self.assertEqual(gateway.main(["schema", "--check", str(HERE / "schema.graphql")]), 0)


if __name__ == "__main__":
    unittest.main()

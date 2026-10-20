import json
import tempfile
import unittest
from pathlib import Path

import export

CORPUS = Path(__file__).resolve().parents[1] / "compliance-report" / "testdata" / "corpus.jsonl"


def ev(w, score, ledger=100):
    return {"type": "score", "wallet": f"W{w}", "score": score, "ledger": ledger}


class ExportTests(unittest.TestCase):
    def test_too_small_population_refused_and_nothing_written(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(export.ExportRefused):
                export.write_export([ev(i, 50) for i in range(export.MIN_GROUP_SIZE - 1)], d)
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_small_cells_suppressed_and_counts_rounded(self):
        events = [ev(i, 55) for i in range(13)] + [ev(100 + i, 5) for i in range(3)]
        r = export.aggregate(events)
        self.assertEqual(r["suppressed_cells"], 1)
        self.assertEqual([c["wallets_approx"] for c in r["score_distribution"]], [15])

    def test_no_wallet_identifiers_in_output(self):
        events = [json.loads(l) for l in CORPUS.read_text().splitlines() if l.strip()]
        with tempfile.TemporaryDirectory() as d:
            try:
                export.write_export(events, d)
            except export.ExportRefused:
                return
            blob = (Path(d) / "export.json").read_text()
            self.assertNotIn("GWALLET", blob)
            self.assertTrue((Path(d) / "METHODOLOGY.md").exists())

    def test_redteam_differencing_cannot_isolate_wallet(self):
        base = [ev(i, 55) for i in range(14)]
        a = export.aggregate(base)
        b = export.aggregate(base + [ev(99, 55)])
        # Adding one wallet moves a rounded count by at most one step (or not at all).
        d = b["score_distribution"][0]["wallets_approx"] - a["score_distribution"][0]["wallets_approx"]
        self.assertIn(d, (0, export.ROUNDING))


if __name__ == "__main__":
    unittest.main()

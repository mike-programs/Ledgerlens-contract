#!/usr/bin/env python3
"""Privacy-preserving research export (issue #1445).

Reads the indexer JSON-lines corpus (docs/compliance-report.md) and writes
`export.json` (versioned, open format) and `METHODOLOGY.md` to --out. Only
aggregate statistics are emitted; wallet identifiers never appear.

Thresholds are enforced mechanically (see docs/research-export.md):
  * MIN_GROUP_SIZE: a published cell must cover >= this many DISTINCT wallets.
    Smaller cells are suppressed (omitted, counted in `suppressed_cells`).
  * ROUNDING: published counts are rounded to the nearest multiple of this.
  * If the whole population is smaller than MIN_GROUP_SIZE the export is
    refused outright (ExportRefused) and nothing is written.
"""

import argparse
import json
import sys
from pathlib import Path

EXPORT_VERSION = 1
MIN_GROUP_SIZE = 10
ROUNDING = 5
BUCKET_WIDTH = 10
LEDGER_WINDOW = 1000


class ExportRefused(Exception):
    pass


def round_count(n):
    return ((n + ROUNDING // 2) // ROUNDING) * ROUNDING


def aggregate(events):
    scores = [e for e in events if e.get("type") == "score" and "wallet" in e]
    wallets = {e["wallet"] for e in scores}
    if len(wallets) < MIN_GROUP_SIZE:
        raise ExportRefused(
            f"population of {len(wallets)} wallets is below MIN_GROUP_SIZE={MIN_GROUP_SIZE}")

    cells = {}
    for e in scores:
        key = (e["ledger"] // LEDGER_WINDOW, min(e["score"] // BUCKET_WIDTH, 100 // BUCKET_WIDTH - 1))
        cells.setdefault(key, set()).add(e["wallet"])

    published, suppressed = [], 0
    for (window, bucket), ws in sorted(cells.items()):
        if len(ws) < MIN_GROUP_SIZE:
            suppressed += 1
            continue
        published.append({
            "ledger_start": window * LEDGER_WINDOW,
            "ledger_end": (window + 1) * LEDGER_WINDOW - 1,
            "score_min": bucket * BUCKET_WIDTH,
            "score_max": bucket * BUCKET_WIDTH + BUCKET_WIDTH - 1,
            "wallets_approx": round_count(len(ws)),
        })
    return {
        "export_version": EXPORT_VERSION,
        "min_group_size": MIN_GROUP_SIZE,
        "rounding": ROUNDING,
        "score_distribution": published,
        "suppressed_cells": suppressed,
    }


METHODOLOGY = """# Export methodology (export_version {v})

- Source: indexer event corpus, `score` events only.
- Cell: distinct wallets scoring in a {w}-ledger window and a {b}-point score
  bucket. A wallet counts once per cell however many scores it submitted.
- Suppression: cells with fewer than {k} distinct wallets are omitted;
  `suppressed_cells` reports how many.
- Rounding: `wallets_approx` is rounded to the nearest multiple of {r}.
- Refusal: if fewer than {k} distinct wallets exist overall, no export is made.
- No wallet addresses, per-wallet histories or event indices are published.
"""


def write_export(events, out):
    result = aggregate(events)  # raises before anything is written
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "export.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (out / "METHODOLOGY.md").write_text(
        METHODOLOGY.format(v=EXPORT_VERSION, w=LEDGER_WINDOW, b=BUCKET_WIDTH,
                           k=MIN_GROUP_SIZE, r=ROUNDING), encoding="utf-8")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpus")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    events = [json.loads(l) for l in Path(a.corpus).read_text(encoding="utf-8").splitlines() if l.strip()]
    try:
        write_export(events, a.out)
    except ExportRefused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

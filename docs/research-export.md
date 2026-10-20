# Research Data Export

`tools/research-export/export.py` turns the indexer corpus into an aggregate,
privacy-preserving dataset for researchers (issue #1445).

```
python3 tools/research-export/export.py corpus.jsonl --out export/
```

## What is exported

Only the score distribution: per (ledger window, 10-point score bucket), the
approximate number of distinct wallets. No addresses, per-wallet histories or
event indices. Consistent with [privacy-model.md](privacy-model.md), no
per-wallet value leaves the indexer.

## Enforced thresholds

| Threshold | Value | Effect |
| --- | --- | --- |
| `MIN_GROUP_SIZE` | 10 distinct wallets | smaller cells are suppressed; population below this is refused (non-zero exit, nothing written) |
| `ROUNDING` | 5 | published counts rounded to the nearest multiple |

Verified by `tools/research-export/test_export.py` (a forced too-small export is refused).

## Format and schedule

`export.json` carries `export_version` (currently 1; any change to cells or
thresholds bumps it) next to `min_group_size` and `rounding`. Every export ships
with `METHODOLOGY.md`. Intended cadence: one export per calendar month from
the indexer's closed ledger range, published as an immutable release asset.

## Red-team re-identification attempt

Attempts made against the exporter (tests in `test_export.py`):

1. **Small-cell isolation** (a bucket with one wallet) – defeated: suppressed.
2. **Tiny population** – defeated: export refused.
3. **Address leakage** – corpus wallets never appear in output.
4. **Differencing two exports** that differ by one wallet – partially
   defeated: rounding hides the change except when it crosses a rounding
   boundary, which reveals only "one more wallet in a cell of ≥10", never
   which wallet or its history.

Residual risk: an adversary who already knows all but one wallet in a cell
can infer the last one's bucket across exports. Mitigation: monthly cadence,
rounding, and the 10-wallet floor; no fix beyond these is planned. Revisit if
`MIN_GROUP_SIZE` is lowered.

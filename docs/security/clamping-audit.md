# Clamping vs Rejection Audit (issue #1442)

Every site in `ledgerlens-score` / `ledgerlens-aggregator` arithmetic that
saturates or clamps, with rationale. Storage-counter `saturating_*` and
`min(MAX_*)` pagination caps are listed as a group.

| Site | Behaviour | Verdict |
| --- | --- | --- |
| Score/confidence input `> 100` (`submit_*`, batch paths in `lib.rs`) | **rejected** (`InvalidScore`/`InvalidConfidence`) | explicit rejection |
| Consensus upper bound `median + epsilon` `.min(100)` | clamp | deliberate: valid inputs near 100 yield a window that cannot exceed the domain |
| Signer weight `prior - penalty` `.max(1)` | clamp | deliberate: a slashed signer keeps the minimum weight, never zero or negative |
| Interpolation / curve outputs `.clamp(0, 100)` | clamp | deliberate: spline overshoot of valid inputs is expected; see [score-math.md](../score-math.md) |
| Adaptive threshold `max(min).min(max)` | clamp | deliberate: configured bounds are the contract |
| Oracle price floor `(price/20_000).min(50)` | cap | deliberate documented cap; non-positive price yields 0 |
| `saturating_add/sub` on timestamps, TTLs, counters, history paging | saturate | deliberate: u64 timestamp/counter overflow is unreachable; underflow means "elapsed 0" |
| `parameter_governance` decay check `saturating_mul` | saturate | deliberate: saturation makes the comparison reject, and `checked_mul` failure already rejects |
| `limit.min(MAX_HISTORY_DEPTH)`, `max_entries.min(MAX_EXPIRING_ENTRIES_PER_CALL)` | cap | deliberate: read-side page size, no state written |
| `ExtendedScore::from_basis_points` / `from_legacy` (aggregator `optimization.rs`) | clamp to 10 000 / 100 | **masks** out-of-range input; strict `try_from_basis_points` added (returns `None`), regression-tested. Existing callers keep the lenient constructor, so no existing behaviour changes |
| `ScoreReadStats` reduction `.min(100)` | cap | deliberate: percentage |

No existing test's expected behaviour changes. Conclusions are referenced from
[score-math.md](../score-math.md).

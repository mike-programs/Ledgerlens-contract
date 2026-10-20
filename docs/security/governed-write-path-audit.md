# Governed Parameter Write-Path Audit (issue #1447)

Governed parameters are those in `parameter_governance::bounds_registry`. This
audit traces every production call of each parameter's `storage::set_*`.

| Parameter | Write paths (all in `ledgerlens-score`) |
| --- | --- |
| cooldown | `parameter_governance::apply_parameter_change`; `set_cooldown` (admin multisig, bounds-checked); `apply_policy_bundle` (time-locked bundle) |
| history depth | `apply_parameter_change`; `apply_param_change` (time-locked, permissionless apply of an admin-proposed change) |
| decay rate | `apply_parameter_change`; `set_decay_rate` (admin auth, bounds-checked) |
| velocity cap | `apply_parameter_change`; `set_score_velocity_cap` (admin multisig) |
| upgrade delay | `apply_parameter_change`; `apply_param_change` |
| staleness window | `apply_parameter_change` (`set_staleness_window_secs`); `apply_param_change` |

## Findings

- Every path is gated by admin authorisation (directly, or by an admin-created
  time-locked proposal). No unauthenticated or differently-authorised path
  exists today.
- Several parameters have a second path besides the proposal/time-lock flow
  (`set_cooldown`, `set_decay_rate`, `set_score_velocity_cap` apply
  immediately under admin auth). These are legacy, intentional, and covered by
  existing tests, so are **left unchanged** to avoid altering governance
  behaviour. Moving them behind the time-lock would be a behaviour change and
  needs its own proposal.
- Cooldown's immediate path validates against constants rather than
  `validate_parameter_value`, so it skips the cooldown ≤ staleness cross-check.
  Recorded as a follow-up; out of scope here.

## Structural guarantee

`test_governed_write_paths.rs` counts the call sites of each setter per source
file and fails on any difference from the table above, so a new write path
needs a deliberate update to both the test and this document.

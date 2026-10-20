//! Structural guard for governed parameters (issue #1447).
//!
//! Counts the production call sites of each governed parameter's storage
//! setter. Adding a new write path changes a count and fails this test until
//! the path is reviewed and `docs/security/governed-write-path-audit.md` is
//! updated.

use std::string::String;
use std::vec::Vec;

const SOURCES: &[(&str, &str)] = &[
    ("lib.rs", include_str!("lib.rs")),
    ("parameter_governance.rs", include_str!("parameter_governance.rs")),
    ("governance_actions.rs", include_str!("governance_actions.rs")),
    ("governance_helpers.rs", include_str!("governance_helpers.rs")),
    ("rent_relay_credits.rs", include_str!("rent_relay_credits.rs")),
    ("fee_schedule.rs", include_str!("fee_schedule.rs")),
    ("invariants.rs", include_str!("invariants.rs")),
];

/// (storage setter call, expected (file, call-site count) pairs).
const GOVERNED: &[(&str, &[(&str, usize)])] = &[
    // lib.rs: `set_cooldown` (admin multisig) and `apply_policy_bundle`.
    ("storage::set_cooldown_secs(", &[("lib.rs", 2), ("parameter_governance.rs", 1)]),
    ("storage::set_history_max_depth(", &[("lib.rs", 1), ("parameter_governance.rs", 1)]),
    ("storage::set_upgrade_delay(", &[("lib.rs", 1), ("parameter_governance.rs", 1)]),
    ("storage::set_staleness_window(", &[("lib.rs", 1)]),
    ("storage::set_staleness_window_secs(", &[("parameter_governance.rs", 1)]),
    // lib.rs: admin-authorised `set_decay_rate` / `set_score_velocity_cap`.
    ("storage::set_decay_rate(", &[("lib.rs", 1), ("parameter_governance.rs", 1)]),
    ("storage::set_score_velocity_cap(", &[("lib.rs", 1), ("parameter_governance.rs", 1)]),
];

#[test]
fn governed_parameter_write_sites_are_exactly_the_audited_set() {
    for (setter, expected) in GOVERNED {
        let mut actual: Vec<(String, usize)> = Vec::new();
        for (file, src) in SOURCES {
            let n = src.matches(setter).count();
            if n > 0 {
                actual.push((String::from(*file), n));
            }
        }
        let want: Vec<(String, usize)> =
            expected.iter().map(|(f, n)| (String::from(*f), *n)).collect();
        assert_eq!(
            actual, want,
            "write sites for `{setter}` changed; review authorisation and update \
             docs/security/governed-write-path-audit.md"
        );
    }
}

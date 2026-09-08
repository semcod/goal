# Ticket 095: Enforce Goal main publication on GitHub

- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

SESSION_EXECUTION_AUTHORIZATION: the user requests continuation, publication and testing after the missing main protection was explicitly reported. This authorizes the bounded Goal settings deployment and the declared independent Validator publication process.

- [x] AC-01: Version the exact server rules and tests that detect unsafe or drifted settings.
- [ ] AC-02: Activate rules, verify real required checks and independent merge, and confirm main CI and the local deployment.

The required checks have no bypass. A separate main update rule permits only App 4344831; it cannot bypass the check/review rules. Existing working data and OneDev ticket-207 are preserved.

Pre-publication validation: 735 product tests passed, 2 existing skips; 14 protection tests passed. Governance, Compose and declaration checks passed. CI uses explicit public-rule verification because GitHub hides bypass actors from read-only callers; deployment uses full administrator-visible readback. Hosted Python checks remain required; OneDev is not substituted.

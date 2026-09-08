# Ticket 096: Validate PR preflight against its authoritative target base

- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

SESSION_EXECUTION_AUTHORIZATION: continue the requested repair, tests and publication. Ticket-095 exposed a preflight that invoked governance without a base, letting a merged adoption ticket contribute unrelated paths. Keep the gate and all independent publication checks; pass the real remote target explicitly.

- [x] AC-01: Prove stale adoption history is not included, while unavailable or invalid remote target observations remain rejected.
- [ ] AC-02: Publish under active server rules, validate both Python versions and resume ticket-095 with the installed fix.

Validation: 35 focused and 743 full tests passed (2 existing full-suite skips). The actual ticket-095 preflight passes with this candidate against the unchanged managed governance gate and authoritative remote base. The same current gate, configured remote, independent Validator and server rules remain required. Publication runs this tested CLI candidate through its ordinary Goal workflow.

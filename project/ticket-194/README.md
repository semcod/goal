# Ticket 194: Align declared external status checks with the active main ruleset

- **ID**: ticket-194
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-23

## Goal and scope

Declare the existing OneDev check alongside all four hosted checks and verify their exact required entries without changing live GitHub protection. SESSION_EXECUTION_AUTHORIZATION: user requests tested merges and explicitly hands off this ticket on 2026-10-23.

## Acceptance criteria

- [x] AC-01: All five existing gates validate; tests reject missing checks, wrong hosted providers and malformed external declarations. Existing review and publisher restrictions remain enforced.
- [ ] AC-02: Exact-head protected checks and independent Validator publication succeed.

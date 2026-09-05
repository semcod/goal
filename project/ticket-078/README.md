# Ticket 078: Tracking-only legacy delivery

- **ID**: ticket-078
- **Owner**: tom
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

## Goal and scope
Prevent bare goal -a from mutating README when synchronized Koru has only a modified existing ticket index. Preserve its bytes and staging; managed governance still runs first.

SESSION_EXECUTION_AUTHORIZATION: continuing user request to repair and publish goal -a, with Koru failure evidence.

## Acceptance criteria
- [x] AC-01: Modified tracked ticket index survives no-change delivery byte-identically, staged or unstaged.
- [x] AC-02: Implementation changes, renamed/deleted/untracked files and unpublished commits never qualify.
- [ ] AC-03: Managed governance and Python/Docker checks pass; publish through protected Goal delivery.

Validation: 660 tests passed, 2 skipped; managed governance and Docker Compose validation passed.

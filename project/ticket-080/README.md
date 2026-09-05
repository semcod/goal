# Ticket 080: Standard adoption release prerequisite

- **ID**: ticket-080
- **Owner**: tom
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

## Goal and scope
Adopt immutable new-project 0.20.7 required by the pre-commit freshness controller before publishing Goal 2.1.303.

SESSION_EXECUTION_AUTHORIZATION: continuing user repair/publication request; user authorized tag metadata repair, and this required immutable adoption follows the managed hook diagnostic.

## Acceptance criteria
- [x] AC-01: Managed package and pyproject binding match the approved immutable revision.
- [x] AC-02: Governance, Python tests and Docker checks pass.
- [ ] AC-03: Protected Goal delivery and Validator merge the adoption.

Validation: 691 Python tests passed, 2 skipped; immutable adoption check, managed gate, Docker Compose and whitespace checks passed.

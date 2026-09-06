# Ticket 075: Adopt workspace inventory repair

- **ID**: ticket-075
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-05

## Goal and scope

Adopt the published upstream repair through the managed Goal adoption path. new-project 0.20.5 is published at fd5dc4210eaf50bb96d02ddfea625bf46a85263f after protected ticket-187 merge.

## Acceptance criteria

- [x] AC-01: Adoption lock and pyproject bind the same published revision.
- [x] AC-02: .github no longer aborts the workspace inventory.
- [ ] AC-03: Managed gate and stack tests pass before protected publication.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: user requested repair/publication via goal -a and continued after the .github workspace audit failure. Only the published standard adoption and required binding are in scope.

## Validation

Goal adoption check is up to date at new-project 0.20.5 / fd5dc4210eaf50bb96d02ddfea625bf46a85263f. Managed scoped gate, 653 tests (2 skipped), Docker Compose and diff whitespace checks pass. The real Goal CLI inventory reads 90 checkouts including semcod/.github with no GOV-WORKSPACE-LIFECYCLE-003. Existing 101 lifecycle findings remain observations; this adoption authorizes no unrelated cleanup.

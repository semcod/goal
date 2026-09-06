# Ticket 082: Audit committed internal dependencies on schedule

- **ID**: ticket-082
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-05

## Authorization and scope

SESSION_EXECUTION_AUTHORIZATION: user requested continued dependency update automation. The previous weekly workflow used unsupported Python 3.11, listed runner packages and attempted a PR without changing a lockfile. Replace it with daily read-only evidence from the committed catalog and lock; ticket-aware update delivery remains separate.

## Acceptance criteria

- [x] AC-01: Bounded infrastructure intent and session authority recorded.
- [x] AC-02: Workflow uses Python 3.12, locked installation and audited external registry dependencies; excludes Goal's own editable project entry.
- [ ] AC-03: Governance, workflow-equivalent execution and hosted manual dispatch pass.

## Validation

Workflow-equivalent uv sync --locked and exact audit shell passed on the merged catalog and lock. Local JSON reports current costs, pfix and clickmd; Goal self-entry excluded as intended. Release base has passing Python 3.12/3.13 CI and Docker build. Hosted manual dispatch follows merge.

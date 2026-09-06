# Ticket 081: Align internal dependency integration and release metadata

- **ID**: ticket-081
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-05

## Authorization and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested continuation, publication through goal -a, current internal dependencies and ecosystem update automation. This material integration requires optimized costs, corrects package identity, provides an operator catalog and documents the merged dependency CLI. Release projections accompany those packaging changes.

## Acceptance criteria

- [x] AC-01: Bounded integration scope and session execution authority recorded.
- [x] AC-02: Metadata and lock require costs 0.2.0; catalog and usage describe actual update boundaries.
- [x] AC-03: Lock, tests, build, Docker and governance pass.
- [ ] AC-04: Protected PR delivery and verified PyPI publication of Goal 2.2.0.

## Validation

691 tests passed, 2 skipped on Python 3.13. Lock check, governance, wheel/sdist and Twine checks passed. Clean wheel installation on Python 3.12.13 reports Goal 2.2.0 and costs 0.2.0; dependency CLI help works. Docker build and version smoke passed. Publication evidence remains external.

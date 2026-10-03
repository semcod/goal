# Ticket 181: Exclude demonstration and foreign trees from automatic project detection

- **ID**: ticket-181
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-03

## Outcome and scope
Detect owned project manifests without treating demonstrations, fixtures or foreign checkouts as testable root packages. Two scoped material files; protected publication is authorized by the current continued-fixes session.

## Acceptance criteria
- [x] AC-01: Bounded discovery retains owned adapters and ignores excluded trees and symbolic links.
- [ ] AC-02: Full Python suite, governance, OneDev and independent protected merge pass.

## Boundaries
No dependency, version, bootstrap or approval policy changes. Preserve source failure reports privately.

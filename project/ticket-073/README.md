# ticket-073: Expose adopted branch intent reconciliation in Goal

- **ID**: ticket-073
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

## Outcome
Provide a bounded, read-only CLI for the independently pinned adopted reconciliation checker. Older standard packages fail closed with adoption guidance. No branch is deleted and no source-branch intent is fabricated.

## Acceptance criteria
- [x] AC-01: Verify the externally supplied lock digest, managed checker hash and isolated execution boundary.
- [x] AC-02: Preserve ready/unresolved/invalid results and never turn report conformance into deletion authority.
- [ ] AC-03: Positive/adversarial, regression, governance and Docker checks pass; publish through exact-head protected review.

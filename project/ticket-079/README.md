# Ticket 079: Material-only no-change remediation

- **ID**: ticket-079
- **Owner**: tom
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

## Goal and scope
Honor GOV-MATERIAL-001 remediation by returning an external no-change receipt without commit/PR for synchronized default HEAD and only a modified tracked ticket index. Require a well-formed managed JSON report containing exactly that finding. Other failures remain fatal.

SESSION_EXECUTION_AUTHORIZATION: continuing user-requested repair and publication of goal -a; actual Koru verification found the material-only gate result.

## Acceptance criteria
- [ ] AC-01: Existing modified ticket index is preserved with material-only gate diagnostics.
- [ ] AC-02: Malformed reports, additional errors, explicit delivery requests and pending implementation remain blocked.
- [ ] AC-03: Real Koru no-change, Python tests, governance and Docker validation pass before protected publication.

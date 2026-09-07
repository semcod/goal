# Local CI publication policy — adopted reference

Canonical policy: [Wellmanifest/new-project 0.20.10](https://github.com/wellmanifest/new-project/blob/d5f77d83b3752477cfb95a535d0e1ce77f148576/docs/information/local-ci-publication.md).
Source revision: `d5f77d83b3752477cfb95a535d0e1ce77f148576`.
Canonical document SHA-256: `44803480f1d51f64eec81a62335b6725747f01b5f2de78105ebfc4017a7922c6`.

This managed file is an adoption reference. The authored document and its
metadata remain at the canonical Wellmanifest home; do not register this copy
as a new document owned by the adopting repository.

For Semcod and Subactor, prefer protected local OneDev verification followed
by the independent local Validator App. Resolve the actual protected profile,
observe existing reconciliation, require fresh verification of the PR head
merged with the current base, then invoke the trusted local Validator adapter
under existing publication authorization. The supported local adapter is
`subactor/validator-agent/bin/run-local-direct-pr.sh`; use its protected deployed
checkout and existing key reference as specified by the canonical runbook.
Never self-approve or merge directly.

A hosted Actions billing or capacity error does not prove local CI is unavailable.
Use hosted dispatch only when explicitly selected by the protected deployment.
Preserve all additional repository checks and required operating systems.
Retire a hosted check only after equivalent deployed local canary evidence and
independent policy review. Missing profiles are gaps, never successful coverage.

Keep declared, configured, deployed, verified and published evidence separate.
Read the canonical policy for the complete workflow, authority boundaries and
migration requirements. This reference grants no execution or merge authority.

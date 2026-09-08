# Ticket 090: Govern artifact upload update

- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Owner**: codex

## Goal and scope
Publish the upgrade requested by PR #124, pinning upload-artifact v7.0.1 to its immutable revision. A replacement PR carries this ticket in its first material commit because the original Dependabot commit predates a required intent. Preserve the original remote history.

## Acceptance criteria
- [x] AC-01: Artifact name, path, missing-file handling and workflow permissions remain unchanged; upstream release SHA, archive default and Node runtime are verified.
- [ ] AC-02: Managed and stack checks pass on current main plus the upgrade; protected Validator merges the exact reviewed head.

Prerequisite: ticket-091 publishes new-project 0.20.12. Upstream v7.0.1 resolves to 043fb46d1a93c77aae656e7c1c64a875d1fc6a0a, uses Node 24 and retains archive=true by default. Full Goal tests passed in the prerequisite (723 passed, 2 skipped); the replacement retains required CI.

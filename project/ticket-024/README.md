# Ticket 024: Preserve dry-run state and fail closed on delivery errors

- **ID**: ticket-024
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-10

## Goal and scope

Make dry-run observably read-only, make every failed Git push terminate the
delivery with a non-zero result, and preserve every declared Python test tool
set when Goal synchronizes an UV-managed environment.

## Acceptance criteria

- [x] AC-01: The user instructed the agent to continue the autonomous work.
- [x] AC-02: A dry-run neither creates nor rewrites `goal.yaml`.
- [x] AC-03: A failed non-governed push exits non-zero and cannot emit a
  successful workflow summary.
- [x] AC-04: UV bootstrap/synchronization includes whichever of `dev` and
  `test` are declared, preventing removal of their verification tools.
- [x] AC-05: Focused tests, full tests, governance and Docker checks pass.

## Validation evidence

- Seven ticket regressions pass, covering absent and existing `goal.yaml`, a
  failed remote push, both UV verification sets, invalid self-update evidence,
  and protection of the canonical CLI command from the legacy push shim.
- The related delivery/bootstrap suite passes with 163 tests and one optional
  skip; the complete suite passes with 519 tests and two optional skips.
- Importing `goal.push.commands` no longer replaces the registered
  `goal.cli.push_cmd` callback, so sequential tests and runtime policy cannot
  accidentally invoke an unpatched legacy workflow.
- Goal resolves Diagit's synchronization command as `uv sync --extra test`.
- Ruff passes for the new regression module; syntax checks pass for all five
  changed implementation/test files.
- Governance passes with 0 errors and 0 warnings.
- Docker image `sha256:6a42109443c1d0f20150aa268396b0c8c1c966264d7cb27b3c06fc8268f3e17d`
  builds successfully and reports Goal 2.1.292 with runtime networking disabled.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Session authorization

The user explicitly said to continue after these three Goal defects were
reported. This is `SESSION_EXECUTION_AUTHORIZATION` for the bounded paths in
`intent.json`; no additional implementation confirmation is required.

## Boundary

This ticket does not change version selection, registry credentials, release
ordering, GitHub protection, governance policy or public CLI syntax. The
application slice remains deliberately unversioned; publication belongs to a
separate integration ticket after protected merge.

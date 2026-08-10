# Ticket 024: Preserve dry-run state and fail closed on delivery errors

- **ID**: ticket-024
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
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

- Nine ticket regressions pass, covering absent and existing `goal.yaml`, a
  failed remote push, both UV verification sets, invalid self-update evidence,
  protection of the canonical CLI command from the legacy push shim, and the
  cost-badge skip boundary across bootstrap and commit phases, and isolation of
  Goal-only controls from the project test environment.
- The related delivery/bootstrap suite passes with 165 tests and one optional
  skip; the complete suite passes with 521 tests and two optional skips.
- Importing `goal.push.commands` no longer replaces the registered
  `goal.cli.push_cmd` callback, so sequential tests and runtime policy cannot
  accidentally invoke an unpatched legacy workflow.
- Goal resolves Diagit's synchronization command as `uv sync --extra test`.
- Ruff passes for the new regression module; syntax checks pass for all five
  changed implementation/test files.
- Governance passes with 0 errors and 0 warnings.
- Docker image `sha256:6a42109443c1d0f20150aa268396b0c8c1c966264d7cb27b3c06fc8268f3e17d`
  builds successfully and reports Goal 2.1.292 with runtime networking disabled.
- PR #50 passed target CI on Python 3.12 and 3.13, then validator-agent
  approved exact head `a1c11f4e3b2a23b2c52f2d53ae07d9f464007f57` in run
  `31425350829`.
- The protected exact-head merge completed as
  `4fae2ec251f6181f15c02c53fe3078ea51c96c9b`; the remote ticket branch was
  deleted and no pull request remains open.

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

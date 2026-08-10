# Ticket 019: Publish Goal 2.1.291

- **ID**: ticket-019
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-10
- **Work classification**: `SERVICE / integration`

## Goal and scope

Publish the ticket-018 post-release boundary repair as Goal 2.1.291. The
release must use Goal's evidence-based version decision, synchronize every
managed version carrier and derived lock/readme metadata, pass the complete
test and build gates, merge through exact-head validation, and be installed
from the public PyPI index before it is considered complete.

## Acceptance criteria

- [ ] AC-01: `goal check-versions` selects `normal-bump -> 2.1.291` from the
  PyPI 2.1.290 baseline and the committed ticket-018 package source.
- [ ] AC-02: `VERSION`, `pyproject.toml`, `goal/__init__.py`, `uv.lock`,
  `README.md`, and `CHANGELOG.md` consistently describe 2.1.291.
- [ ] AC-03: The full Python suite and package build pass from the synchronized
  release tree.
- [ ] AC-04: The release PR passes Python 3.12/3.13 CI and exact-head validator
  approval before merge.
- [ ] AC-05: Goal 2.1.291 is visible on PyPI and imports as 2.1.291 in a fresh
  environment installed only from the public index.

## Session authorization

The user explicitly requested autonomous continuation, testing, publication,
dependency refresh and downstream Goal updates. This bounded release executes
that authorization without another confirmation. Registry credentials remain
environment-owned and are used only by the governed publish command.

## Boundary

Only atomic release metadata, build evidence, this ticket and the ticket index
may change. No application source, runtime dependency constraint, governance
policy, GitHub workflow or downstream dirty repository is modified here.

## Participants

- Human participant: unresolved; no user-* file was created.
- Agent participant: [ai-codex.md](ai-codex.md)

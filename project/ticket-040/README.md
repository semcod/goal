# Ticket 040: Publish Goal 2.1.295 with adoption proof repairs

- **ID**: ticket-040
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Release the merged ticket-037/038 production standard proof and ticket-039
bootstrap scoping repair as Goal 2.1.295. Use the real governed pull-request
workflow to synchronize the five atomic release carriers, including the
expected legacy `pfix` dev marker, then publish only from the exact clean merged
`main` and verify public registry/install evidence.

## Acceptance criteria

- [ ] AC-01: The real high-level `goal -a` PR flow creates no unexpected
  tracked changes: only the five declared release carriers plus ticket metadata
  change, and disposable `.venv` state is removed with the worktree.
- [ ] AC-02: VERSION, `pyproject.toml`, `goal/__init__.py`, README badges and
  `uv.lock` synchronize exactly to 2.1.295; the runtime `costs` requirement is
  unchanged and only dev `pfix` gains its compatibility marker.
- [ ] AC-03: Full tests, governance, package, Docker, protected CI and exact-head
  Validator Agent approval pass before merge.
- [ ] AC-04: Clean merged `main` publishes exactly one wheel and one sdist for
  2.1.295 and creates an annotated tag plus final GitHub Release.
- [ ] AC-05: A fresh public-index environment reports Goal 2.1.295 and the
  installed CLI enforces both standard tag and GitHub Release proof.

## Boundary

- Source code is already merged; this ticket owns only atomic release carriers
  and its own governance/evidence files.
- Top-level CHANGELOG mutation is disabled to stay within the five-file release
  budget; ticket changelog contains the bounded release narrative.
- Registry publication occurs only after the validated PR is merged and the
  local tree equals authoritative remote `main`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

# Ticket 064: Authenticate GitHub Release verification for governance adoption

- **ID**: ticket-064
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-31

## Goal and scope

Make Goal's published-Release preflight use authenticated GitHub metadata,
resolve the latest final release to its immutable peeled commit and prepare a
pre-commit standard update only under an exact staged adoption ticket. Then
atomically adopt the verified `wellmanifest/new-project` release. A missing or
invalid Release must still fail closed.

## Acceptance criteria

- [x] AC-01: A GitHub CLI token is sent only as an HTTPS Authorization header
      for canonical Release metadata.
- [x] AC-02: Missing or invalid Release metadata remains a deterministic
      refusal.
- [x] AC-03: Goal tracks and validates the exact 0.19.18 standard payload;
      only the two formerly ignored standard files become trackable.
- [x] AC-04: `goal governance adopt --latest --pre-commit --ticket` resolves
      an annotated final release and mutates only under matching staged
      `IN_PROGRESS` governance-adoption evidence.
- [x] AC-05: A current pin is a no-op; a prepared update stops the initiating
      commit for explicit review and restaging.

## Validation

- Governance adoption command tests: 35 passed.
- Full Goal suite: 627 passed, 2 skipped.
- Scoped Ruff, staged exact-diff governance and whitespace checks pass.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

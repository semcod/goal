# Ticket 035: Commit generated workflow artifacts before final summary

- **ID**: ticket-035
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-11

## Goal and scope

Keep `goal -a` clean after it finishes. Slow-test planfile tickets must be
generated and staged before the workflow commit, while the final summary stays
read-only. The Python bootstrap's credential-free `.env.example` template must
remain versionable, and `.gitignore` insertion must compare exact patterns
rather than misleading substrings.

## Acceptance criteria

- [x] AC-01: The user's instruction to continue repairing Goal supplies
  bounded local execution authorization.
- [x] AC-02: Generated slow-test ticket artifacts are staged before commit and
  included in commit statistics.
- [x] AC-03: Final summary rendering cannot mutate the planfile.
- [x] AC-04: `.env.example` is considered safe and exact `.gitignore` pattern
  comparison is idempotent.
- [ ] AC-05: Focused/full tests, Ruff, governance, build and Docker pass.

## Validation evidence

- 20 focused workflow and validator tests pass.
- The Git fixture proves the planfile is staged before commit; the summary
  fixture proves byte-for-byte read-only behavior.
- Changed-file Ruff and deterministic governance pass.

## Session authorization

The request to continue local Goal repair is `SESSION_EXECUTION_AUTHORIZATION`
for this ticket. Push, merge, publication, release metadata and secret access
remain excluded.

## Boundary

This ticket owns pre-commit generation of the known slow-test planfile artifact
and exact safety classification of the generated environment template. It does
not change ticket policy, dependency metadata, publishing or arbitrary secret
file handling.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

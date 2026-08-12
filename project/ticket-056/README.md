# Ticket 056: Keep committed pull-request resume mutation-free

- **ID**: ticket-056
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-12

## Goal and scope

Make the canonical bare `goal -a` path safely resume one already committed,
governed pull-request candidate. Today `goal -a` does not forward `--ticket`;
without that hidden subcommand option Goal skips the committed-candidate path,
runs mutating bootstrap/doctor logic and can generate environments, config and
sample tests inside a reviewed checkout. Even with an explicit ticket, the
resume path writes `.governance/delivery-events.jsonl` before it revalidates
the candidate, so the audit event itself makes the checkout dirty.

For pull-request delivery only, Goal must resolve an omitted ticket from
exactly one `IN_PROGRESS` governance ticket before project bootstrap. Zero or
multiple active tickets fail closed with an explicit `--ticket` instruction.
Explicit tickets keep precedence. Delivery events move to the Git common
directory so they persist across linked worktrees without changing the target
tree. Package bootstrap, doctor behavior outside committed PR resume, and
other delivery modes remain unchanged.

## Acceptance criteria

- [x] AC-01: The user's request to continue implementation and fix Goal records
  `SESSION_EXECUTION_AUTHORIZATION` for this bounded repair.
- [x] AC-02: Bare governed `goal -a` resolves exactly one active ticket and
  resumes a clean committed candidate before bootstrap, doctor, TODO handling,
  staging, versioning or commit generation.
- [x] AC-03: An explicit `--ticket` keeps precedence; zero or multiple active
  tickets fail before mutation and name the required corrective option.
- [x] AC-04: Delivery events are appended below the Git common directory and
  never alter `git status` in a primary or linked worktree.
- [x] AC-05: Focused regressions, the full Python suite, Ruff, governance,
  package build and Docker smoke pass before protected PR delivery.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Authorization

The user explicitly requested continued implementation, testing and push in
this session. This authorizes execution inside `intent.json`; it is not trusted
merge approval. Exact-head Validator evidence remains mandatory.

## Reproduction evidence

- In the real todo2code ticket-075 delivery, bare `goal -a` entered doctor
  instead of resume and created root/nested `.venv`, `.env`, `uv.lock`, a
  sample Python test and tool config in `pyproject.toml` before it was stopped.
- The earlier explicit-ticket resume wrote
  `.governance/delivery-events.jsonl` before candidate revalidation; the file
  had to be locally ignored for the unchanged candidate to pass.

## Non-goals

- No weakening of the exact candidate/base/ticket commit binding.
- No automatic selection when more than one active ticket exists.
- No change to doctor/bootstrap for genuine uncommitted delivery work.
- No version, dependency, public API or release change.

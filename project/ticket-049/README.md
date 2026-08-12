# Ticket 049: Resume governed PR delivery after pre-PR interruption

- **ID**: ticket-049
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Repair the governed `pull-request` retry exposed twice by ticket 048. When a
Goal run has already tested and committed an authorized ticket diff but fails
before it can create/push the controlled PR branch, the next run currently
returns early as `No changes to commit`. Allow that next run to resume only
from a clean, ticket-bound, fast-forward commit range ahead of the authoritative
remote base, rerun tests, and then use the existing governed PR delivery path.

## Acceptance criteria

- [ ] AC-01: A clean `pull-request` retry recognizes already committed ticket
  work only when remote base is an ancestor and every ahead commit is bound to
  the requested ticket.
- [ ] AC-02: An eligible retry reruns project tests and creates or reuses the
  controlled exact-head PR without version, changelog, tag or registry effects.
- [ ] AC-03: Equal, behind, dirty, unbound and divergent histories do not enter
  resume delivery; ambiguous or unsafe histories fail closed.
- [ ] AC-04: Focused/full tests, Ruff, governance and Docker pass without new
  dependencies or a package version change.

## Risks

- A generic "ahead means push" rule could publish an unrelated local commit.
  Resume therefore requires a clean tree, authoritative remote-base ancestry,
  a non-empty ahead range, and the exact `[ticket-NNN] ` prefix on every commit.
- A merged or merely behind branch is a no-op, not a new PR candidate. A
  genuinely divergent branch is reported and never pushed automatically.
- Resume bypasses commit creation, not verification: governance already runs
  before bootstrap and the full configured test stage must pass again.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

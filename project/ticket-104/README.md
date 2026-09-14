# Ticket 104: Accept Conventional Commits ticket scopes in governed delivery

- **ID**: ticket-104
- **Owner**: agent:codex-goal-ticket104
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-14

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: on 2026-09-14 the user approved implementing
the delivery-flow unblocking plan
(`subactor/docs/architecture/refactoring/delivery-flow-unblocking.md`, S5).

Governed pull-request resume accepts a committed candidate only when every
subject starts with `[ticket-NNN] `. Repositories whose commit-msg hook enforces
Conventional Commits (for example `semcod/giton`) reject that form, so a ticket
cannot be committed in a form both tools accept. This ticket also accepts a
Conventional Commit whose scope names exactly the ticket, e.g.
`build(ticket-004): title`, while still rejecting unbound or longer ids.

Non-goals: no change to how Goal writes its own commit titles or to push,
PR creation and governance checks.

## Acceptance criteria

Handoff, 2026-09-14: after the explicit ownership-transfer question, the user
repeated the instruction to correct this ticket. SESSION_EXECUTION_AUTHORIZATION
covers the bounded single-ticket binding fix and its regression cases. Preserve
the prior implementation and commit history; do not amend the report consumer's
commits or bypass publication checks. Previous layout owner:
claude-delivery-flow-unblocking-20260914. New editing session:
codex-goal-ticket104-handoff-20260914, controller fencing token 234.

The Conventional Commit scope must identify exactly one distinct numeric ticket,
equal to the requested ticket. Non-ticket component scopes and repetitions of the
same ticket identity remain compatible; multiple different ticket IDs fail for
each requested ticket. Regression cases cover both orders and extra scope parts.
Local correction validation: the complete delivery test module passed 69/69
tests; managed governance passed with zero errors/warnings, and git diff --check
passed. These are local results, not full-suite/platform CI or merge evidence.
The user continued with publication of the correction in the existing PR #149.
SESSION_EXECUTION_AUTHORIZATION permits a normal follow-up commit and push and
the independent protected delivery process, never history rewriting or direct
merge. Required Python 3.12/3.13 and governance checks must bind the new HEAD.

- [x] AC-01: `[ticket-NNN] title` and `type(ticket-NNN): title` (optionally with
  other scope parts or `!`) bind the ticket; `ticket-NNNN`, scope-less mentions
  and malformed subjects do not.
- [ ] AC-02: A clean committed candidate with a Conventional Commit ticket scope
  resumes governed pull-request delivery; the delivery test module passes.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

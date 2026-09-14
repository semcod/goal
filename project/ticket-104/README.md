# Ticket 104: Accept Conventional Commits ticket scopes in governed delivery

- **ID**: ticket-104
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
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

- [ ] AC-01: `[ticket-NNN] title` and `type(ticket-NNN): title` (optionally with
  other scope parts or `!`) bind the ticket; `ticket-NNNN`, scope-less mentions
  and malformed subjects do not.
- [ ] AC-02: A clean committed candidate with a Conventional Commit ticket scope
  resumes governed pull-request delivery; the delivery test module passes.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

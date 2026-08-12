# Ticket 052: Install the managed new-project remote lifecycle workflow

- **ID**: ticket-052
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-12

## Goal and scope

Install the exact managed GitHub remote-lifecycle workflow from published
`new-project v0.16.1`. Ticket 051 already integrated the governance-owned
checker that the workflow executes, so this infrastructure ticket changes only
the workflow plus its own governance evidence.

## Acceptance criteria

- [x] AC-01: `.github/workflows/new-project-governance.yml` is byte-identical
      to `wellmanifest/new-project@4e6ba5ec...` and its SHA-256 is recorded.
- [x] AC-02: The workflow is valid YAML, invokes the integrated managed checker
      and uses digest/commit-pinned actions from the published standard.
- [ ] AC-03: Full Goal tests and deterministic governance pass before a
      protected PR; Python 3.12/3.13 CI and exact-head Validator approval are
      required before merge.

## Boundary

- `.governance/**` and the package lock are governance-owned and excluded.
- Full `new-project` 0.16.1 adoption follows in a separate governance ticket.
- The source is the annotated published `v0.16.1` tag, peeled to
  `4e6ba5ec15873346446d67d8787f17f68f57f81e`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Validation evidence

- Source and target SHA-256 are both
  `9dd307f48368fea9438bb607e28e48cffcfe0ae4f231d77df86c384745bb68e9`;
  byte comparison passes.
- YAML structure loads successfully, both GitHub Actions are pinned to exact
  40-character commits, and the workflow invokes the ticket-051 checker.
- Deterministic governance passes with no errors or warnings. Full and hosted
  validation remain required before merge.

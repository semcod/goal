# Ticket 047: Publish Goal 2.1.297 source-hub health

- **ID**: ticket-047
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-12

## Goal and scope

Publish Goal 2.1.297 from the exact merged ticket-046 source-hub health repair.
Synchronize only the five established release carriers through a protected PR,
then publish the package, annotated tag and final GitHub Release exclusively
from the clean validated merge SHA. Verify a fresh public install and use that
package for the real `wellmanifest/new-project` ticket-065 health and delivery.

## Acceptance criteria

- [ ] AC-01: The governed high-level PR workflow synchronizes exactly VERSION,
  `pyproject.toml`, `goal/__init__.py`, README version badges and `uv.lock` to
  2.1.297, plus this ticket's evidence.
- [ ] AC-02: Full tests, scoped Ruff, governance, wheel/sdist and Docker pass;
  protected CI and Validator App approve the exact final PR head.
- [ ] AC-03: The clean merged `main` is retested before registry/tag/Release
  effects and produces exactly one wheel and one sdist for 2.1.297.
- [ ] AC-04: Annotated `v2.1.297`, final GitHub Release and PyPI artifacts all
  bind to the exact clean merge and immutable hashes are recorded.
- [ ] AC-05: A fresh public-index install reports 2.1.297 and that public CLI
  runs the real `new-project` source-hub health and ticket-065 PR delivery.

## Boundary

- No executable source belongs to this release ticket; implementation is
  already integrated by exact-head-approved PR #70.
- Top-level CHANGELOG is intentionally not rewritten; the bounded release
  narrative lives in this ticket.
- No registry, tag or Release action occurs before protected merge and clean
  merge validation. Existing immutable releases are never moved.
- The user's instruction to repair and continue is bounded
  `SESSION_EXECUTION_AUTHORIZATION`; independent approval remains external.

## Pre-publication evidence

- Accepted base is clean `main@d97ada6`; the ticket plan is a separate prior
  commit and no implementation source is part of this release diff.
- PyPI returns 404 for Goal 2.1.297 and neither annotated tag `v2.1.297` nor a
  GitHub Release exists before entering `PUBLICATION`.
- A clean-tree Goal probe with explicit target and patch bump performed no
  version write, commit, push, tag or registry action, confirming that the
  high-level workflow requires a declared pending release diff before its
  version stage.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

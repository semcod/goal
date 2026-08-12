# Ticket 047: Publish Goal 2.1.297 source-hub health

- **ID**: ticket-047
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Publish Goal 2.1.297 from the exact merged ticket-046 source-hub health repair.
Synchronize only the five established release carriers through a protected PR,
then publish the package, annotated tag and final GitHub Release exclusively
from the clean validated merge SHA. Verify a fresh public install and use that
package for the real `wellmanifest/new-project` ticket-065 health and delivery.

## Acceptance criteria

- [x] AC-01: The governed high-level PR workflow synchronizes exactly VERSION,
  `pyproject.toml`, `goal/__init__.py`, README version badges and `uv.lock` to
  2.1.297, plus this ticket's evidence.
- [x] AC-02: Full tests, scoped Ruff, governance, wheel/sdist and Docker pass;
  protected CI and Validator App approve the exact final PR head.
- [x] AC-03: The clean merged `main` is retested before registry/tag/Release
  effects and produces exactly one wheel and one sdist for 2.1.297.
- [x] AC-04: Annotated `v2.1.297`, final GitHub Release and PyPI artifacts all
  bind to the exact clean merge and immutable hashes are recorded.
- [x] AC-05: A fresh public-index install reports 2.1.297 and that public CLI
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
- The real high-level Goal flow selected `explicit-target -> 2.1.297`, passed
  581 tests with 2 existing skips, synchronized only the five declared release
  carriers plus ticket evidence, skipped registry/tag effects and opened PR
  #71 at candidate head `9c4ff9c`.
- All carriers agree at 2.1.297; governance and scoped Ruff pass. The candidate
  build produced exactly `goal-2.1.297-py3-none-any.whl`
  (`d592c494c0755c174ff90b6017d8b2256d0577fe02a85c06b43e640d386066ea`)
  and `goal-2.1.297.tar.gz`
  (`3b2719c5b451106e535f4e697b352b0473b4560f1a2092dda86f3733d8820147`).
- Docker built candidate image
  `sha256:fc1f80ed7c532c99e20fb915926beaa624881653e1a3e923e05e6f74e99ba66e`;
  the image and all build distributions were removed after recording hashes.

## Publication evidence

- PR #71 exact head `354121923c7ceb186dc6378e75686347dd3a3c09`
  passed protected Python 3.12/3.13 CI. Validator App run `31587897149`
  produced exact-head approval review `4915531453`; trusted merge
  `866bebee75b118f2285bb90a70284925f8d89d68` has that head as parent 2
  and an identical tree.
- The clean merge passed 581 tests with 2 existing skips, Ruff, governance,
  wheel/sdist and Docker validation before publication. No candidate artifact
  or image was reused as registry evidence.
- PyPI 2.1.297 publishes wheel SHA-256
  `01876c5bc85dccc824d9c8a0b52978c20b096886d42845346b9a585ec7d39f9f`
  and sdist SHA-256
  `7e4172b768865aaa1726af51343537e425e361c9bfe3a3b477dca291a116d3fa`;
  independent downloads from both PyPI and GitHub Release matched them.
- Annotated `v2.1.297` peels to trusted merge `866bebee...`; final GitHub
  Release was published at 2026-08-12T10:41:16Z and a fresh public-index
  Python 3.13 install reported Goal 2.1.297.
- That public CLI produced `GOV-HUB-PASS` for the real new-project candidate
  (15 JSON documents, 9 shell suites), delivered ticket-065 as PR #96, and the
  published new-project v0.15.0 pilot subsequently reported 33 read-only glon
  changes without altering the user's files.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

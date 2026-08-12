# Ticket 040: Publish Goal 2.1.295 with adoption proof repairs

- **ID**: ticket-040
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Release the merged ticket-037/038 production standard proof and ticket-039
bootstrap scoping repair as Goal 2.1.295. Use the real governed pull-request
workflow to synchronize the five atomic release carriers, including the
expected legacy `pfix` dev marker, then publish only from the exact clean merged
`main` and verify public registry/install evidence.

## Acceptance criteria

- [x] AC-01: The real high-level `goal -a` PR flow creates no unexpected
  tracked changes: only the five declared release carriers plus ticket metadata
  change, and disposable `.venv` state is removed with the worktree.
- [x] AC-02: VERSION, `pyproject.toml`, `goal/__init__.py`, README badges and
  `uv.lock` synchronize exactly to 2.1.295; the runtime `costs` requirement is
  unchanged and only dev `pfix` gains its compatibility marker.
- [x] AC-03: Full tests, governance, package, Docker, protected CI and exact-head
  Validator Agent approval pass before merge.
- [x] AC-04: Clean merged `main` publishes exactly one wheel and one sdist for
  2.1.295 and creates an annotated tag plus final GitHub Release.
- [x] AC-05: A fresh public-index environment reports Goal 2.1.295 and the
  installed CLI enforces both standard tag and GitHub Release proof.

## Boundary

- Source code is already merged; this ticket owns only atomic release carriers
  and its own governance/evidence files.
- Top-level CHANGELOG mutation is disabled to stay within the five-file release
  budget; ticket changelog contains the bounded release narrative.
- Registry publication occurs only after the validated PR is merged and the
  local tree equals authoritative remote `main`.

## Pre-merge evidence

- The exact high-level command selected `normal-bump -> 2.1.295`, ran 560 tests
  with 2 existing skips, committed the declared scope and created PR #65.
- The committed diff contains exactly the five release carriers plus ticket
  governance. Runtime `costs>=0.1.53` is unchanged; only optional-dev `pfix`
  gained `python_version >= '3.10'` and the lockfile equivalent.
- `.env`, `.venv` and `goal.egg-info` are ignored local bootstrap artifacts and
  are absent from the PR. They will be removed with the disposable worktree
  after terminal delivery rather than by an unsafe partial cleanup.
- The first CLI attempt rejected misplaced `--ticket` before side effects. A
  second attempt stopped at an invalid empty component path in the ticket DSL,
  also before bootstrap; the intent was corrected and the gate passed.

## Terminal evidence

- PR #65 passed Python 3.12/3.13 CI and received deterministic Validator Agent
  approval for exact head `c37252d75035e6abb20b75fd23b156d68869aa7e`.
  GitHub merged it as `main@11561fd3eed757eb2a0143c206b38577490389ba`.
- Governance passed with zero errors/warnings, package build produced one wheel
  and one sdist, and Docker built image
  `sha256:4db175432191215939a40b5337df78b8b49c2c5244a425714d68f535ee0c383e`.
- Governed `publish-only` ran from clean `main`, repeated all 560 passing tests
  (2 skipped), and published exactly the two 2.1.295 artifacts. Their public
  PyPI SHA-256 values are `477d8bc960787d6c74c79a5c2707b9cbd06d47449c85216a04e3d7a63d1c51e8`
  (wheel) and `f2bb0bb03d76140d8231af70649abbcde61c8db332a8e4d3e0c4e35275075529`
  (sdist).
- Annotated tag `v2.1.295` peels exactly to the merge commit. The final,
  non-draft, non-prerelease GitHub Release was published with both artifacts.
- A fresh Python 3.13 environment installed `goal==2.1.295` with
  `--no-cache-dir` from `https://pypi.org/simple` and reported that exact CLI
  version. Against live glon, the installed CLI rejected unpublished
  `new-project` main because the release tag identified another revision, then
  accepted v0.14.1 tag/Release proof and reached the expected read-only drift
  report without modifying the project.
- GitHub removed the remote PR head automatically. The complete disposable
  worktree, local branch and validation image were removed after ancestry
  proof; the source tree remained clean and equal to `origin/main`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

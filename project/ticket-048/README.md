# Ticket 048: Allow artifactless GitHub Releases for generic repositories

- **ID**: ticket-048
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Repair the `create_on_tag` channel exposed by the real
`wellmanifest/new-project` v0.16.0 publication. Goal 2.1.297 successfully
created and pushed the annotated tag, then skipped the configured GitHub
Release because a generic Governance Hub deliberately has no `dist/*` package
artifacts. A safe retry also needs to reuse that tag only when it is annotated
and peels to the clean current HEAD.

## Acceptance criteria

- [x] AC-01: A configured generic `create_on_tag` release succeeds without
  assets, while PyPI/registry fallback still requires matching artifacts.
- [x] AC-02: Clean governed `direct-main --force-publish` repairs a missing
  Release only from an existing annotated version tag peeled to exact HEAD;
  mismatched or lightweight tags fail closed.
- [x] AC-03: Focused/full tests, Ruff, governance and Docker pass without new
  dependencies or package-version changes.
- [x] AC-04: After exact-head approval and merge, the corrected Goal code
  completes the already-tagged `new-project` v0.16.0 GitHub Release.

## Risks

- Assetless Releases are valid for generic repositories but not a substitute
  for registry artifacts. The permissive flag is passed only by the generic
  create-on-tag path and is not read from broad defaults.
- An existing tag is trusted only after checking its object type and peeled
  commit locally; the governed push still fails if the remote ref conflicts.
- Release creation failure must abort governed direct-main instead of being
  reported as a successful complete publication.

## Evidence before PR

- The package fallback default still rejects a missing `dist/*`; only the
  generic create-on-tag caller passes the explicit assetless-release flag.
- Recovery accepts an existing version tag only when `git cat-file` identifies
  an annotated tag and its peeled commit equals the clean current `HEAD`.
- Governed direct-main now treats a configured GitHub Release failure as
  terminal; legacy ungoverned invocation retains its warning behavior.
- 30 focused tests and the complete suite (`588 passed, 2 skipped`) pass with
  scoped Ruff and `GOV-PASS`; no dependencies or version carriers changed.
- Wheel/sdist validation produced SHA-256
  `3f4323525d4e5d1cc3614478a57dfd30d48185e31d9759c28dbd3146f8417e0c`
  and `a00f706107150f048b2827cf76e47cbf7d50426f538e4b877312e60cd9f86071`.
  The pinned-base Docker build passed as
  `sha256:a5a7c4ec9e9c0ad50740caa27017214cd0e524ca9974aea8aa38eec763a281c1`;
  the validation image was removed.
- The ticket remains active through protected exact-head PR validation and
  trusted merge, before the downstream `new-project` Release repair.
- Public Goal initially refreshed the root AI-cost badge after its governance
  gate and committed that out-of-scope file. The same PR was corrected to a
  zero-net README diff before validation; the guarded retry disables cost
  badge mutation explicitly.
- PR #72 merged the first repair as `main@320ad3d`, but AC-04's real clean
  retry failed before tag recovery: version resolution selected
  `normal-bump -> 0.16.1` from the existing v0.16.0 baseline. No repository,
  tag or Release mutation occurred. The same active ticket returns to `EDIT`
  to bind the already-released generic version before the normal bump guard.

## Follow-up evidence before PR

- A full-workflow regression starts from `normal-bump: 0.16.0 -> 0.16.1` and
  proves the guarded retry publishes, pushes and mirrors exactly v0.16.0.
- Three negative cases prove disabled `create_on_tag`, registry/package
  projects and normal `already-bumped` first publication do not enter repair.
- 34 focused tests and the complete suite (`592 passed, 2 skipped`) pass with
  scoped Ruff and `GOV-PASS` on refreshed base `main@320ad3d`.
- Candidate wheel and sdist SHA-256 are
  `7f90cfd7214ec72db7e3d513b1550c2543e2410933becb48998f5edc39d2b41b`
  and `4a9d53992ead0b534711f6db0806619b267ee3866ea7b3816e14ad282396d9b2`;
  pinned-base Docker image
  `sha256:3f5b44dd485de8a49afd96376c7575c344c498bef00a80d69c510df7ef278590`
  built successfully. Temporary outputs and image were removed.
- PR #73 merged as `main@b214711` after exact-head CI and Validator approval.
  The real retry created final v0.16.0 without assets and without changing the
  immutable tag or main, but its title exposed the temporary clone directory
  instead of configured `project.name`. The same ticket returns to `EDIT` to
  make Release metadata canonical and reconcilable on an existing Release.

## Metadata-correction evidence before PR

- The release identity resolves from configured `project.name` with checkout
  directory only as a legacy fallback; `new-project` is stable across clones.
- Existing assetless Releases reconcile canonical title and notes, and any
  metadata edit failure remains terminal in governed direct-main.
- All interpolated `gh release` arguments are shell-quoted and the read-only
  Release probe now uses an argument vector without a shell.
- 36 focused tests and the full suite (`594 passed, 2 skipped`) pass with
  scoped Ruff and `GOV-PASS`; pinned-base Docker image
  `sha256:ecdc4e79bd5c1d51a487cc3c2bcf312a832ad56651e99c5b4b3aef34d5b25fd1`
  built successfully and was removed.

## Completion evidence

- PR #74 exact head `c65916ff11180115e482e2d5604166683e9ede62`
  passed protected Python 3.12/3.13 CI. Validator App run `31599336116`
  produced exact-head approval review `4916776878`; trusted merge
  `db2da6e7e4176f078d1e2a1bcec790db79f9c62a` has an identical PR tree.
- The clean merge passed 594 tests with 2 existing skips and `GOV-PASS`.
- The merged Goal flow selected
  `existing-tag-release-repair -> 0.16.0`, changed zero files and reconciled
  the existing Release to canonical title `new-project v0.16.0` and notes
  `Automated release v0.16.0` without creating package assets.
- The final Release is non-draft and non-prerelease at
  `https://github.com/wellmanifest/new-project/releases/tag/v0.16.0`.
  Annotated `v0.16.0`, local HEAD and remote `main` all resolve to unchanged
  `6800f0138bc9063eb2dacb0a8b797dedcafb7952`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

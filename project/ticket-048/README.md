# Ticket 048: Allow artifactless GitHub Releases for generic repositories

- **ID**: ticket-048
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-12

## Goal and scope

Repair the `create_on_tag` channel exposed by the real
`wellmanifest/new-project` v0.16.0 publication. Goal 2.1.297 successfully
created and pushed the annotated tag, then skipped the configured GitHub
Release because a generic Governance Hub deliberately has no `dist/*` package
artifacts. A safe retry also needs to reuse that tag only when it is annotated
and peels to the clean current HEAD.

## Acceptance criteria

- [ ] AC-01: A configured generic `create_on_tag` release succeeds without
  assets, while PyPI/registry fallback still requires matching artifacts.
- [ ] AC-02: Clean governed `direct-main --force-publish` repairs a missing
  Release only from an existing annotated version tag peeled to exact HEAD;
  mismatched or lightweight tags fail closed.
- [ ] AC-03: Focused/full tests, Ruff, governance and Docker pass without new
  dependencies or package-version changes.
- [ ] AC-04: After exact-head approval and merge, the corrected Goal code
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

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

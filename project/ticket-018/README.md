# Ticket 018: Stop post-release duplicate version bumps

- **ID**: ticket-018
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-10
- **Work classification**: `BUG / application`

## Goal and scope

Prevent a metadata-only Goal run after a publish-only release from selecting
the next patch merely because the remote Git tag still names the prior release.
Committed-source analysis must recognize the commit where every managed version
carrier first reached the current version and inspect only source changes after
that boundary. A complete pre-bump ahead of the registry must continue to
request publication, and real source committed after the boundary must still
request the next release.

## Acceptance criteria

- [x] AC-01: Goal 2.1.290 was published from synchronized version metadata, but
  a subsequent metadata-only `goal -a` reproduced a false 2.1.291 proposal.
- [x] AC-02: When all managed carriers reached the current version after the
  last tag, source already preceding that transition is not reported again.
- [x] AC-03: Real package source committed after the transition remains
  publishable, and existing pre-bump/version-resolution behavior stays green.
- [x] AC-04: Focused history/version tests and the full Python suite pass.
- [x] AC-05: Fresh-base governance and exact-head protected delivery pass.

## Session authorization

The user explicitly requested autonomous continuation, testing and publication
of the Goal version-resolution work. This directly reproduced regression is a
bounded prerequisite and proceeds without another confirmation. Trusted merge
approval remains external and exact-head bound.

## Reproduction evidence

After PyPI exposed 2.1.290 while the latest reachable Git tag was v2.1.289,
`goal -a --no-publish --delivery-mode pull-request` reported both
`goal/__init__.py` and the already-published `goal/publish/changes.py` as new
source and selected `normal-bump -> 2.1.291`. The generated bump was reverted
before merge in PRs #32 and #33; 2.1.291 was never published.

## Implementation evidence

- Managed carriers with one synchronized current value now identify the first
  post-tag commit at which all of them reached that value.
- Committed-source analysis uses that transition as its effective release
  boundary and conservatively falls back to the reachable tag when history is
  missing or ambiguous.
- Focused regression/version tests: `27 passed`.
- Full Python suite: `510 passed, 2 skipped`.
- Fresh-base governance: `GOV-PASS` with zero errors and warnings.

## Boundary

Only version-transition history detection, committed-source classification,
focused regression tests and this ticket's evidence may change. No package
version, dependency, registry artifact, public CLI or governance policy change
is authorized.

## Participants

- Human participant: unresolved; no user-* file was created.
- Agent participant: [ai-codex.md](ai-codex.md)

## Publication

- Governed delivery produced [PR #34](https://github.com/semcod/goal/pull/34).
- CI passed on Python 3.12 and 3.13.
- `ifuri-validator-agent` approved exact head
  `a96e79f86d7c3194a0a14c5bfca41777e6d4466a`.
- The protected PR merged as
  `114d62a3f2b37ff89f2ee05bcd2d142cd06d6609`.
- Package publication is intentionally handled by a subsequent release slice;
  this application ticket did not mix release metadata into its diff.

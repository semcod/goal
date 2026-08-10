# Ticket 011: Eliminate duplicate docs-only commit attempt

- **ID**: ticket-011
- **Owner**: session user (identity unresolved)
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-10
- **Work classification**: `SERVICE / delivery`

## Goal and scope

Make docs/metadata-only delivery perform exactly one commit attempt, never let
the test suite commit into the repository executing the tests, and stop before
publish/tag/push when the real commit fails.  Preserve the `no-release`
decision: no version bump, release tag or registry publication is introduced.

## Acceptance criteria

- [x] AC-01: The user approved continuation after the duplicate commit symptom
  was reported.
- [x] AC-02: The metadata-only workflow test cannot execute a real Git commit
  in its caller's repository.
- [x] AC-03: A successful docs-only workflow requests exactly one plain commit,
  skips version bump/publication/tag and can continue to push.
- [x] AC-04: A failed docs-only commit aborts before publish, tag or push and
  cannot be reported as a successful workflow.
- [x] AC-05: Focused tests, the full suite and governance validation pass.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Session authorization

After the completed ticket-010 delivery explicitly identified the remaining
duplicate empty-commit report, the user instructed the agent to continue.  This
authorizes this narrowly scoped correction and transition to
`IN_PROGRESS / EDIT`.

## Boundary

This ticket does not change version selection, release publication, registry
credentials, delivery policies or GitHub configuration.

## Validation evidence

- Metadata-only focused E2E cases: 3 passed on Python 3.13 and Python 3.12.
- Full push E2E module: 38 passed.
- Full Python 3.13 suite: 506 passed, 2 optional skips.
- Test-isolation invariant: Git `HEAD` was identical before and after the full
  suite and both focused runs.
- Ruff on changed source/tests: PASS.
- Governance check: PASS (0 errors, 0 warnings).
- Equivalent Python 3.12 container matrix: 8 project types passed, 0 failed,
  with runtime networking disabled.

## Infrastructure observation

The repository `integration/Dockerfile` still uses Python 3.11 although the
package requires Python 3.12 or newer, so its build fails before tests.  The
same matrix passed in a temporary Python 3.12 image; no infrastructure file was
changed by this application ticket.

## Delivery evidence

- Governed release command: `goal --ascii --delivery-mode direct-main -a`.
- Release: `goal 2.1.289`; public PyPI exposes the package and `uvx` reports
  `goal, version 2.1.289`.
- Release commit and annotated tag target:
  `f2c6d3b76c72225abd59293fd07f4bdd3eab1e4d` / `v2.1.289`.
- Production workflow ran 506 tests with 2 optional skips, then created exactly
  one release commit after the ticket merge; no nested test commit appeared.

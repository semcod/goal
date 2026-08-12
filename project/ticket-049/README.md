# Ticket 049: Resume governed PR delivery after pre-PR interruption

- **ID**: ticket-049
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Repair the governed `pull-request` retry exposed twice by ticket 048. When a
Goal run has already tested and committed an authorized ticket diff but fails
before it can create/push the controlled PR branch, the next run currently
returns early as `No changes to commit`. Allow that next run to resume only
from a clean, ticket-bound, fast-forward commit range ahead of the authoritative
remote base, rerun tests, and then use the existing governed PR delivery path.

## Acceptance criteria

- [x] AC-01: A clean `pull-request` retry recognizes already committed ticket
  work only when remote base is an ancestor and every ahead commit is bound to
  the requested ticket.
- [x] AC-02: An eligible retry reruns project tests and creates or reuses the
  controlled exact-head PR without version, changelog, tag or registry effects.
- [x] AC-03: Equal, behind, dirty, unbound and divergent histories do not enter
  resume delivery; ambiguous or unsafe histories fail closed.
- [x] AC-04: Focused/full tests, Ruff, governance and Docker pass without new
  dependencies or a package version change.

## Risks

- A generic "ahead means push" rule could publish an unrelated local commit.
  Resume therefore requires a clean tree, authoritative remote-base ancestry,
  a non-empty ahead range, and the exact `[ticket-NNN] ` prefix on every commit.
- A merged or merely behind branch is a no-op, not a new PR candidate. A
  genuinely divergent branch is reported and never pushed automatically.
- Resume bypasses commit creation, not verification: governance already runs
  before bootstrap and the full configured test stage must pass again.

## Evidence before PR

- The read-only classifier requires one authoritative remote base, a clean
  tree, base ancestry, a non-empty diff and exact `[ticket-049] ` binding for
  every ahead commit. Equal/behind histories return no candidate; unbound and
  divergent histories fail closed.
- The orchestrator reruns configured tests, reclassifies the candidate after
  testing and requires immutable base/HEAD/files before calling the existing
  governed `deliver_pull_request`. It returns before all version, changelog,
  tag, registry and Release stages.
- 47 focused tests and the complete suite (`600 passed, 2 skipped`) pass with
  scoped Ruff and `GOV-PASS`; no dependency or version carrier changed.
- Candidate wheel and sdist SHA-256 are
  `e2cbd5b9ee198f3826b9bd6b5e3a63d40f45e7ab9847de38c32e8f382ab3ae10`
  and `9eecae69a0c6a526a54c784bc5ac5214e5ba60ec4b36c676911a25bef1454e7c`.
  Pinned-base Docker image
  `sha256:034faf2bd3fac4a8520464156df142d67878d0e5b45ec1f290a508f87edb0e29`
  built successfully; temporary distributions, build outputs and image were
  removed.

## Closure evidence

- PR #76 froze candidate HEAD
  `a297cf96b075853ca0de9fb7baa4ee7ac5d85308`; protected Python 3.12 and
  Python 3.13 checks passed.
- Validator GitHub App run `31601902913` approved that exact HEAD in review
  `4917056332`; the advisory LLM verdict was not the approval trust root.
- GitHub created merge commit
  `7534d1ab275f578de27801dce83c2b8d59ff91a6` with the approved candidate as
  its exact second parent and an identical resulting tree.
- A fresh detached worktree at the merge passed the complete suite
  (`600 passed, 2 skipped`), scoped Ruff and `GOV-PASS`; the worktree was
  removed afterward.
- A repository-wide Ruff diagnostic still reports 87 pre-existing findings
  outside ticket 049's changed paths. The four changed source/test files pass
  Ruff and no out-of-scope cleanup was folded into this regression repair.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

# Ticket 058: Make Python publish retries idempotent

- **ID**: ticket-058
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-12

## Goal and scope

Make every Twine-based Python publication idempotent, including repositories
whose tracked `goal.yaml` predates the current built-in default. The runtime
must add `--skip-existing` before executing a configured Twine upload, while
doctor PY013 must diagnose and auto-migrate both a stale distribution pattern
and a missing idempotency flag.

The defect was reproduced while completing Goal 2.1.299: the artifact already
existed on PyPI, but Goal rebuilt it and a legacy `twine upload` returned HTTP
400. The identical command with `--skip-existing` returned zero and explicitly
reported both artifacts as already present. No registry object was replaced.

## Acceptance criteria

- [x] AC-01: The user's instruction to repair Goal and continue records
  `SESSION_EXECUTION_AUTHORIZATION` for this bounded regression fix.
- [x] AC-02: Runtime resolution adds exactly one `--skip-existing` to Twine
  upload commands, preserves custom options and leaves non-Twine commands
  unchanged.
- [x] AC-03: PY013 rejects a missing idempotency flag or wrong distribution
  pattern and auto-fixes either defect to the safe canonical command.
- [x] AC-04: Focused and full tests, Ruff, governance and a bounded live Glon
  reproduction prove a retry succeeds without modifying the source checkout.
- [ ] AC-05: Protected CI and Validator Agent approve the exact final PR head
  before merge.

## Non-goals

- Do not reinterpret a generic HTTP 400 as successful publication.
- Do not weaken artifact/version filtering or immutable registry semantics.
- Do not add a dependency or change non-Twine publishers.
- Built-in config producers and Goal's governance-owned `goal.yaml` are
  intentionally split into dependent tickets to respect the repository's
  five-file, two-component and workstream ownership limits.
- Do not publish a new Goal version before this implementation is merged and
  revalidated from clean `main`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Validation evidence

- 59 focused runtime/doctor tests pass. They cover option preservation,
  no duplicate flag, non-Twine commands, wrong names, safe custom Twine
  options and isolation of Python from Node/Rust sibling strategies.
- Governance passes with 0 errors/0 warnings after splitting configuration
  producers and governance-owned config into dependent bounded tickets.
- A disposable clone of real Glon commit `ae7ea353...` auto-fixed exactly the
  Python publish line. Its two other tracked publish lines were byte-unchanged.
- Public Glon 0.1.28 wheel and sdist matched the local SHA-256 hashes
  `d845c2a23be9ea87b75ac5587ec5c231ad3f97b48c117198111c41c635f3fe43`
  and `e2af788f01f6590935c59a139627f0932a48f3429a2425f601b4f8a7916d68b3`.
  The resolved Twine retry contained one `--skip-existing`, returned 0 and
  skipped both existing immutable files. The bounded clone was removed.
- The full suite passes 615 tests with 2 existing skips; scoped Ruff,
  governance and whitespace validation also pass on the final candidate.

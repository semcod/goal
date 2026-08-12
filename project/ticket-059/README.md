# Ticket 059: Align built-in Python publish commands

- **ID**: ticket-059
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Align every built-in Goal configuration producer with the retry-safe Twine
contract delivered by ticket-058. Fresh default configurations and the legacy
`pip` / `pipenv` package-manager descriptors must include exactly one
`--skip-existing`, so newly generated projects are safe before doctor or the
runtime boundary needs to repair them.

## Acceptance criteria

- [x] AC-01: The user's instruction to repair and continue records
  `SESSION_EXECUTION_AUTHORIZATION` for this bounded regression fix.
- [x] AC-02: The default Python strategy emits the canonical retry-safe Twine
  command.
- [x] AC-03: The `pip` and `pipenv` package-manager descriptors emit
  retry-safe Twine commands without changing non-Twine managers.
- [x] AC-04: Focused/full tests, Ruff and governance pass before protected
  exact-head delivery.
- [x] AC-05: Protected CI and Validator Agent approve the exact final head;
  the unchanged tree is merged and post-merge CI passes.

## Non-goals

- Do not change runtime normalization or doctor migration from ticket-058.
- Do not edit governance-owned `goal.yaml`; that is a dependent ticket.
- Do not change versions, dependencies or public interfaces.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Validation evidence

- Three focused regressions prove the default, `pip` and `pipenv` commands
  contain the canonical flag exactly where expected.
- The full suite passes 618 tests with 2 existing skips; scoped Ruff,
  governance (0 errors/0 warnings) and whitespace checks pass.
- The touched constants module's existing late import is now explicitly marked
  `noqa: E402`; import order and runtime behavior are unchanged.
- PR #98 passed Python 3.12/3.13 and remote lifecycle on exact HEAD
  `7e3a5500317f8f580c3c7b426cb72fbf3dc9c7c0`. Validator run
  `31626544571` and review `4919749433` deterministically approved that SHA.
- PR #98 merged as `1895ddef2fad331b56ae3840b70f6f756da24da2`;
  its second parent and tree equal the approved candidate. Post-merge CI
  `31626699872` passed both supported Python versions and the remote ticket
  branch was deleted.

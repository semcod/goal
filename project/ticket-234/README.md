# ticket-234: Truthful empty test selection

- **ID**: ticket-234
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-05

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: continue the accepted Maskservice PLF-22276
request. Empty detected project types currently print all tests passed and parse
a stale JUnit report although no test ran. Keep valid standalone repository
delivery through its declared governance checks; never fabricate test success.
The existing boolean test runner API and typed-project behavior stay compatible.

## Acceptance criteria

- [x] AC-01: Empty selection and explicit opt-out are reported distinctly in
  automatic/interactive console and YAML/Markdown final summaries; stale report data is ignored.
- [x] AC-02: Real test success/failure and mandatory delivery checks retain
  behavior; zero project-type selection cannot bypass a failing declared gate.
- [ ] AC-03: Proportional/full suite and governed checks pass; immutable head
  is independently checked and published through protected OneDev and Validator.

## Boundaries

No fake health cache, dependency/version/tag/registry effects, hardware writes,
review bypass or claims to count executed cases inside every framework.

## Validation

245 focused regressions passed; full suite: 1269 passed and 2 existing skips.
Native governance passes with no errors/warnings. Differential Ruff reports no
introduced findings; legacy lint findings remain unchanged. Protected exact-head
OneDev and independent Validator publication remain pending.

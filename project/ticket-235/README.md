# ticket-235: Cold UV pytest plugin startup

- **ID**: ticket-235
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-05

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: continue maskservice:PLF-22281 in the accepted
repair/test/merge campaign. A fresh UV environment currently launches the
pytest console entry and fails to import a required project-local plugin.
Use module startup in the existing UV producers without disabling that plugin.
Keep configured arguments, warm project Python selection and mandatory gates.

## Acceptance criteria

- [x] AC-01: A genuinely cold offline UV project loads a required local plugin
  on its first test execution; warm module execution remains compatible.
- [x] AC-02: Root, configured, bash rewrite and subproject launchers use module
  startup with preserved arguments; meaningful regressions and full suite pass.
- [ ] AC-03: Governed checks pass; immutable head is independently checked and
  published through protected OneDev and Validator.

## Boundaries

No dependency/version/tag/registry changes, plugin disabling, review bypass,
retry-until-green or unrelated shell/test metric redesign.

## Validation evidence

49 focused regressions passed. Actual initially absent environment, with pytest
import failing before provisioning, passed 1274 tests with 2 existing skips
on its first module invocation offline after locked wheel-cache preparation.
Governance passed with 0 errors/warnings. The original console launcher still
fails the required root plugin import as a negative control. No new Ruff
findings relative to the same baseline/configuration. Exact protected head
validation and merge remain pending; no public package/version effect.

The argument-preservation regression also covers strict marker validation.

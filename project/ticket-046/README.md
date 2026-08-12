# Ticket 046: Run new-project source-hub health through Goal

- **ID**: ticket-046
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Repair the regression introduced when ticket-041 correctly distinguished the
maintained `wellmanifest/new-project` source hub from an adopted target but
left the source-hub path as a terminal error.  Goal must keep refusing target
package adoption into the hub, while `goal governance check` and the governed
delivery gate execute the hub's deterministic Linux contract directly from
the checked-out source tree.

The runner must validate the canonical JSON documents, require every shell
suite to be wired into the authoritative CI workflow, execute the required
check-name comparison and every `tests/*.test.sh` suite, stop on the first
failure, and remain read-only.  Target-repository behavior and the hosted
Windows trust boundary stay unchanged.

## Acceptance criteria

- [x] AC-01: `goal governance check` recognizes the canonical source hub and
  returns success only after its deterministic Linux health contract passes.
- [x] AC-02: Governed Goal delivery uses the same source-hub health runner
  instead of failing with `GOV-MANIFEST-001` or invoking the target-only
  `project/governance-check.sh` wrapper.
- [x] AC-03: Missing/malformed hub inputs, unwired suites and failed suites
  fail closed with bounded diagnostics; target package validation is
  unchanged.
- [ ] AC-04: Focused tests, full pytest, Ruff, adopted governance, package and
  Docker checks pass before exact-head external validation and trusted merge.
- [ ] AC-05: A public Goal release executes the real `new-project` candidate
  health gate before that repository's governed PR delivery.

## Evidence before PR

- 54 focused tests cover successful dispatch, malformed JSON, incomplete CI
  wiring, failed-suite short circuit, target argument isolation and leaked Git
  state; focused Ruff and governance pass.
- The real ticket-065 `new-project` candidate passed 15 canonical JSON checks,
  the required-check comparison and all 9 Linux shell suites through the Goal
  source tree.  Its exact status hash was unchanged after execution.
- A real governed pull-request dry-run reached the normal no-change outcome
  instead of `GOV-MANIFEST-001`, while retaining the candidate's clean status.
- The complete suite passes with 581 tests and 2 existing skips; wheel, sdist
  and pinned-base Docker image builds pass.  All generated build environments,
  distributions and the temporary image were removed immediately afterward.

## Participants

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

# Ticket 041: Make governed delivery diagnose new-project layouts

- **ID**: ticket-041
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Repair Goal's boundary with the `new-project` standard. Governed delivery must
distinguish an adopted target package (`.governance/*`) from the source hub
(`governance/*` and `scripts/*`) before launching a target-only wrapper. The
existing governance verification callbacks must remain read-only, and validator
failures should point to canonical remediation and managed `error/*.md`
runbooks when diagnostics v2 provides them.

## Acceptance criteria

- [ ] AC-01: Delivery rejects an incomplete adopted package before executing
  `project/governance-check.sh`, with a distinct fail-closed explanation for
  the `new-project` source hub.
- [ ] AC-02: `governance verify-delivery` and hidden hook authorization load
  existing configuration without creating or rewriting `goal.yaml`; a missing
  hook policy fails closed.
- [ ] AC-03: Goal consumes both diagnostics v1 and v2 and, for v2 failures,
  prints the canonical remediation plus a safe existing
  `.governance/error/*.md` runbook path.
- [ ] AC-04: Focused/full tests, scoped Ruff, governance, package and Docker
  builds pass.

## Boundary

- Keep the change inside the existing delivery adapter and governance CLI; do
  not add a command or dependency.
- The source hub is identified and routed explicitly, but Goal does not invent
  a substitute hub gate. Repairing the hub's own wrapper remains a source-
  standard responsibility.
- Release/version files and adoption generation remain unchanged.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

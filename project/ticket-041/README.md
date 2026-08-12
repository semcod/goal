# Ticket 041: Make governed delivery diagnose new-project layouts

- **ID**: ticket-041
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-12

## Goal and scope

Repair Goal's boundary with the `new-project` standard. Governed delivery must
distinguish an adopted target package (`.governance/*`) from the source hub
(`governance/*` and `scripts/*`) before launching a target-only wrapper. The
existing governance verification callbacks must remain read-only, and validator
failures should point to canonical remediation and managed `error/*.md`
runbooks when diagnostics v2 provides them.

## Acceptance criteria

- [x] AC-01: Delivery rejects an incomplete adopted package before executing
  `project/governance-check.sh`, with a distinct fail-closed explanation for
  the `new-project` source hub.
- [x] AC-02: `governance verify-delivery` and hidden hook authorization load
  existing configuration without creating or rewriting `goal.yaml`; a missing
  hook policy fails closed.
- [x] AC-03: Goal consumes both diagnostics v1 and v2 and, for v2 failures,
  prints the canonical remediation plus a safe existing
  `.governance/error/*.md` runbook path.
- [x] AC-04: Focused/full tests, scoped Ruff, governance, package and Docker
  builds pass.

## Boundary

- Keep the change inside the existing delivery adapter and governance CLI; do
  not add a command or dependency.
- The source hub is identified and routed explicitly, but Goal does not invent
  a substitute hub gate. Repairing the hub's own wrapper remains a source-
  standard responsibility.
- Release/version files and adoption generation remain unchanged.

## Validation evidence

- 46 focused governance/delivery tests and 570 full tests pass, with 2 existing
  skips; scoped Ruff and `git diff --check` pass.
- The deterministic governance gate passes with 0 errors and 0 warnings.
- Wheel/sdist build successfully; Docker builds the final source as image
  `sha256:64b4c1eb67a8f579b919f302811b9f1c897a341749419146c7d787f257b061f3`.
- The original high-level dry-run was repeated against the real dirty
  `new-project` hub: it failed before the target wrapper with
  `GOV-MANIFEST-001`, identified the source hub, and byte/status comparison
  proved the checkout remained unchanged.
- `goal governance check --target-root <new-project>` now routes directly to
  the hub checks declared in `.github/workflows/ci.yml` and explicitly rejects
  target-package adoption into the hub.
- When `main` advanced through the unrelated ticket-040 closure, the gate
  stopped publication with `GOV-BASE-001`; the branch was refreshed to
  `d898d3f` without changing scope or architecture and revalidated.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

# Ticket 074: Legacy clean base no-change

- **ID**: ticket-074
- **Owner**: tom
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

## Goal and scope

Bare goal -a on clean, synchronized adopted Koru currently generates a cost badge then fails its own governance gate. Verify remote default HEAD before bootstrap and return a no-change result. Preserve dirty/feature branches and explicit release requests. Publish through the protected delivery controller.

## Acceptance criteria

- [x] AC-01: Managed governance runs before no-change resolution.
- [x] AC-02: Clean synchronized legacy targets stay byte-identical and return success.
- [x] AC-03: Unpublished changes and explicit publication requests are never hidden; regression and stack checks pass.

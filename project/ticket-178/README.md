# Ticket 178: Honor disabled registry publishing

- **ID**: ticket-178
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT

## Goal and scope

An explicit publishing.enabled=false currently still invokes package build and registry publication during a clean managed release. Honor the registry configuration before any package effects, retain configured Git/tag/GitHub Release delivery, and preserve the existing tests and publication gates.

## Acceptance criteria

- [x] AC-01: Disabled registry config prevents package analysis and publisher calls for regular, forced and loaded-config forms.
- [x] AC-02: Enabled/default config, --no-publish precedence and declared GitHub fallback remain intact; governance passes.

## Risks

Intentional registry disabling is not proof that a package was published. Emit an explicit skipped-registry message; the enclosing configured GitHub delivery must still succeed independently.

## Validation

18 publish-stage and publish-change tests passed. Four new disabled-registry cases fail before the fix; enabled/default and CLI precedence remain covered. Native governance: GOV-PASS. Actual GitHub/tag delivery remains independently gated by the enclosing workflow.

109 delivery-integrity and push-workflow regression tests passed. Disabled registry completion is an explicit policy outcome, not a receipt of package publication; independent Git/GitHub delivery must still succeed.

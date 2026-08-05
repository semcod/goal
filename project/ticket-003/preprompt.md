# Ticket preprompt (ticket-003)

- **Title**: Governed Goal delivery modes
- **Created**: 2026-08-05
- **Mode**: release control; fail closed before remote side effects

## Technical directives

- Complete and validate ticket-002 governance adoption first.
- Preserve compatibility when `governance.delivery` is absent.
- Resolve policy before commit, push, tag, PR, build publication, or audit
  success is reported.
- Never treat an environment variable by itself as durable authorization.
- Never silently fall back from `pull-request` to `direct-main`.
- Never push a non-base branch directly to the configured base ref.
- Preserve existing project-owned `pre-push` commands.
- Keep audit events deterministic, append-only, and free of credentials.
- Do not create or edit a human-owned `user-*.md` file.

## References

- `project/ticket-002/README.md`
- `goal/cli/__init__.py`
- `goal/push/core.py`
- `goal/push/stages/push_remote.py`
- `goal/cli/governance_cmd.py`

# Ticket preprompt

- **Task ID**: ticket-015
- **Task title**: Add required Python 3.12 Docker entrypoint
- **Created**: 2026-08-10T08:50:31Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.

Use Python 3.12 consistently with `pyproject.toml`. Keep the image a minimal
CLI entrypoint and do not add ports, services, secrets or registry publication.
The user's execution/autonomy request is bounded session authorization; do not
ask again for the same scope and do not treat it as merge approval.

# Ticket preprompt

- **Task ID**: ticket-014
- **Task title**: Fetch legacy governance base during upgrade
- **Created**: 2026-08-10T07:21:43Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.

Characterize the depth-one upgrade failure. Parse prior provenance defensively,
fetch only a validated full SHA from the same remote, preserve exact-head
verification for the requested revision, and add a regression that fails
without the extra object.

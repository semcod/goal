# Ticket preprompt

- **Task ID**: ticket-013
- **Task title**: Adopt governance ownership extensions
- **Created**: 2026-08-10T07:20:24Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.

Use the immutable full SHA for new-project 0.14.1. Preserve target-owned
manifest extensions, verify every managed hash, and add only the ownership
needed for `integration/**` and Python lockfiles.

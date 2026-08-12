# Ticket preprompt

- **Task ID**: ticket-049
- **Task title**: Resume governed PR delivery after pre-PR interruption
- **Created**: 2026-08-12T13:20:35Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.
The request to execute this work creates SESSION_EXECUTION_AUTHORIZATION;
proceed within the recorded intent without a redundant confirmation prompt.
Require new authority for destructive action, secrets, external coordination,
material objective expansion and trusted merge approval.

Observed reproduction: a governed pull-request run creates and tests a ticket
commit, then fails to create its controlled branch because a merged local alias
exists. After that alias is safely removed, the identical retry exits at the
empty staging-area shortcut instead of delivering the existing ahead commit.

Keep resume classification read-only and fail closed. Require a clean tree,
one authoritative remote base, known ancestry and exact ticket prefixes for
the entire ahead range. Rerun configured tests before calling the existing
authorized PR delivery function. Never add a raw-push escape hatch.

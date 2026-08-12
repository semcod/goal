# Ticket preprompt

- **Task ID**: ticket-037
- **Task title**: Fetch immutable new-project release evidence during adoption
- **Created**: 2026-08-12T07:50:03Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.
The request to execute this work creates SESSION_EXECUTION_AUTHORIZATION;
proceed within the recorded intent without a redundant confirmation prompt.
Require new authority for destructive action, secrets, external coordination,
material objective expansion and trusted merge approval.

Technical boundary:

- Primary implementation: `goal/cli/governance_cmd.py`.
- Regression contract: `tests/test_governance_cmd.py`.
- Use no new dependency; publication lookup must be bounded and fail closed.
- Never contact the real GitHub API from tests.
- Preserve headless operation and exact `--check`/`--upgrade` exit forwarding.

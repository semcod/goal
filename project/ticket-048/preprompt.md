# Ticket preprompt

- **Task ID**: ticket-048
- **Task title**: Allow artifactless GitHub Releases for generic repositories
- **Created**: 2026-08-12T12:13:54Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.
The request to execute this work creates SESSION_EXECUTION_AUTHORIZATION;
proceed within the recorded intent without a redundant confirmation prompt.
Require new authority for destructive action, secrets, external coordination,
material objective expansion and trusted merge approval.

Reproduction: `wellmanifest/new-project` tag `v0.16.0` is annotated and peels
to `6800f0138bc9063eb2dacb0a8b797dedcafb7952`, but its GitHub Release is
missing because Goal 2.1.297 required package assets from a generic repository.
Relevant implementation lives in `goal/publish/github_fallback.py`,
`goal/push/core.py` and `goal/push/stages/tag.py`.

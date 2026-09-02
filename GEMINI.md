# GEMINI.md

This repository follows the `wellmanifest/new-project` policy-as-code standard.
This file is the Gemini / Antigravity entry; the same rules are in `AGENTS.md`,
`CLAUDE.md`, `.cursor/rules/new-project-standard.mdc`, `.aider.conf.yml` and
`.github/copilot-instructions.md`.

Fail-closed. Do not write code until this contract is followed.

1. Read `AGENTS.md` and `.governance/manifest.json`.
2. Allocate tickets only through `./project/new-ticket.sh`. Never copy
   `project/ticket-*`.
3. Work on a branch or worktree whose name contains `ticket-NNN`. Never commit on
   `main` or a dirty primary checkout.
4. Stay inside that ticket's `intent.json` `allowedPaths`.
5. Run `./scripts/install-agent-hosts.sh` once per clone so the git hook is active.
6. Run `./project/governance-check.sh` before claiming done.

If any step is unclear: STOP. Do not invent a ticket number.

# GitHub Copilot instructions

This repository follows the `wellmanifest/new-project` policy-as-code standard.
Same fail-closed contract as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` and the Cursor
rule. Copilot Chat and the Copilot coding agent load this file automatically.

1. Read `AGENTS.md` before proposing any change.
2. Allocate tickets only through `./project/new-ticket.sh`. Never copy a
   `project/ticket-NNN` directory and never invent a ticket number.
3. Work on a branch or worktree whose name contains `ticket-NNN`. Never write on
   `main` or a dirty primary checkout.
4. Stay inside that ticket's `intent.json` `allowedPaths`.
5. Run `./scripts/install-agent-hosts.sh` once per clone so `.githooks/pre-commit`
   is active, then `./project/governance-check.sh` before claiming done.

Suggestions that skip these steps are rejected by the pre-commit hook and by the
`governance / enforce` CI job. Markdown is not a substitute for either.

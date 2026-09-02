# CLAUDE.md

This repository follows the `wellmanifest/new-project` policy-as-code standard.
Same contract as `AGENTS.md`, `GEMINI.md`, `.cursor/rules/new-project-standard.mdc`,
`.aider.conf.yml` and `.github/copilot-instructions.md`. Claude Code must follow
it even when the session did not start in an IDE.

1. Read `AGENTS.md` and `.governance/manifest.json` first.
2. Allocate tickets only through `./project/new-ticket.sh`. Never copy a
   `project/ticket-NNN` directory and never invent a ticket number.
3. Work on a branch or worktree whose name contains `ticket-NNN`. Never write on
   `main` or a dirty primary checkout.
4. Stay inside that ticket's `intent.json` `allowedPaths`.
5. Run `./scripts/install-agent-hosts.sh` once per clone so `.githooks/pre-commit`
   is active.
6. Run `./project/governance-check.sh` before claiming done.

The pre-commit hook rejects commits that are not bound to an `IN_PROGRESS`
`ticket-NNN`, and the `governance / enforce` CI job rejects a pull request whose
host contract or packaging declaration drifted. Markdown is not a substitute for
either gate.

# AGENTS.md

This target repository follows `wellmanifest/new-project` policy-as-code.

Before any multi-step implementation, an agent must:

1. Read `.governance/manifest.json`, `TODO.md`, `project/TICKETS.md` and the
   active ticket.
2. Reuse an unfinished ticket whose workstream and scope match. A second active
   ticket is allowed only in a distinct workstream with no write-scope overlap.
   Otherwise run `./project/new-ticket.sh --title "..." --agent "..."
   --workstream "..."`.
3. Complete the ticket `README.md`, owned `ai-*.md`, `intent.json` and `TODO.md`.
4. Treat a user request that already says to execute or work autonomously as
   `SESSION_EXECUTION_AUTHORIZATION`; record it in the agent-owned ticket file.
5. Move to `EDIT` without a second confirmation and stay inside `intent.json`
   `allowedPaths`. Ask for new authority only for destructive action, secret
   access, new external coordination, or material objective expansion.
6. Never create or edit `project/ticket-*/user-*.md`; only its human owner or a
   trusted intake boundary may do so.
7. Keep executable source/tests/scripts outside ticket directories.
8. Run the managed `./project/governance-check.sh` (or
   `project\governance-check.bat` on Windows) plus the stack checks before
   reporting completion. Root `project.sh` / `project.bat` are optional
   target-owned seed aliases and must not be assumed to contain the gate.
9. Serialize ticket-ID allocation before branching, then use a separate
   branch/worktree per implementation ticket. Each diff must resolve to exactly
   one active ticket. Shared contract paths are edited only by the declared
   integration workstream; `integrationTicket` coordinates work but does not
   transfer path ownership.
10. Only `IN_PROGRESS` reserves a workstream and write scope. `BACKLOG`, `PLAN`
   and `BLOCKED` retain evidence without blocking another implementation;
   transition back to `IN_PROGRESS` before changing source or tests.
11. Treat GitHub review as trusted only when it targets the current HEAD and
   either a `User` login is in protected `trusted-reviewers` or a `Bot` login
   is in the separate protected `trusted-validator-apps` input. Never trust an
   arbitrary Bot review.
12. Require merge approval evidence to bind repository, PR, current HEAD,
   active ticket and actor. The protected resolver creates that evidence
   outside the PR checkout; repository-authored evidence is untrusted.
13. A signed attestation is trusted only after a protected verifier validates
   its signature, issuer, predicate type and subject bindings.
14. Validator-agent examples use
   `LLM_MODEL_VALIDATOR=openrouter/z-ai/glm-5.2`; model findings stay advisory.
15. Configure GitHub with `delete_branch_on_merge=true`. A merged ticket branch
   must disappear after merge. A PR closed without merge keeps its branch until
   the owner explicitly discards that unmerged work. When no PR is open, the
   only remote branch is the default branch.
16. At merge, publication or explicit pilot discard, inventory temporary linked
   worktrees and duplicate clones. Verify dirty state and HEAD reachability
   before removal; preserve unknown or unique data. Remove an exact linked
   worktree through Git, prune its metadata and only then delete its released
   disposable branch. Prefer recoverable trash for a verified duplicate clone.
   Run the adopted workspace lifecycle checker through Goal for the terminal
   audit. CI validates GitHub state separately and cannot inspect a developer
   filesystem.
17. Allocate every ticket ID only through `./project/new-ticket.sh` after
   fetching/pruning. Never create or copy `project/ticket-{NNN}` manually; the
   clone-wide lock and high-water reservation must exist before commit.
18. Keep an implementation ticket `IN_PROGRESS / PUBLICATION` through
   exact-head review and trusted merge. Set `DONE / DONE` only in a
   governance-only closure based on the integrated default branch.
19. Resolve `GOV-*` findings through `.governance/diagnostics.json` and its
   linked `.governance/error/*.md` runbook when present. Ticket logs are
   historical evidence and never authorize bypassing a fail-closed gate.
20. Keep each incident-specific `remediation-intent.dsl.json` in its target
   ticket. Validate it before LLM planning and treat todo2code/LLM results as
   digest-bound advisory input; never let either expand the accepted intent.

Markdown approval is an audit note, not trusted merge approval. Required
merge approval comes from the repository's protected review, attestation and
ruleset boundary.

# AGENTS.md

This target repository follows `wellmanifest/new-project` policy-as-code.

HOME vs ADOPT: wellmanifest owns standards; product CLI/daemons HOME in
`subactor` or `semcod`. "w ramach wellmanifest" means ADOPT packs such as
`wellmanifest/{new-project,dsl,logs}`, not HOME wellmanifest. For
SERVICE/FEATURE that create a repo, fill `intent.json` `placement`
(`home`, `shape`, `runtimeOwner`, `adopt`) in WAIT_FOR_APPROVAL.
`shape=runtime_service` must not use `home=wellmanifest`.

Before any multi-step implementation, an agent must:

1. Read `.governance/manifest.json`, `TODO.md`, `project/TICKETS.md` and the
   active ticket.
   Respect `repository.mode`: `standalone` owns a separate repository, while
   `monorepo` confines work to declared `repository.componentRoots`. Require a
   running Docker engine and Docker runtime files only when
   `docker.required=true`; existing Docker configuration remains subject to
   stack validation even when Docker is optional.
2. Reuse an unfinished ticket whose workstream and scope match. A second active
   ticket is allowed when its write scope is disjoint and the manifest's
   per-workstream concurrency limit permits it.
   Otherwise run `./project/new-ticket.sh --title "..." --agent "..."
   --workstream "..."`.
3. Complete the minimal ticket `README.md` and `intent.json`. Routine disjoint
   source/test work uses that compact intent; add the full `delivery` contract
   for dependency manifests, integration-owned paths or repositories whose
   manifest requires it. Participant prose,
   changelog, raw logs, TODO and indexes are optional and never delivery output.
4. Treat a user request that already says to execute or work autonomously as
   `SESSION_EXECUTION_AUTHORIZATION`; record it in the agent-owned ticket file.
   When that same request explicitly creates a new repository, `HEAD` is
   unborn and no implementation exists, it also authorizes exactly one local
   governance seed-baseline commit. Resolve an immutable seed profile, stage
   only its exact allowlist, scan for secrets, create no remote effect, then
   record the real resulting `HEAD` as `delivery.acceptedBaseSha`. This narrow
   exception never authorizes remote creation, push, pull request, merge, tag
   or release; ordinary implementation starts only after the baseline.
5. Move to `EDIT` without a second confirmation and stay inside `intent.json`
   `allowedPaths`. Ask for new authority only for destructive action, secret
   access, new external coordination, or material objective expansion.
   When the recorded outcome includes publication, this authorization also
   permits invoking the repository's declared protected delivery process and
   that process's merge after exact-head trusted approval. Do not ask for a
   second chat confirmation. Session prose is never approval evidence and the
   agent must not merge directly.
6. Never create or edit `project/ticket-*/user-*.md`; only its human owner or a
   trusted intake boundary may do so.
7. Keep executable source/tests/scripts outside ticket directories.
8. Run the managed `./project/governance-check.sh` (or
   `project\governance-check.bat` on Windows) plus the stack checks before
   reporting completion. Root `project.sh` / `project.bat` are optional
   target-owned seed aliases and must not be assumed to contain the gate.
9. Serialize ticket-ID allocation before branching, then use a separate
   branch/worktree per implementation ticket. Resolve its location with the
   managed `wellmanifest/worktrees` checker. The canonical linked worktree is
   `<workspace>/.worktrees/<repo>--ticket-NNN--<slug>` with its lease under
   `<workspace>/.worktrees/.leases`; never create publishable ticket work in a
   repo-local `.worktrees`, parallel `<organization>-worktrees`, nested
   `.worktrees/.worktrees`, system temporary directory or duplicate clone.
   Each diff must resolve to exactly one active ticket. Shared contract paths are edited only by the declared
   integration workstream; `integrationTicket` coordinates work but does not
   transfer path ownership. Product commercial registries (prices,
   entitlements, public plan ids) and brand facades (tokens, vocabulary,
   public plan names) belong in `integration.requiredForPaths`. For Subactor,
   bump `subactor/offer` and/or `subactor/brand` before any portal facade
   rewrite; `wellmanifest/policy-dsl` owns promo rules only. Empty
   `conflictsWith` does not authorize a parallel offer or brand rewrite.
10. Only `IN_PROGRESS` reserves a workstream and write scope. `BACKLOG`, `PLAN`
   and `BLOCKED` retain evidence without blocking another implementation;
   transition back to `IN_PROGRESS` before changing source or tests.
11. Treat GitHub review as trusted only when it targets the current HEAD and
   either a `User` login is in protected `trusted-reviewers` or a `Bot` login
   is in the separate protected `trusted-validator-apps` input. Never trust an
   arbitrary Bot review.
11a. **INVOKE VALIDATOR-AGENT — do not ask the human.** When publication needs
   trusted merge approval (protected default branch, merge blocked on reviews,
   or the user asks to publish/merge), the coding agent MUST dispatch
   `subactor/validator-agent` itself:

   ```bash
   # from a checkout of subactor/validator-agent @ main
   ./bin/dispatch-direct-pr.sh \
     --owner <org> --name <repo> --pr <N> --ticket ticket-NNN \
     --wait-checks --merge --watch
   ```

   Freeze: re-read `gh pr view <N> --json headRefOid` immediately before
   dispatch; do not push after freeze until approve or fail. MUST NOT ask the
   human to “use the validator”, MUST NOT self-approve, and MUST NOT treat
   chat/Markdown as merge approval. Normative:
   `subactor/validator-agent/docs/PUBLICATION_FREEZE.md`.
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
   worktrees, duplicate clones and non-default local branches. Verify dirty state and HEAD reachability
   before removal; preserve unknown or unique data. Remove an exact linked
   worktree through Git, prune its metadata and only then delete its released
   disposable branch. Prefer recoverable trash for a verified duplicate clone.
   The checker is read-only; during active work exempt a branch only through
   the exact allowlisted checkout path, never a pattern or branch name. Run the
   adopted workspace lifecycle checker through Goal for the terminal audit. CI
   validates GitHub state separately and cannot inspect a developer filesystem.
17. Allocate every ticket ID only through `./project/new-ticket.sh` after
   fetching/pruning. Never create or copy `project/ticket-{NNN}` manually; the
   clone-wide lock and high-water reservation must exist before commit.
18. Keep an implementation ticket `IN_PROGRESS / PUBLICATION` through
   exact-head review and trusted merge. The protected delivery controller closes
   it through an external receipt; never create a repository closure commit,
   branch or PR.
19. Resolve `GOV-*` findings through `.governance/diagnostics.json` and its
   linked `.governance/error/*.md` runbook when present. Ticket logs are
   historical evidence and never authorize bypassing a fail-closed gate.
20. Keep each incident-specific `remediation-intent.dsl.json` in its target
   ticket. Validate it, atomically render its declared task/TODO paths and run
   `verify-todo2code` before extraction. Analyze todo2code with the exact graph,
   diagnostics and plans so only records citing those projections can affect
   the digest-bound advisory overlay; never let todo2code or an LLM expand the
   accepted intent.
21. When `.governance/manifest.json` selects `domainContracts.mode=cqrs`, keep
   command and query definitions only in `operations/index.json`. Publish the
   mandatory `events/index.json` and `error/index.json` catalogs with stable
   `events/{event-id}.md` and `error/{code}.md` documents. Protobuf and JSON
   Schema models describe transport shape only; they never grant authority or
   redefine C/Q semantics. Run the managed gate after every graph change.
22. Host-agnostic standard: follow `GEMINI.md`, `CLAUDE.md`, and
   `.cursor/rules/new-project-standard.mdc` in addition to this file. Run
   `./scripts/install-agent-hosts.sh` once per clone so `.githooks/pre-commit`
   rejects commits that are not bound to an `IN_PROGRESS` `ticket-NNN`. Do
   not write on `main` or a dirty primary checkout. Markdown is not a
   substitute for the hook.
23. Require material delivery: ticket directories, TODO, ticket indexes and a
   generated artifact registry are tracking carriers, not an outcome. Reject a
   carrier-only commit or PR. If analysis finds no material delta, emit an
   external no-change receipt and create no repository history. Intent may be
   committed atomically with the first material change; do not create a
   separate plan-only commit.

Markdown approval is an audit note, not trusted merge approval. Required
merge approval comes from the repository's protected review, attestation and
ruleset boundary.

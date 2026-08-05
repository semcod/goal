# Ticket preprompt (ticket-002)

- **Title**: Pinned governance bootstrap for Goal
- **Created**: 2026-08-04
- **Mode**: governance planning; fail closed on unpublished source

## Technical directives

- Use only a reviewed, published full commit SHA.
- Run adoption `--check` before any managed write.
- Do not use a moving branch, local dirty content or an invented lock hash.
- Review conflicts before any explicit upgrade operation.
- Preserve the previous root `project.sh` analysis pipeline in
  `project/analysis.sh` before installing the standard gate entry point.
- Preserve project-owned `README.md`, `project/README.md`, source and tests.
- Customize target workstreams without widening a ticket's approved paths.
- Do not create or edit a human-owned `user-*.md` file.
- Do not invoke OpenRouter or any LLM; specifically never select Gemini 3.1
  Pro Preview. The approved future fallback is `z-ai/glm-5.2`.

## References

- `docs/GOAL_KORU_SUBACTOR_REFACTORING_PLAN.md`
- `project/ticket-001/README.md`
- `repo://wellmanifest/new-project/scripts/create_adoption_lock.py`
- `repo://wellmanifest/new-project/governance/manifest.default.json`
- Published revision: `c0bb63e7fc889934140c96b1625f3ab232122baf`

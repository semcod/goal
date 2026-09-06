# Documentation instructions

<!-- wellmanifest:docs-placement:start -->
## Documentation placement

Before research or writing, identify the owning repository, document kind and canonical path using [wellmanifest/docs 0.1.0](https://github.com/wellmanifest/docs/blob/fdb0fcaa7c606dc2503cabb71eff64d5f86ee659/docs/standard/POLICY.md). Resolve existing documents through the artifact registry when available; update the canonical document instead of creating duplicates.

- Durable information: `docs/information/<id>.md`.
- Analysis and final reports: `docs/analysis/<id>.md`.
- Refactoring plans: `docs/refactoring/<id>.md`.
- Architecture decisions: `docs/decisions/<id>.md`.
- Index every delivered document in `docs/README.md`.
- Cross-repository results have one owner, `subactor/docs`, under `architecture/{information,analysis,refactoring,decisions}/`, indexed in its root `README.md`. Other repositories link to that source.

Use the standard's JSON metadata and section templates. Keep stable IDs, increment the declared version when findings change, update dates, bind exact source revisions and evidence, and separate facts, hypotheses and recommendations. Preserve historical append-only versioning.

A final report or plan must not exist only in `$HOME/.local/state`, `/tmp`, agent session storage, chat or `project/ticket-*`. Tickets contain bounded intent and a link to the canonical result. Raw logs, transcripts, secrets, working databases, backups and Git bundles remain in private ignored recovery storage; publish only safe receipt references and digests when needed.

Before completion, verify placement, metadata, index links and Git tracking. The final response links to the repository document and states whether it is local, committed, in a PR or merged. Documentation status and session prose never grant execution or merge approval.

This instruction reference is not evidence that the documentation checker is wired into protected CI. Adoption and enforcement must be verified separately.
<!-- wellmanifest:docs-placement:end -->

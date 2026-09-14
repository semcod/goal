---
{
  "schema": "wellmanifest.docs/document/v2",
  "id": "markdown-output",
  "kind": "feature",
  "version": 1,
  "title": "Markdown CLI output",
  "status": "implemented",
  "owner": "semcod/goal",
  "scope": "repository",
  "updated": "2026-09-14",
  "source_revision": "ad8f1253d0168e0b7d4fa069ecab2a3017edb660",
  "priority": "P2",
  "evidence": [
    "https://github.com/semcod/goal/commit/ad8f1253d0168e0b7d4fa069ecab2a3017edb660"
  ]
}
---

# Markdown CLI output

<!-- docs:section summary -->
## Purpose and status

Read Goal CLI output as a human-readable report, not a stable machine protocol. This guide replaces the duplicated Markdown overview; command defaults differ.

<!-- docs:section details -->
## Scope and behavior

`goal status --markdown` prints Markdown; `goal status --ascii` selects ASCII when global Markdown is not enabled. Status defaults to Markdown.

The global `--markdown` / `--ascii` choice is propagated through the CLI context. Without an explicit choice, the global Markdown flag follows `--all`. Push inherits this context when its own output option is unspecified; commit enables Markdown through its local flag or global context. Do not assume one default for every command.

`MarkdownFormatter` composes sections and optionally metadata. Frontmatter is emitted only when metadata exists: the status report has no frontmatter, while the push report adds metadata. Scalar metadata is not generally YAML-escaped, so arbitrary output is not a guaranteed YAML interchange format.

The status report includes current state, staged files, at most the first 20 unstaged files and suggested actions. It is not a complete repository inventory.

For automation, see [integration and exit codes](../SERVICE/MARKDOWN_OUTPUT_INTEGRATION.md).

<!-- docs:section validation -->
## Validation

Use read-only checks:

```bash
python -m goal status --markdown
python -m goal status --ascii
python -m goal push --help
```

Behavior is defined in `goal/cli/__init__.py`, `goal/cli/utils_cmd.py`, `goal/cli/push_cmd.py`, `goal/cli/commit_cmd.py` and `goal/formatter.py`. Run `python -m pytest tests/test_cli_options.py tests/test_formatter.py` for regression coverage.

<!-- docs:section risks -->
## Risks and ownership

Examples do not authorize commit, push or release. A formatted success message is not trusted approval evidence. Global Markdown can override the status command's local ASCII choice. Recheck option precedence when changing the CLI.

---
{
  "schema": "wellmanifest.docs/document/v2",
  "id": "markdown-output-integration",
  "kind": "service",
  "version": 1,
  "title": "Integrating Markdown reports",
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

# Integrating Markdown reports

<!-- docs:section summary -->
## Purpose and status

Capture a Goal report without losing its exit status or treating presentation text as a stable API. Use this procedure for logs and CI artifacts.

<!-- docs:section details -->
## Scope and behavior

Capture stdout, stderr and the return code separately:

```python
import subprocess

result = subprocess.run(
    ["goal", "status", "--markdown"],
    capture_output=True, text=True, check=False,
)
if result.returncode:
    raise RuntimeError(result.stderr or result.stdout)
report = result.stdout
```

Store `report` as a Markdown artifact only after deciding how to handle failure. Keep stderr as diagnostic evidence. In a shell pipeline, enable `set -o pipefail` before piping output to `tee`; otherwise the pipeline can hide Goal's failure.

Do not parse the report using fixed line numbers, assume frontmatter is present, or send it directly to a JUnit consumer. Metadata emission is conditional and arbitrary scalar values are not guaranteed valid YAML. Automated decisions need an explicitly documented structured interface, not inferred headings.

See [output defaults and limitations](../FEATURE/MARKDOWN_OUTPUT.md) before choosing command flags. A status report is a read-only example; push and release are separate authorized operations.

<!-- docs:section validation -->
## Validation

Run `python -m pytest tests/test_cli_options.py tests/test_formatter.py`. Inspect a successful and a failed subprocess result in the consuming integration. Confirm that a nonzero return code remains a failure even when an artifact was written.

Source of rendering behavior: `goal/formatter.py`. CLI option resolution: `goal/cli/__init__.py` and command modules.

<!-- docs:section risks -->
## Risks and ownership

Reports can contain filenames and repository information: apply the destination's access controls and retention policy. Do not publish captured output blindly. This guide defines integration practice, not a new output schema or permission to bypass checks.

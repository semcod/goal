# Markdown Output for Goal

Goal supports structured markdown output perfect for LLM consumption, CI/CD logs, and documentation.

## Usage

Add the `--markdown` flag to any Goal command to get structured output:

```bash
goal push --markdown
goal status --markdown
goal --markdown --all
```

## Example Output

### Failed Test Scenario

```markdown
---
command: goal push
project_types: ["python"]
version_bump: "1.0.1 -> 1.0.2"
file_count: 7
timestamp: "2026-01-29T10:03:15.123456"
---

# Goal Push Result

## Overview
**Project Type:** python
**Files Changed:** 7 (+1140/-99 lines)
**Version:** 1.0.1 → 1.0.2
**Commit Message:** `feat(examples): update 7 files (+1140/-99)`

## Changed Files
- goal/cli.py (+150/-10)
- examples/README.md (+100/-5)
- examples/python-package/pyproject.toml (+50/-0)
- examples/nodejs-app/package.json (+45/-0)
- examples/rust-crate/Cargo.toml (+40/-0)
- examples/makefile/Makefile (+200/-0)
- examples/github-actions/.github/workflows/release.yml (+555/-84)

### Command: `pytest`
**Status:** ❌ Failed (exit code: 1)

**Output:**
```
========================================================================================== test session starts ==========================================================================================
platform linux -- Python 3.13.7, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/tom/github/wronai/goal
configfile: pyproject.toml
collected 0 items                                                                                                                                                                                       

========================================================================================= no tests ran in 0.01s =========================================================================================
```

## Error
```
Tests failed - aborted by user
```

## Summary

**Actions Taken:**
- ✅ Detected project types
- ✅ Staged changes
- ✅ Attempted to run tests

**Next Steps:**
- ➡️ Fix failing tests
- ➡️ Run tests manually: pytest
- ➡️ Retry with: goal push
- ➡️ Or skip tests: goal push --yes -m 'chore: skip tests'

---
*Generated at 2026-01-29T10:03:15.123456*
```

### Successful Release Scenario

```markdown
---
command: goal push
project_types: ["python"]
version_bump: "1.0.1 -> 1.0.2"
file_count: 5
timestamp: "2026-01-29T10:05:30.654321"
---

# Goal Push Result

## Overview
**Project Type:** python
**Files Changed:** 5 (+100/-20 lines)
**Version:** 1.0.1 → 1.0.2
**Commit Message:** `fix: resolve critical bug in parser`

## Changed Files
- src/parser.py (+80/-15)
- tests/test_parser.py (+20/-5)
- CHANGELOG.md (+0/-0)

### Command: `pytest`
**Status:** ✅ Success (exit code: 0)

**Output:**
```
========================================================================================== test session starts ==========================================================================================
platform linux -- Python 3.13.7, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/tom/github/wronai/goal
collected 25 items

tests/test_parser.py .........................
25 passed in 0.52s

========================================================================================= 25 passed in 0.52s =========================================================================================
```

## Actions Performed
1. ✅ Detected project types
2. ✅ Staged changes
3. ✅ Ran tests
4. ✅ Committed changes
5. ✅ Updated version to 1.0.2
6. ✅ Updated changelog
7. ✅ Created tag v1.0.2
8. ✅ Pushed to remote
9. ✅ Published version 1.0.2

## Summary

**Actions Taken:**
- ✅ Detected project types
- ✅ Staged changes
- ✅ Ran tests
- ✅ Committed changes
- ✅ Updated version to 1.0.2
- ✅ Updated changelog
- ✅ Created tag v1.0.2
- ✅ Pushed to remote
- ✅ Published version 1.0.2

**Next Steps:**
- ➡️ Changes committed successfully
- ➡️ Version updated to 1.0.2
- ➡️ Run `goal push --yes` to retry without prompts
- ➡️ Run `goal --all` for full automation including publish

---
*Generated at 2026-01-29T10:05:30.654321*
```

## Integration with LLMs

The markdown output is designed to be easily consumed by LLMs:

### Python Example

```python
import subprocess
import json

# Run goal with markdown output
result = subprocess.run(
    ["goal", "push", "--markdown"],
    capture_output=True,
    text=True
)

# Parse front matter
lines = result.stdout.split('\n')
front_matter = {}
if lines[0] == '---':
    i = 1
    while lines[i] != '---':
        key, value = lines[i].split(': ', 1)
        try:
            front_matter[key] = json.loads(value)
        except:
            front_matter[key] = value
        i += 1

# Extract key information
project_type = front_matter.get('project_types', ['unknown'])[0]
version_bump = front_matter.get('version_bump')
file_count = front_matter.get('file_count', 0)

print(f"Project: {project_type}")
print(f"Version: {version_bump}")
print(f"Files changed: {file_count}")
```

### Shell Script Example

```bash
#!/bin/bash
# Extract version from markdown output
VERSION=$(goal push --dry-run --markdown | grep "version_bump" | cut -d'"' -f2)
echo "Next version will be: $VERSION"

# Check if tests will run
if goal push --dry-run --markdown | grep -q "pytest"; then
    echo "Tests will be run"
fi
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Release with structured output
  run: |
    goal push --markdown > release-output.md
    
    # Upload as artifact
    name: upload-release-output
    uses: actions/upload-artifact@v3
    with:
      name: release-output
      path: release-output.md
```

### GitLab CI

```yaml
release:
  script:
    - goal push --markdown | tee release-output.md
  artifacts:
    reports:
      junit: release-output.md
```

## Benefits

1. **Structured Data**: Easy to parse programmatically
2. **Human Readable**: Clear formatting for logs
3. **LLM Friendly**: Optimized for AI consumption
4. **Complete Context**: All relevant information included
5. **Timestamped**: Exact timing of operations
6. **Metadata**: Front matter with key metrics

## Tips

- Use `--markdown` in CI/CD for structured logs
- Pipe output to files for audit trails
- Combine with `--dry-run` for planning
- Use with `--all` for complete automation logs
- The output includes timestamps for precise tracking

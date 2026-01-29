# Markdown Output

Goal outputs structured markdown by default, perfect for:
- CI/CD logs
- LLM consumption
- Automated documentation
- Release notes

## Enabling Markdown Output

Markdown is the default output format. You can explicitly specify it:

```bash
goal --markdown push
goal push --markdown
goal status --markdown
```

To use legacy ASCII output:

```bash
goal --ascii push
```

## Output Structure

### Front Matter

Every markdown output includes YAML front matter:

```yaml
---
command: goal push
project_types: ["python"]
version_bump: "1.0.1 -> 1.0.2"
file_count: 7
timestamp: "2026-01-29T10:30:00Z"
---
```

### Sections

#### Overview
Summary of the operation:

```markdown
## Overview

**Project Type:** python
**Files Changed:** 7 (+1140/-99 lines)
**Version:** 1.0.1 → 1.0.2
**Commit Message:** feat(goal): add YAML configuration support
```

#### Files
List of changed files with statistics:

```markdown
## Files Changed

| File | Added | Deleted |
|------|-------|--------|
| goal/config.py | 450 | 0 |
| goal/cli.py | 120 | 15 |
| README.md | 50 | 10 |
| pyproject.toml | 2 | 0 |
| VERSION | 1 | 1 |
| CHANGELOG.md | 25 | 0 |
| goal/__init__.py | 1 | 1 |
```

#### Test Results
Test execution details:

```markdown
## Test Results

**Status:** ✓ Passed
**Command:** pytest tests/ -v
**Duration:** 2.3s
**Exit Code:** 0

```
pytest tests/ -v
============================= test session starts ==============================
collected 15 items

tests/test_config.py .......                                            [ 46%]
tests/test_cli.py ........                                                [100%]

============================== 15 passed in 2.31s ==============================
```
```

#### Actions
List of actions performed:

```markdown
## Actions Performed

1. ✓ Detected project types: python
2. ✓ Staged all changes
3. ✓ Generated smart commit message
4. ✓ Updated version in 3 files
5. ✓ Updated CHANGELOG.md
6. ✓ Created git tag v1.0.2
7. ✓ Pushed to origin/main
8. ✓ Published to PyPI
```

#### Summary
Final summary and next steps:

```markdown
## Summary

✅ Successfully released version 1.0.2

### Next Steps
- Monitor deployment status
- Update documentation if needed
- Announce release to users
```

## Complete Example

```bash
goal push --bump minor --yes
```

Output:

```markdown
---
command: goal push
project_types: ["python"]
version_bump: "1.0.1 -> 1.0.2"
file_count: 7
timestamp: "2026-01-29T10:30:00Z"
---

# Goal Push Result

## Overview

**Project Type:** python
**Files Changed:** 7 (+1140/-99 lines)
**Version:** 1.0.1 → 1.0.2
**Commit Message:** feat(goal): add YAML configuration support

## Files Changed

| File | Added | Deleted |
|------|-------|--------|
| goal/config.py | 450 | 0 |
| goal/cli.py | 120 | 15 |
| README.md | 50 | 10 |
| pyproject.toml | 2 | 0 |
| VERSION | 1 | 1 |
| CHANGELOG.md | 25 | 0 |
| goal/__init__.py | 1 | 1 |

## Test Results

**Status:** ✓ Passed
**Command:** pytest tests/ -v
**Duration:** 2.3s
**Exit Code:** 0

```
pytest tests/ -v
============================= test session starts ==============================
collected 15 items

tests/test_config.py .......                                            [ 46%]
tests/test_cli.py ........                                                [100%]

============================== 15 passed in 2.31s ==============================
```

## Actions Performed

1. ✓ Detected project types: python
2. ✓ Staged all changes
3. ✓ Generated smart commit message
4. ✓ Updated version in 3 files
5. ✓ Updated CHANGELOG.md
6. ✓ Created git tag v1.0.2
7. ✓ Pushed to origin/main
8. ✓ Published to PyPI

## Summary

✅ Successfully released version 1.0.2

### Next Steps
- Monitor deployment status
- Update documentation if needed
- Announce release to users
```

## Using in CI/CD

### GitHub Actions

```yaml
- name: Release with Goal
  run: |
    goal --all --bump patch > release.md
    
- name: Upload Release Notes
  uses: actions/upload-artifact@v3
  with:
    name: release-notes
    path: release.md
```

### GitLab CI

```yaml
release:
  script:
    - goal --all --bump minor | tee release-notes.md
  artifacts:
    paths:
      - release-notes.md
```

### Parsing with Tools

#### Python

```python
import yaml
from pathlib import Path

# Parse front matter
content = Path("release.md").read_text()
front_matter = yaml.safe_load(content.split('---')[1])

print(f"Version bump: {front_matter['version_bump']}")
print(f"Files changed: {front_matter['file_count']}")
```

#### jq (JSON)

```bash
# Convert to JSON and parse
goal --all --bump patch | \
  yq eval '.front_matter' -o json | \
  jq '.version_bump'
```

## Customizing Output

### Disabling Markdown

```bash
# For scripts that need plain output
goal --ascii push
```

### Redirecting to File

```bash
# Save release notes
goal --all --bump patch > release-$(date +%Y%m%d).md

# Append to log
goal push >> release.log 2>&1
```

### Filtering Sections

```bash
# Get only the summary
goal push | grep -A 10 "## Summary"

# Get version bump info
goal push | grep "Version:" | cut -d: -f2
```

## Integration Examples

### Slack Notification

```bash
#!/bin/bash
# notify-slack.sh

WEBHOOK_URL="$SLACK_WEBHOOK_URL"
RELEASE_MD=$(goal --all --bump patch)

VERSION=$(echo "$RELEASE_MD" | grep "Version:" | cut -d: -f2 | tr -d ' ')

curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"🚀 Released version $VERSION\n\n\`\`\`$RELEASE_MD\`\`\`\"}" \
  "$WEBHOOK_URL"
```

### Email Report

```bash
#!/bin/bash
# email-report.sh

goal --all --bump minor | \
  mail -s "Release $(date +%Y-%m-%d)" \
       -a "Content-Type: text/markdown" \
       team@example.com
```

### Jira Integration

```bash
#!/bin/bash
# update-jira.sh

RELEASE_MD=$(goal --all --bump patch)
VERSION=$(echo "$RELEASE_MD" | grep "Version:" | cut -d: -f2 | tr -d ' ')
SUMMARY=$(echo "$RELEASE_MD" | grep "Commit Message:" | cut -d: -f2-)

# Create Jira release
jira create-release --project "PROJ" --name "$VERSION" --description "$SUMMARY"
```

## Tips

1. **Save outputs** for audit trails
2. **Parse front matter** for automation
3. **Use in templates** for consistent formatting
4. **Combine with artifacts** in CI/CD
5. **Filter with grep** for specific information

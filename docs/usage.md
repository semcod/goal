# Basic Usage

Goal provides an interactive workflow for git operations with smart commit messages.

## Main Commands

### `goal` or `goal push`

The primary command for committing and pushing changes.

```bash
# Interactive mode (default)
goal

# Explicit push command
goal push

# Automatic mode (no prompts)
goal --yes

# Full automation (tests, commit, push, publish)
goal --all

# Specify version bump type
goal --bump minor

# Preview changes
goal push --dry-run
```

### Interactive Workflow

When you run `goal push`, it will guide you through:

```bash
$ goal push

=== GOAL Workflow ===
Will commit 3 files (+42/-5 lines)
Version bump: 1.0.0 → 1.0.1
Commit message: feat: add user authentication

Run tests? [Y/n] 
# Press Enter to run tests, or 'n' to skip

✓ Tests passed

Commit changes? [Y/n]
# Press Enter to commit, or 'n' to cancel

✓ Committed: feat: add user authentication
✓ Updated VERSION to 1.0.1
✓ Updated CHANGELOG.md
✓ Created tag: v1.0.1

Push to remote? [Y/n]
# Press Enter to push, or 'n' to skip

✓ Successfully pushed to main

Publish version 1.0.1? [Y/n]
# Press Enter to publish, or 'n' to skip

✓ Published version 1.0.1
```

## Common Options

### Version Bumping

```bash
# Patch version (default) - 1.0.0 → 1.0.1
goal push

# Minor version - 1.0.0 → 1.0.1
goal push --bump minor

# Major version - 1.0.0 → 2.0.0
goal push --bump major
```

### Skip Steps

```bash
# Don't create git tag
goal push --no-tag

# Don't update changelog
goal push --no-changelog

# Don't sync version to other files
goal push --no-version-sync
```

### Custom Messages

```bash
# Custom commit message
goal push -m "feat: add OAuth2 authentication"

# Custom message with body
goal push -m "feat: add authentication" -m "Implements OAuth2 flow with refresh tokens"
```

### Split Commits

Split changes by type into separate commits:

```bash
goal push --split

# Result:
# ✓ Committed (code): feat: add API endpoints
# ✓ Committed (docs): docs: update API documentation
# ✓ Committed (release): chore(release): bump version to 1.1.0
```

### Ticket Prefixes

Create a `TICKET` file:

```ini
prefix=ABC-123
format=[{ticket}] {title}
```

Or override per command:

```bash
goal push --ticket JIRA-456
```

Result: `[ABC-123] feat: add user profile`

## Status and Information

### Check Repository Status

```bash
goal status

# Output:
# Version: 1.0.1
# Branch: main
# Staged files (2):
#   + src/app.py
#   + tests/test_app.py
# Unstaged/untracked (1):
#   ? README.md
```

### Show Version Information

```bash
goal version

# Output:
# Current: 1.0.1
# Next (patch): 1.0.2
# Next (minor): 1.0.2
# Next (major): 2.0.0

goal version --bump minor
# Current: 1.0.1
# Next (minor): 1.1.0
```

### Generate Commit Messages

```bash
# Simple message
goal commit
# feat: add user authentication

# Detailed message with body
goal commit --detailed
# feat: add user authentication
#
# Statistics: 3 files changed, 42 insertions, 5 deletions
# Summary:
# - Dirs: src=2, tests=1
# - Exts: .py=3
# - A/M/D: 2/1/0
# ...
```

## Project Initialization

### Initialize Goal

```bash
goal init

# Output:
# ✓ Created VERSION file (1.0.0) - detected from project
# ✓ Created CHANGELOG.md
# ✓ Created goal.yaml with auto-detected settings
#   Project: my-app (python)
#   Types: python
# Detected project types: python
# ✓ Goal initialized!
```

### Force Reinitialize

```bash
goal init --force
# Overwrites existing goal.yaml
```

## Output Formats

### Markdown Output (Default)

Goal outputs structured markdown perfect for logs and LLMs:

```bash
goal push --markdown
```

### ASCII Output

For simpler terminal output:

```bash
goal push --ascii
```

## Dry Run

Preview what Goal would do without making changes:

```bash
goal push --dry-run

# Output:
# === DRY RUN ===
# Project types: python
# Files to commit: 3 (+42/-5 lines)
#   - src/app.py (+40/-3)
#   - tests/test_app.py (+2/-2)
#   - README.md (+0/0)
# Commit message: feat: add user authentication
# Version: 1.0.0 → 1.0.1
# Version sync: VERSION, pyproject.toml
# Tag: v1.0.1
```

## Working with Different Configs

```bash
# Use custom config file
goal --config staging.yaml push

# Short form
goal -c .goal/production.yaml --all
```

## Tips

1. **First time**: Run `goal init` to set up your project
2. **Daily use**: Just run `goal` for interactive workflow
3. **CI/CD**: Use `goal --all` for full automation
4. **Preview**: Use `--dry-run` to check before committing
5. **Customize**: Edit `goal.yaml` to fit your workflow

# Basic Usage

Goal provides an interactive workflow for git operations with smart commit messages.

### `goal` or `goal push`

The primary command for committing and pushing changes.

```bash
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

# Minor version - 1.0.0 → 1.0.1
goal push --bump minor

# Major version - 1.0.0 → 2.0.0
goal push --bump major
```

# Don't update changelog
goal push --no-changelog

# Don't sync version to other files
goal push --no-version-sync
```

# Custom commit message
goal push -m "feat: add OAuth2 authentication"

# Custom message with body
goal push -m "feat: add authentication" -m "Implements OAuth2 flow with refresh tokens"
```

### Split Commits

Split changes by type into separate commits:

```bash
goal push --split

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

### Show Version Information

```bash
goal version

# Next (major): 2.0.0

goal version --bump minor
# Detailed message with body
goal commit --detailed
### Force Reinitialize

```bash
goal init --force
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

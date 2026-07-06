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

### Dependency Updates

Upgrade dependencies as part of the push workflow:

```bash
# Single project
goal -u

# Full automation + dependency upgrades
goal -au

# Monorepo: auto-discovers subprojects when root has no manifest
goal -au

# Monorepo: explicit recursive scan
goal -aur

# Monorepo: ask before each subproject
goal -aiu

# Preview only
goal -au --dry-run
```

| Flags | Behavior |
|-------|----------|
| `-u` | Upgrade dependencies before tests/commit |
| `-r` | Also scan subfolders (useful when root has its own manifest) |
| `-i` | Ask `Process project <path>?` before each subproject |
| `-a` without `-i` | Upgrade all detected projects automatically |
| `-a` with `-i` | Full workflow is automatic, but dependency upgrades are per-project prompts |

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

## Monorepo Sweep — `goal all`

When a folder holds many independent git repositories, `goal all` runs the full
`goal -a` workflow in every sub-repo that has **uncommitted changes**. Clean
repos and non-git folders are skipped.

```bash
# From the parent folder holding all your repos:
goal all ./*          # sweep every dirty sub-repo (lists them, asks once)
goal -a ./*           # identical shorthand: -a + paths ⇒ sweep
goal auto all         # `auto` is a word-form of -a; defaults to * (all sub-folders)

# Preview first, then run for real:
goal all ./* --dry-run
goal all ./* -y       # skip the batch confirmation
```

It prints the matched dirty projects, asks one confirmation (skipped with `-y`
or `--dry-run`), runs `goal -a` in each project, continues past failures, and
prints a succeeded/failed summary at the end. See
[Command Reference → `goal all`](commands.md#goal-all).

## Tips

1. **First time**: Run `goal init` to set up your project
2. **Daily use**: Just run `goal` for interactive workflow
3. **CI/CD**: Use `goal --all` for full automation
4. **Monorepo of repos**: Use `goal all ./*` to sweep every dirty sub-repo
5. **Preview**: Use `--dry-run` to check before committing
6. **Customize**: Edit `goal.yaml` to fit your workflow

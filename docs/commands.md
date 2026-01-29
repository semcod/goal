# Command Reference

Complete reference for all Goal commands and options.

## Global Options

These options can be used with any Goal command:

| Option | Short | Description |
|--------|-------|-------------|
| `--config PATH` | `-c PATH` | Path to goal.yaml config file |
| `--markdown` | | Use markdown output format (default) |
| `--ascii` | | Use ASCII output format |
| `--help` | `-h` | Show help message |
| `--version` | | Show version and exit |

## Main Commands

### `goal` (default)

Run the interactive push workflow.

```bash
goal [OPTIONS]
```

**Options:**
- `--bump, -b {patch,minor,major}`: Version bump type (default: patch)
- `--yes, -y`: Skip all prompts (run automatically)
- `--all, -a`: Automate all stages including tests, commit, push, and publish
- `--dry-run`: Show what would be done without doing it

**Examples:**
```bash
goal                          # Interactive workflow
goal --bump minor            # Interactive with minor bump
goal --yes                   # Automatic workflow
goal --all                   # Full automation
goal --dry-run               # Preview changes
```

### `goal push`

Add, commit, tag, and push changes to remote.

```bash
goal push [OPTIONS]
```

**Options:**
- `--bump, -b {patch,minor,major}`: Version bump type (default: patch)
- `--no-tag`: Skip creating git tag
- `--no-changelog`: Skip updating changelog
- `--no-version-sync`: Skip syncing version to project files
- `--message, -m TEXT`: Custom commit message
- `--dry-run`: Show what would be done without doing it
- `--yes, -y`: Skip all prompts
- `--split`: Create separate commits per change type
- `--ticket TEXT`: Ticket prefix for commit titles

**Examples:**
```bash
goal push                                    # Interactive
goal push --yes                              # Automatic
goal push --bump minor                       # Minor version bump
goal push -m "Custom message"                # Custom message
goal push --split                            # Split by type
goal push --no-tag                           # No git tag
goal push --dry-run                          # Preview
```

### `goal init`

Initialize Goal in current repository.

```bash
goal init [OPTIONS]
```

**Options:**
- `--force, -f`: Overwrite existing goal.yaml

**Creates:**
- `VERSION` file with initial version
- `CHANGELOG.md` with template
- `goal.yaml` with auto-detected settings

**Examples:**
```bash
goal init                # Initialize if not exists
goal init --force        # Regenerate config
```

### `goal status`

Show current git status and version info.

```bash
goal status [OPTIONS]
```

**Options:**
- `--markdown/--ascii`: Output format (default: markdown)

**Shows:**
- Current version
- Current branch
- Staged files
- Unstaged/untracked files

### `goal version`

Show or bump version.

```bash
goal version [OPTIONS]
```

**Options:**
- `--type, -t {patch,minor,major}`: Version bump type (default: patch)

**Examples:**
```bash
goal version              # Show current and next versions
goal version --bump minor # Show next minor version
```

### `goal commit`

Generate a smart commit message for current changes.

```bash
goal commit [OPTIONS]
```

**Options:**
- `--detailed, -d`: Generate detailed commit message with body
- `--unstaged, -u`: Analyze unstaged changes instead of staged
- `--markdown/--ascii`: Output format (default: markdown)
- `--ticket TEXT`: Ticket prefix for commit title

**Examples:**
```bash
goal commit               # Simple message
goal commit --detailed    # Detailed message with body
goal commit --unstaged    # Analyze unstaged changes
```

### `goal info`

Show detailed project information and version status.

```bash
goal info
```

**Shows:**
- Detected project types
- Current version
- Version files status
- Git information
- Recent tags
- Pending changes

## Configuration Commands

### `goal config`

Manage goal.yaml configuration.

#### `goal config show`

Show current configuration.

```bash
goal config show [OPTIONS]
```

**Options:**
- `--key, -k KEY`: Show specific config key (dot notation)

**Examples:**
```bash
goal config show                    # Show full config
goal config show -k project        # Show project section
goal config show -k git.commit.strategy  # Show specific key
```

#### `goal config get`

Get a configuration value.

```bash
goal config get KEY
```

**Arguments:**
- `KEY`: Configuration key (dot notation)

**Examples:**
```bash
goal config get project.name
goal config get versioning.files
```

#### `goal config set`

Set a configuration value.

```bash
goal config set KEY VALUE
```

**Arguments:**
- `KEY`: Configuration key (dot notation)
- `VALUE`: Value to set (JSON parsed for complex types)

**Examples:**
```bash
goal config set git.commit.scope "my-app"
goal config set versioning.bump_rules.minor 100
goal config set versioning.files '["VERSION", "pyproject.toml:version"]'
```

#### `goal config validate`

Validate goal.yaml configuration.

```bash
goal config validate
```

**Returns:**
- Success if configuration is valid
- List of errors if invalid

#### `goal config update`

Update goal.yaml based on project detection.

```bash
goal config update
```

**Updates:**
- Detected project types
- Version files
- Other auto-detected settings

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Git repository not found |
| 4 | Configuration error |
| 5 | Tests failed (when using --yes) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PYPI_TOKEN` | PyPI authentication token |
| `NPM_TOKEN` | npm authentication token |
| `CARGO_REGISTRY_TOKEN` | Cargo registry token |
| `GITHUB_TOKEN` | GitHub token for releases |

## Configuration File Location

Goal looks for `goal.yaml` in this order:

1. Path specified with `--config`
2. Current directory
3. Parent directories (up to git root)

## Examples by Use Case

### Development Workflow
```bash
# Make changes...
goal                    # Interactive commit and push
```

### CI/CD Pipeline
```bash
goal --all --bump patch    # Full automation
```

### Quick Fix
```bash
goal push -m "fix: critical bug" --yes
```

### Feature Branch
```bash
goal push --no-tag --no-changelog    # No release on feature branch
```

### Split Changes
```bash
goal push --split                     # Separate commits by type
```

### Custom Config
```bash
goal -c staging.yaml --all           # Use staging config
```

## See Also

- [Configuration Guide](configuration.md) - Detailed configuration options
- [Examples](examples.md) - Practical examples
- [Troubleshooting](troubleshooting.md) - Common issues

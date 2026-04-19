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

### `goal config`

View or manage user configuration stored in `~/.goal`.

```bash
goal config [OPTIONS]
```

**Options:**
- `--reset`: Reset configuration and run setup again
- `--show`: Show current configuration (default)

**Configuration includes:**
- Author name and email (from git config)
- Default license preference
- License classifier for package managers

**Examples:**
```bash
goal config                  # Show current configuration
goal config --reset          # Reset and reconfigure
```

**What it shows:**
```
======================================================================
  📋 Goal User Configuration
======================================================================

Config file: /home/tom/.goal

Current settings:
  Author name:  Tom Sapletta
  Author email: info@softreck.com
  License:      Apache License 2.0 (Apache-2.0)

💡 Tip: Run 'goal config --reset' to reconfigure
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

### `goal check-versions`

Validate version consistency across project files, README badges, and published registry versions.

```bash
goal check-versions [OPTIONS]
```

**Options:**
- `--update-badges`: Update README badges if they don't match current version

**Behavior:**
- Compares local version with registry versions (PyPI, npm, crates.io, RubyGems)
- Validates README badge versions match current version
- Checks version consistency across project files (package.json, pyproject.toml, etc.)
- Warns about mismatches before publishing

**Examples:**
```bash
goal check-versions                    # Check all versions
goal check-versions --update-badges  # Check and update badges
```

**Output:**
```
🔍 Version Check for v2.1.33
Detected project types: python

📦 Registry Versions:
  ✅ python: Version 2.1.33 is up to date

🏷️  README Badges:
  ✅ Badges are up to date

📁 Local Version Files:
  ✅ pyproject.toml: 2.1.33
  ✅ All version files are consistent

📋 Summary:
  ✅ All versions are consistent and ready for publishing!
```

### `goal publish`

Publish the current version to package registries.

```bash
goal publish [OPTIONS]
```

**Options:**
- `--yes, -y`: Skip confirmation prompts
- `--dry-run`: Show what would be published without doing it

**Behavior:**
- Detects project type and builds packages if needed
- Uploads only the current version artifacts (not everything in `dist/`)
- Shows clear error messages for common issues (File already exists, Authentication)

**Examples:**
```bash
goal publish                    # Interactive
goal publish --yes              # Automatic
```

**Note:** If a `Makefile` with a `publish` target exists, `goal publish` will use `make publish` instead.

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

### `goal wizard`

Interactive guided setup for new projects.

```bash
goal wizard [OPTIONS]
```

**Options:**
- `--reset`: Reset and reconfigure everything
- `--skip-git`: Skip git repository setup
- `--skip-user`: Skip user configuration
- `--skip-project`: Skip project configuration

**Description:**
The wizard walks you through complete project setup:
- Git repository initialization and remote configuration
- User configuration (name, email, license preference)
- Project configuration (name, description, versioning strategy)
- Commit message strategy and changelog settings

**Examples:**
```bash
goal wizard                    # Full interactive setup
goal wizard --skip-git         # Skip git setup
goal wizard --reset            # Reset all configuration
```

### `goal license`

Manage project licenses.

```bash
goal license <SUBCOMMAND> [OPTIONS]
```

**Subcommands:**

#### `goal license create <license_id>`
Create a LICENSE file with the specified license.

**Options:**
- `--fullname, -n TEXT`: Copyright holder full name
- `--year, -y INTEGER`: Copyright year
- `--force, -f`: Overwrite existing LICENSE file

**Examples:**
```bash
goal license create MIT --fullname "John Doe"
goal license create Apache-2.0 --year 2024
```

#### `goal license update`
Update existing LICENSE file.

**Options:**
- `--license, -l TEXT`: New SPDX license ID
- `--fullname, -n TEXT`: New copyright holder name
- `--year, -y INTEGER`: New copyright year

#### `goal license validate`
Validate the LICENSE file.

#### `goal license info <license_id>`
Show information about a license.

#### `goal license check <license1> <license2>`
Check compatibility between two licenses.

#### `goal license list`
List available license templates.

**Options:**
- `--custom`: Show only custom templates

#### `goal license template <license_id>`
Add or show custom license templates.

**Options:**
- `--file, -f PATH`: Template file path to add

### `goal authors`

Manage project authors and team members.

```bash
goal authors <SUBCOMMAND> [OPTIONS]
```

**Subcommands:**

#### `goal authors list`
List all project authors.

#### `goal authors add <name> <email>`
Add an author to the project.

**Options:**
- `--role, -r TEXT`: Author role or title
- `--alias, -a TEXT`: Short alias for reference

**Examples:**
```bash
goal authors add "Jane Doe" jane@example.com --role "Developer"
goal authors add "Bob Smith" bob@company.com --alias "bob"
```

#### `goal authors remove <email>`
Remove an author from the project.

#### `goal authors update <email>`
Update an author's information.

**Options:**
- `--name, -n TEXT`: New name
- `--role, -r TEXT`: New role
- `--alias, -a TEXT`: New alias

#### `goal authors import`
Import authors from git history.

#### `goal authors export`
Export authors to CONTRIBUTORS.md.

#### `goal authors find <identifier>`
Find an author by name, email, or alias.

#### `goal authors current`
Show current user's author information.

#### `goal authors co-author <name> <email>`
Generate a co-author trailer for commit messages.

### Co-author Support

Add co-authors to commits using the `--co-author` flag:

```bash
goal commit --co-author "Jane Doe <jane@example.com>"
goal commit --co-author "Jane <jane@example.com>" --co-author "Bob <bob@example.com>"
```

The co-author trailers are automatically formatted as:
```
Co-authored-by: Jane Doe <jane@example.com>
Co-authored-by: Bob Smith <bob@example.com>
```

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

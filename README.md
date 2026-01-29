# Goal

Automated git push with smart commit messages, changelog updates, version tagging, and interactive workflow.

## Features

- 🚀 **Interactive workflow** - Confirms each stage (test, commit, push, publish) with Y/n prompts
- 🧠 **Smart commit messages** - Generates conventional commits based on diff analysis
- 📦 **Multi-language support** - Python, Node.js, Rust, Go, Ruby, PHP, .NET, Java
- 🏷️ **Version management** - Automatic version bumping and synchronization across project files
- 📝 **Changelog updates** - Maintains CHANGELOG.md with version history
- 🐳 **CI/CD ready** - `--yes` flag for automated workflows
- 🧪 **Test integration** - Runs project-specific test commands before committing
- 📦 **Publish support** - Publishes to package managers (PyPI, npm, crates.io, etc.)

## Installation

```bash
pip install goal
```

## Quick Start

### 1. Initialize your repository

```bash
goal init
```

Creates `VERSION` and `CHANGELOG.md` files if they don't exist.

### 2. Run the interactive workflow

```bash
goal
```

This will guide you through:
- ✅ Run tests? [Y/n]
- ✅ Commit changes? [Y/n]
- ✅ Push to remote? [Y/n]
- ✅ Publish version X.X.X? [Y/n]

Press Enter to accept the default (Yes) for any step.

## Usage Examples

### Basic interactive workflow

```bash
# Run full interactive workflow with default patch bump
goal

# Run with minor version bump
goal --bump minor

# Run without prompts (for CI/CD)
goal --yes

# Automate ALL stages without any prompts
goal --all
```

### Using the push command directly

```bash
# Interactive push with prompts
goal push

# Split commits by change type (docs/code/ci/examples)
goal push --split

# Split + auto (CI style)
goal push --split --yes

# Split + add ticket prefix
goal push --split --ticket ABC-123

# Automatic push without prompts
goal push --yes

# Dry run to see what would happen
goal push --dry-run

# Custom commit message
goal push -m "feat: add new authentication system"

# Skip specific steps
goal push --no-tag --no-changelog
```

### Version management

```bash
# Check current version
goal version

# Bump specific version type
goal version --bump minor
goal version --bump major

# Check repository status
goal status
```

## Supported Project Types

Goal automatically detects your project type and uses appropriate commands:

| Language | Test Command | Publish Command | Version Files |
|----------|--------------|-----------------|---------------|
| **Python** | `pytest` | `python -m build && twine upload dist/*` | pyproject.toml, setup.py |
| **Node.js** | `npm test` | `npm publish` | package.json |
| **Rust** | `cargo test` | `cargo publish` | Cargo.toml |
| **Go** | `go test ./...` | `git push origin --tags` | go.mod (uses git tags) |
| **Ruby** | `bundle exec rspec` | `gem build *.gemspec && gem push *.gem` | *.gemspec |
| **PHP** | `composer test` | `composer publish` | composer.json |
| **.NET** | `dotnet test` | `dotnet pack && dotnet nuget push *.nupkg` | *.csproj |
| **Java** | `mvn test` | `mvn deploy` | pom.xml, build.gradle |

## Markdown Output

Goal outputs structured markdown by default (perfect for LLM consumption and CI/CD logs). Use `--ascii` to get the legacy console output.

```bash
# Default: markdown output
goal push
goal status

# Force legacy output
goal push --ascii
goal status --ascii

# Use with automation
goal --all > release.log
```

The markdown output includes:
- Front matter with metadata (command, version, file count)
- Structured sections for overview, files, and test results
- Code blocks for command outputs
- Summary with actions taken and next steps

Example output:
```markdown
---
command: goal push
project_types: ["python"]
version_bump: "1.0.1 -> 1.0.2"
file_count: 7
---

# Goal Push Result

## Overview
**Project Type:** python
**Files Changed:** 7 (+1140/-99 lines)
**Version:** 1.0.1 → 1.0.2
...
```

See [docs/markdown-output.md](docs/markdown-output.md) for detailed examples.

## Command Reference

### `goal` or `goal push`

Main command for the complete workflow.

**Options:**
- `--bump, -b`: Version bump type [patch|minor|major] (default: patch)
- `--yes, -y`: Skip all prompts (run automatically)
- `--all, -a`: Automate all stages including tests, commit, push, and publish
- `--markdown/--ascii`: Output format (default: markdown)
- `--split`: Create separate commits per change type (docs/code/ci/examples)
- `--ticket`: Ticket prefix to include in commit titles (overrides TICKERT)
- `--no-tag`: Skip creating git tag
- `--no-changelog`: Skip updating changelog
- `--no-version-sync`: Skip syncing version to project files
- `--message, -m`: Custom commit message
- `--dry-run`: Show what would be done without doing it

## Split commits (per type)

When `--split` is enabled, Goal will create multiple commits:

- **code**: changes in `goal/`, `src/`, `lib/`, `*.py`
- **docs**: `docs/*`, `README.md`, `*.md`
- **ci**: `.github/*`, `.gitlab/*`, `*.yml`/`*.yaml`
- **examples**: `examples/*`
- **other**: everything else

Then it will create a final **release metadata** commit with version bump + changelog (unless disabled).

## Ticket prefixing (TICKET)

Create a `TICKET` file in repository root:

```ini
prefix=ABC-123
format=[{ticket}] {title}
```

You can override it per run:

```bash
goal push --ticket ABC-123
goal push --split --ticket ABC-123
goal commit --ticket ABC-123
```

### `goal init`

Initialize goal in current repository.

Creates:
- `VERSION` file with initial version 1.0.0
- `CHANGELOG.md` with standard template

### `goal status`

Show current git status and version info.

Displays:
- Current version
- Current branch
- Staged files
- Unstaged/untracked files

### `goal version`

Show or bump version.

**Options:**
- `--type, -t`: Version bump type [patch|minor|major] (default: patch)

## Examples by Use Case

### Development Workflow

```bash
# Make your changes...
git add some/files

# Run goal with interactive prompts
goal

# Prompts will appear:
# Run tests? [Y/n] - Runs pytest for Python projects
# Commit changes? [Y/n] - Creates smart commit message
# Push to remote? [Y/n] - Pushes to origin with tags
# Publish version 1.2.3? [Y/n] - Publishes to PyPI/npm/etc
```

### Full Automation

```bash
# Automate everything - tests, commit, push, publish
goal --all

# Short form
goal -a

# With specific version bump
goal --all --bump minor
```

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Deploy with Goal
  run: |
    goal push --yes --bump minor
    
# Or with --all flag
- name: Full release
  run: |
    goal --all --bump patch
```

### Skip Testing in Quick Fixes

```bash
# Skip tests for documentation changes
goal push --yes -m "docs: update README"
```

### Pre-release Workflow

```bash
# Check what will be done
goal push --dry-run --bump minor

# Run with specific version bump
goal push --bump minor

# Or skip publishing for internal releases
goal push --yes --no-tag
```

## Configuration

Goal requires no configuration files. It works based on conventions:

1. **Version detection**: Looks for `VERSION` file first, then project-specific files
2. **Project detection**: Automatically detects project type from files
3. **Commit messages**: Uses conventional commit format based on diff analysis
4. **Changelog**: Updates CHANGELOG.md in Keep a Changelog format

## Integration Examples

### Makefile

```makefile
.PHONY: release patch minor major

# Interactive release
release:
	goal

# Automatic patch release
patch:
	goal push --yes

# Full automation release
all:
	goal --all

# Automatic minor release
minor:
	goal push --yes --bump minor

# Automatic major release
major:
	goal push --yes --bump major

# Dry run
dry-run:
	goal push --dry-run
```

### package.json scripts

```json
{
  "scripts": {
    "release": "goal",
    "release:patch": "goal push --yes",
    "release:all": "goal --all",
    "release:minor": "goal push --yes --bump minor",
    "release:major": "goal push --yes --bump major"
  }
}
```

### pre-commit hook

```bash
#!/bin/sh
# .git/hooks/pre-commit
goal push --dry-run
```

## Smart Commit Messages

Goal analyzes your changes to generate appropriate commit messages:

- **feat**: New features, additions
- **fix**: Bug fixes, patches
- **docs**: Documentation changes
- **style**: Formatting, linting
- **refactor**: Code restructuring
- **perf**: Performance improvements
- **test**: Test additions/changes
- **build**: Build system, CI/CD
- **chore**: Dependencies, maintenance

Examples:
- `feat: add user authentication`
- `fix: resolve memory leak in parser`
- `docs: update API documentation`
- `test: add coverage for payment module`

## Troubleshooting

### Tests fail but I want to continue

The interactive workflow will ask if you want to continue when tests fail:

```
Tests failed. Continue anyway? [y/N]
```

### Custom test/publish commands

If Goal doesn't detect your test command correctly, you can run them manually before using `goal push --yes`.

### Publishing fails

Ensure you're authenticated with the appropriate package manager:
- PyPI: `twine configure` or use `__token__`
- npm: `npm login`
- crates.io: `cargo login`

## License

Apache License 2.0
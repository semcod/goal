# Goal

<p align="center">
  <img src="https://img.shields.io/badge/version-2.1.4-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/pypi-goal-orange.svg" alt="PyPI">
  <a href="https://github.com/wronai/goal/actions"><img src="https://github.com/wronai/goal/workflows/CI/badge.svg" alt="CI"></a>
  <a href="https://coveralls.io/github/wronai/goal"><img src="https://coveralls.io/repos/github/wronai/goal/badge.svg" alt="Coverage"></a>
</p>

Automated git push with **enterprise-grade commit intelligence**, smart changelog updates, version tagging, and interactive workflow.

## 🆕 What's New in v2.1

> **Enterprise-Grade Commit Intelligence** - Transform statistical commit messages into business-value summaries

```
❌ BEFORE: refactor(core): add testing, logging, validation
✅ AFTER:  feat(goal): enterprise-grade commit intelligence engine

NEW CAPABILITIES:
├── deep code analysis engine: intelligent change detection
├── code relationship mapping: architecture understanding
└── code quality metrics: maintainability tracking

IMPACT: ⭐ Value score: 85/100 | 🔗 Relations: cli→generator
```

📖 [Full Documentation](docs/enhanced-summary.md) | 📂 [Examples](examples/enhanced-summary/)

## Features

- 🚀 **Interactive workflow** - Confirms each stage (test, commit, push, publish) with Y/n prompts
- 🧠 **Smart commit messages** - Generates conventional commits based on diff analysis
- 🎯 **Enhanced Summary** - Business-value focused messages with capabilities, metrics, relations
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

### 1. Install Goal

```bash
pip install goal
```

### 2. Initialize your repository

```bash
goal init
```

Creates `VERSION`, `CHANGELOG.md`, and `goal.yaml` with auto-detected settings.

### 3. Run the interactive workflow

```bash
goal
```

This will guide you through:
- ✅ Run tests? [Y/n]
- ✅ Commit changes? [Y/n]
- ✅ Push to remote? [Y/n]
- ✅ Publish version X.X.X? [Y/n]

Press Enter to accept the default (Yes) for any step.

## Documentation

📚 **Complete Documentation**: [docs/README.md](docs/README.md)

### Key Topics
- [Installation Guide](docs/installation.md) - Detailed installation instructions
- [Quick Start](docs/quickstart.md) - Get started in 5 minutes
- [Configuration Guide](docs/configuration.md) - Complete goal.yaml reference
- [Examples](docs/examples.md) - Real-world examples and use cases
- [CI/CD Integration](docs/ci-cd.md) - Use Goal in pipelines
- [Command Reference](docs/commands.md) - All commands and options

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

### Real-world examples

#### 1. Python project with pytest

```bash
# Make changes to your Python code
git add .

# Run the full workflow
goal

# Output:
# ✓ Detected project types: python
# ✓ Running tests: pytest tests/ -v
# ✓ Tests passed (23/23)
# ✓ Generated commit: feat(api): add user authentication endpoint
# ✓ Updated VERSION to 1.2.3
# ✓ Updated CHANGELOG.md
# ✓ Created tag v1.2.3
# ✓ Pushed to origin
# ? Publish to PyPI? [Y/n]: Y
# ✓ Published version 1.2.3
```

#### 2. Node.js project with npm

```bash
# Quick patch release for bug fix
goal push --yes -m "fix: resolve memory leak in parser"

# Output:
# ✓ Detected project types: nodejs
# ✓ Running tests: npm test
# ✓ Tests passed
# ✓ Committed: fix: resolve memory leak in parser
# ✓ Updated package.json to 1.0.1
# ✓ Updated CHANGELOG.md
# ✓ Created tag v1.0.1
# ✓ Pushed to origin
```

#### 3. Rust project with cargo

```bash
# Major release with breaking changes
goal push --bump major --yes

# Output:
# ✓ Detected project types: rust
# ✓ Running tests: cargo test
# ✓ All tests passed
# ✓ Generated commit: feat!: change public API structure
# ✓ Updated Cargo.toml to 2.0.0
# ✓ Updated CHANGELOG.md
# ✓ Created tag v2.0.0
# ✓ Pushed to origin
# ? Publish to crates.io? [Y/n]: Y
# ✓ Published crate v2.0.0
```

#### 4. Multi-language project

```bash
# Project with both Python backend and Node.js frontend
goal info

# Output:
# === Project Information ===
# Project types: python, nodejs
# Current version: 1.5.0
# 
# Version files:
#   ✓ VERSION: 1.5.0
#   ✓ package.json: 1.5.0
#   ✓ pyproject.toml: 1.5.0

# Run release - updates both package.json and pyproject.toml
goal push --yes
```

#### 5. Documentation updates

```bash
# Skip tests for docs-only changes
goal push --no-test -m "docs: update API documentation"

# Or let goal detect it's docs only
git add README.md docs/
goal push --yes

# Output:
# ✓ Detected project types: python
# ✓ Generated commit: docs: update API documentation
# ✓ Updated VERSION to 1.5.1
# ✓ Updated CHANGELOG.md
# ✓ Created tag v1.5.1
# ✓ Pushed to origin
```

#### 6. CI/CD automation

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    branches: [main]
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Goal
        run: pip install goal
      - name: Configure PyPI token
        run: echo "__token__=${{ secrets.PYPI_TOKEN }}" > ~/.pypirc
      - name: Release
        run: goal --all --bump patch
```

#### 7. Dry run for preview

```bash
# Preview what will happen
goal push --dry-run --bump minor

# Output:
# === DRY RUN ===
# Project types: python
# Files to commit: 12 (+342/-15 lines)
#   - src/auth.py (+120/-5)
#   - tests/test_auth.py (+85/-0)
#   - docs/api.md (+137/-10)
# Commit message: feat(auth): add OAuth2 integration
# Version: 1.5.0 -> 1.6.0
# Version sync: VERSION, pyproject.toml
# Tag: v1.6.0
```

#### 8. Custom commit message

```bash
# Override auto-generated message
goal push -m "feat: implement real-time notifications"

# Or use conventional commit format
goal push -m "fix(auth): resolve JWT token expiration issue"
```

#### 9. Split commits for large changes

```bash
# Split changes into logical commits
goal push --split --yes

# Output:
# ✓ Committed docs: update README and API docs
# ✓ Committed feat: add user authentication system
# ✓ Committed test: add comprehensive test coverage
# ✓ Committed chore: update dependencies and CI config
# ✓ Committed release: v2.0.0
```

#### 10. Skip specific steps

```bash
# Skip version bump for hotfix
goal push --yes --no-version-sync -m "hotfix: critical security patch"

# Skip changelog for minor tweak
goal push --yes --no-changelog -m "style: fix linting issues"

# Skip tag creation for experimental feature
goal push --yes --no-tag -m "feat: experimental AI integration"
```

### Using the push command directly

```bash
# Interactive push with prompts
goal push

# Automatic push without prompts
goal push --yes

# Dry run to see what would happen
goal push --dry-run

# Custom commit message
goal push -m "feat: add new authentication system"

# Skip specific steps
goal push --no-tag --no-changelog

# With version bump
goal push --bump minor

# Markdown output for CI/CD logs
goal push --markdown
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

### Working with Multiple Projects

```bash
# Monorepo with frontend and backend
# Structure:
# /backend (Python)
# /frontend (Node.js)
# /docs

# From root directory
goal info

# Output:
# Project types: python, nodejs
# Version files:
#   ✓ VERSION: 2.1.0
#   ✓ backend/pyproject.toml: 2.1.0
#   ✓ frontend/package.json: 2.1.0

# Release updates all projects
goal push --yes
```

### Hotfix Workflow

```bash
# Critical fix - skip tests and version bump
goal push --yes --no-test --no-version-sync -m "hotfix: security patch"

# Then create proper release
goal push --bump patch -m "release: v1.2.1 with security fix"
```

### Feature Branch Workflow

```bash
# On feature branch
goal push --yes --no-tag --no-publish

# After merge to main
goal push --bump minor --yes
```

### Release Candidate

```bash
# Create RC version
goal push --bump patch -m "release: v2.0.0-rc1"

# After testing, promote to stable
goal push --bump patch -m "release: v2.0.0 stable"
```

## Configuration

Goal uses `goal.yaml` for configuration. Run `goal init` to create it automatically with detected settings.

### goal.yaml Structure

```yaml
# goal.yaml - Goal configuration file
version: "1.0"

project:
  name: "my-project"           # Auto-detected from pyproject.toml/package.json
  type: ["python"]             # Auto-detected project types
  description: "My project"    # Auto-detected description

versioning:
  strategy: "semver"           # semver, calver, or date
  files:                       # Files to sync version to
    - "VERSION"
    - "pyproject.toml:version"
    - "package.json:version"
  bump_rules:                  # Auto-bump thresholds
    patch: 10                  # Files changed
    minor: 50                  # Lines added
    major: 200                 # Large changes

git:
  commit:
    strategy: "conventional"   # conventional, semantic, custom
    scope: "my-project"        # Default scope for commits
    templates:                 # Custom commit templates
      feat: "feat({scope}): {description}"
      fix: "fix({scope}): {description}"
      docs: "docs({scope}): {description}"
    classify_by:               # Classification methods
      - "file_extensions"
      - "directory_paths"
      - "line_stats"
      - "keywords_diff"
  changelog:
    enabled: true
    template: "keep-a-changelog"
    output: "CHANGELOG.md"
    sections: ["Added", "Changed", "Fixed", "Deprecated"]
  tag:
    enabled: true
    prefix: "v"
    format: "{prefix}{version}"

strategies:
  python:
    test: "pytest tests/ -v"
    build: "python -m build"
    publish: "twine upload dist/*"
  nodejs:
    test: "npm test"
    build: "npm run build"
    publish: "npm publish"

registries:
  pypi:
    url: "https://pypi.org/simple/"
    token_env: "PYPI_TOKEN"
  npm:
    url: "https://registry.npmjs.org/"
    token_env: "NPM_TOKEN"

hooks:
  pre_commit: ""               # Command to run before commit
  post_commit: ""              # Command to run after commit
  pre_push: ""                 # Command to run before push
  post_push: ""                # Command to run after push

advanced:
  auto_update_config: true     # Auto-update config on detection changes
  performance:
    max_files: 50              # Split commits if > N files
    timeout_test: 300          # Test timeout in seconds
```

### Config Commands

```bash
# Show full configuration
goal config show

# Show specific key (dot notation)
goal config show -k git.commit.strategy

# Get a value
goal config get project.name

# Set a value
goal config set git.commit.scope "my-app"

# Validate configuration
goal config validate

# Update config based on project detection
goal config update
```

### Custom Config File

```bash
# Use a custom config file
goal --config custom-goal.yaml push

# Or in CI/CD
goal -c .goal/ci.yaml --all
```

### Conventions (without goal.yaml)

Goal also works without configuration based on conventions:

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

# Release with custom message
release-message:
	goal push --yes -m "$(MSG)"

# Release from specific branch
release-branch:
	git checkout main
	git pull
	goal --all --bump $(BUMP)
```

### package.json scripts

```json
{
  "scripts": {
    "release": "goal",
    "release:patch": "goal push --yes",
    "release:all": "goal --all",
    "release:minor": "goal push --yes --bump minor",
    "release:major": "goal push --yes --bump major",
    "release:dry": "goal push --dry-run",
    "release:docs": "goal push --yes -m 'docs: update documentation'"
  }
}
```

### pre-commit hook

```bash
#!/bin/sh
# .git/hooks/pre-commit
echo "Running goal pre-commit check..."
goal push --dry-run
if [ $? -eq 0 ]; then
    echo "✅ Ready to commit!"
else
    echo "❌ Issues found. Fix them before committing."
    exit 1
fi
```

### Docker integration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install goal
RUN pip install goal

# Copy source code
COPY . .

# Run tests and release
CMD ["sh", "-c", "goal --all"]
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

### Common Issues

#### Goal doesn't detect my project type
```bash
# Check what's detected
goal info

# Manually specify in goal.yaml
project:
  type: ["python", "nodejs"]
```

#### Version sync not working
```bash
# Check version files
goal info

# Manually configure in goal.yaml
versioning:
  files:
    - "VERSION"
    - "my-app/__init__.py:__version__"
```

#### Tests timing out
```yaml
# In goal.yaml
advanced:
  performance:
    timeout_test: 600  # 10 minutes
```

#### Commit message not accurate
```bash
# Use custom message
goal push -m "your custom message"

# Or configure templates in goal.yaml
git:
  commit:
    templates:
      feat: "feat({scope}): {description}"
```

## Tips & Tricks

### 1. Use with aliases
```bash
# Add to ~/.bashrc or ~/.zshrc
alias g='goal'
alias gp='goal push --yes'
alias ga='goal --all'
alias gd='goal push --dry-run'
```

### 2. Team workflow
```bash
# For team development, use ticket prefixes
echo "prefix=PROJ-123" > TICKET
goal push --split  # Creates commits like "PROJ-123: feat: add feature"
```

### 3. Release checklist
```bash
# Before release
goal status      # Check status
goal push --dry-run  # Preview changes

# Release
goal --all       # Full automation
```

### 4. Working with feature flags
```bash
# Commit feature flag changes
goal push -m "feat: enable beta feature flag"

# Later, remove the flag
goal push -m "feat: launch feature to all users"
```

### 5. Automated releases on schedule
```yaml
# .github/workflows/scheduled-release.yml
name: Scheduled Release
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Goal
        run: pip install goal
      - name: Weekly Release
        run: goal --all --bump patch
```

## License

Apache License 2.0

---

<div align="center">
  <sub>Built with ❤️ by the community</sub>
</div>
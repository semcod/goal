# Quick Start

Get up and running with Goal in 5 minutes!

## Installation

```bash
pip install goal
```

Or install from source:

```bash
git clone https://github.com/wronai/goal.git
cd goal
pip install -e .
```

## Initialize Your Project

```bash
cd your-project
goal init
```

This creates:
- `VERSION` - Current version file
- `CHANGELOG.md` - Changelog template
- `goal.yaml` - Configuration with auto-detected settings

## Make Your First Commit

1. Make some changes to your project
2. Stage them: `git add .`
3. Run Goal:

```bash
goal push
```

Goal will:
- Analyze your changes
- Generate a smart commit message
- Update the version
- Update the changelog
- Create a git tag
- Push to remote

## Example Workflow

```bash
# 1. Initialize
goal init
# ✓ Created VERSION (1.0.0)
# ✓ Created CHANGELOG.md
# ✓ Created goal.yaml with auto-detected settings
#   Project: my-app (python)

# 2. Make changes
echo "print('Hello, World!')" > app.py
git add app.py

# 3. Commit with Goal
goal push
# ✓ Detected project types: python
# ✓ Generated commit message: feat: add app.py
# ✓ Updated VERSION to 1.0.1
# ✓ Updated CHANGELOG.md
# ✓ Created tag: v1.0.1
# ✓ Successfully pushed to main

# 4. Check status
goal status
# Version: 1.0.1
# Branch: main
# No staged files
# No unstaged/untracked files
```

## Common Commands

```bash
# Interactive workflow (default)
goal

# Automatic workflow (no prompts)
goal --yes

# Full automation (tests, commit, push, publish)
goal --all

# Specify version bump
goal --bump minor

# Generate commit message only
goal commit

# Check current version
goal version

# Dry run (preview)
goal push --dry-run
```

## Next Steps

- Read the [Configuration Guide](configuration.md) to customize Goal
- Check out [Examples](examples.md) for advanced workflows
- See [Command Reference](commands.md) for all options

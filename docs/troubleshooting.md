# Troubleshooting

Common issues and solutions when using Goal.

# Check if you're in a goal repository with local changes
ls -la goal/ goal/cli.py 2>/dev/null || echo "Not in goal repo"

# If you're in the goal repo and want to use the local version:
python3 -m goal  # instead of just 'goal'

# If using Python 3 specifically:
python3 -m pip install goal

# Check PATH
echo $PATH | grep -o "[^:]*" | grep -E "(local|user)"
```

# Install with user permissions
pip install --user goal

# Add to PATH if needed
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

# Or navigate to git repository
cd /path/to/your/repo

# Find goal.yaml
find . -name "goal.yaml" -type f

# Use custom config
goal --config /path/to/config.yaml push
```

# Validate configuration
goal config validate

# ✗ project.name is required
goal config set project.name "my-project"

# ✗ Invalid versioning.strategy
goal config set versioning.strategy "semver"

# ✗ Version file not found
goal config update  # Auto-detects files
```

# Check config location
goal config show -k project.name

# Manual edit
goal config set versioning.files '["VERSION", "pyproject.toml:version"]'
```

# Check staged files
git diff --cached --name-only

# Use unstaged changes
goal commit --unstaged
```

# Use custom message
goal push -m "Your custom message"

# Configure templates
goal config set git.commit.templates.feat "feat({scope}): add {description}"
```

# Check if files are already committed
git log --oneline -1

# Check untracked files
git ls-files --others --exclude-standard

# Add specific files
git add specific_file.py
goal push
```

# Check version files
goal config get versioning.files

# Manual version sync
goal config set versioning.files '["VERSION", "pyproject.toml:version"]'
goal push --yes -m "chore: sync version"
```

# Fix version format
echo "1.0.0" > VERSION
git add VERSION

# Or use semver format
goal config set versioning.strategy "semver"
```

# Check bump rules
goal config show -k versioning.bump_rules

# Adjust thresholds
goal config set versioning.bump_rules.minor 100
goal config set versioning.bump_rules.major 500
```

# Skip tests
goal push --yes -m "fix: critical hotfix"

# Or disable tests in config
goal config set strategies.python.test ""
```

# Check project type
goal config get project.type

# Set custom test command
goal config set strategies.python.test "python -m pytest"
goal config set strategies.nodejs.test "npm run test:ci"
```

# Set timeout in config
goal config set advanced.performance.timeout_test 120

# Or run tests manually
pytest tests/
goal push --yes
```

### File already exists on PyPI

If you see `HTTPError: 400 Bad Request ... File already exists`, it means you're trying to upload a package version that's already on PyPI.

```bash
# Quick fix: clean dist and rebuild
rm -rf dist build *.egg-info
python -m build
# Upload ONLY the current version artifacts
twine upload dist/*your-package-{version}*

# Or let goal handle it correctly (goal v2.1.23+):
python3 -m goal  # use local version if in goal repo
```

**Why this happens**: `twine upload dist/*` uploads ALL files in dist/, including old versions. Goal v2.1.23+ automatically filters to upload only the current version.

# Option 1: ~/.pypirc
[pypi]
username = __token__
password = pypi-xxxxxxxx

# Option 2: Environment variables
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxx

# Option 3: Configure in goal.yaml
goal config set registries.pypi.token_env "PYPI_TOKEN"
export PYPI_TOKEN=pypi-xxxxxxxx
```

# Check project type
goal config get project.type

# Python:
pip install build twine
# Rust:
cargo install cargo-publish
```

# Set upstream branch
git push --set-upstream origin main

# Or specify branch explicitly
goal config set git.push.branch "main"
```

# Use git command then goal for versioning
git push --force-with-lease
goal push --no-push  # Skip push in Goal
```

# Use test PyPI first
goal config set registries.testpypi.token_env "TEST_PYPI_TOKEN"
goal config set strategies.python.publish "twine upload --repository testpypi dist/*"
```

# Check package.json
cat package.json | grep version

# Dry run publish
npm publish --dry-run
```

# Check cargo login
cargo login --registry crates.io

# Check Cargo.toml
cat Cargo.toml | grep version

# Dry run
cargo publish --dry-run
```

# Check file count
git ls-files | wc -l

# Configure max_files for splitting
goal config set advanced.performance.max_files 30

# Use specific paths
goal push --no-all
```

# Or exclude files
echo "*.log" >> .gitignore
git add .gitignore
```

# Check hook configuration
goal config get hooks.pre_commit

# Run hook manually
bash -c "$(goal config get hooks.pre_commit)"

# Temporarily disable
goal config set hooks.pre_commit ""
```

# Check if script is executable
chmod +x scripts/my-hook.sh

# Use absolute path
goal config set hooks.pre_commit "/full/path/to/script.sh"
```

# GitHub Actions
- name: Install Goal
  run: pip install goal

# Or include in requirements.txt
echo "goal" >> requirements.txt
pip install -r requirements.txt
```

# Configure git user
git config user.name "CI Bot"
git config user.email "ci@bot.com"

# Or use environment
git config user.name "$GITHUB_ACTOR"
git config user.email "$GITHUB_ACTOR@users.noreply.github.com"
```

# Set in CI config
env:
  PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}

# Or export
export PYPI_TOKEN="your-token"
```

# Use git commands directly
git -c trace=true status

# Check config
goal config show
```

# Show full config
goal config show > config-debug.yaml

# Validate
goal config validate

# Check specific values
goal config get project.name
goal config get versioning.files
```

# Check staged files
git diff --cached --stat

# Check last commit
git log --oneline -1

# Solution: Stage your changes
git add .
goal push
```

# Solution: Fix tests or skip them
goal push  # Will prompt to continue
# or
goal push --yes -m "fix: skip tests"
```

# Solution: Create VERSION file or configure version files
echo "1.0.0" > VERSION
git add VERSION
# or
goal config update
```

# Solution: Validate and fix config
goal config validate
goal config set project.name "my-project"
```

### Check version

```bash
goal --version
```

### Check help

```bash
goal --help
goal push --help
goal config --help
```

# Collect information
goal --version > issue-info.txt
goal config show >> issue-info.txt
git status >> issue-info.txt

### Community resources

- [GitHub Issues](https://github.com/wronai/goal/issues)
- [GitHub Discussions](https://github.com/wronai/goal/discussions)
- [Documentation](https://github.com/wronai/goal/docs)

# Reset to last good state
git log --oneline
git reset --hard HEAD~1

# Try again
goal push --dry-run
```

# Set correct version manually
echo "1.0.1" > VERSION
git add VERSION
git commit -m "chore: fix version"

# Create missing tag
git tag v1.0.1
git push origin v1.0.1
```

# Backup current config
cp goal.yaml goal.yaml.backup

# Restore custom settings
goal config set git.commit.scope "my-scope"
```

# Troubleshooting

Common issues and solutions when using Goal.

## General Issues

### Goal command not found

```bash
# Check installation
pip show goal

# If not installed
pip install goal

# If using Python 3 specifically
python3 -m pip install goal

# Check PATH
which goal
echo $PATH | grep -o "[^:]*"
```

### Permission denied

```bash
# Install with user permissions
pip install --user goal

# Add to PATH if needed
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

### Git repository not found

```bash
# Initialize git repository
git init

# Or navigate to git repository
cd /path/to/your/repo

# Verify git status
git status
```

## Configuration Issues

### goal.yaml not found

```bash
# Check current directory
ls -la goal.yaml

# Find goal.yaml
find . -name "goal.yaml" -type f

# Create config
goal init

# Use custom config
goal --config /path/to/config.yaml push
```

### Configuration validation errors

```bash
# Validate configuration
goal config validate

# Common errors and fixes:
# ✗ project.name is required
goal config set project.name "my-project"

# ✗ Invalid versioning.strategy
goal config set versioning.strategy "semver"

# ✗ Version file not found
goal config update  # Auto-detects files
```

### Config not updating

```bash
# Force update from detection
goal config update

# Check config location
goal config show -k project.name

# Manual edit
goal config set versioning.files '["VERSION", "pyproject.toml:version"]'
```

## Commit Issues

### No changes to commit

```bash
# Check git status
git status

# Stage changes
git add .

# Check staged files
git diff --cached --name-only

# Use unstaged changes
goal commit --unstaged
```

### Generated commit message is wrong

```bash
# Generate message without committing
goal commit

# Use custom message
goal push -m "Your custom message"

# Configure templates
goal config set git.commit.templates.feat "feat({scope}): add {description}"
```

### Commit fails with "nothing to commit"

```bash
# Check if files are already committed
git log --oneline -1

# Check untracked files
git ls-files --others --exclude-standard

# Add specific files
git add specific_file.py
goal push
```

## Version Issues

### Version not updating in files

```bash
# Check version files
goal config get versioning.files

# Verify current version
goal version

# Manual version sync
goal config set versioning.files '["VERSION", "pyproject.toml:version"]'
goal push --yes -m "chore: sync version"
```

### Version format error

```bash
# Check current version
cat VERSION

# Fix version format
echo "1.0.0" > VERSION
git add VERSION

# Or use semver format
goal config set versioning.strategy "semver"
```

### Bump rules not working

```bash
# Check bump rules
goal config show -k versioning.bump_rules

# Adjust thresholds
goal config set versioning.bump_rules.minor 100
goal config set versioning.bump_rules.major 500
```

## Test Issues

### Tests failing but you want to continue

```bash
# Interactive - will prompt to continue
goal push

# Skip tests
goal push --yes -m "fix: critical hotfix"

# Or disable tests in config
goal config set strategies.python.test ""
```

### Test command not found

```bash
# Check project type
goal config get project.type

# Set custom test command
goal config set strategies.python.test "python -m pytest"
goal config set strategies.nodejs.test "npm run test:ci"
```

### Tests taking too long

```bash
# Set timeout in config
goal config set advanced.performance.timeout_test 120

# Or run tests manually
pytest tests/
goal push --yes
```

## Push Issues

### Push fails - authentication error

```bash
# Check git remote
git remote -v

# Configure credentials
git config --global credential.helper store

# Or use token-based auth
git remote set-url origin https://token@github.com/user/repo.git
```

### Push fails - branch not found

```bash
# Check current branch
git branch

# Set upstream branch
git push --set-upstream origin main

# Or specify branch explicitly
goal config set git.push.branch "main"
```

### Push fails - force push needed

```bash
# Goal doesn't support force push directly
# Use git command then goal for versioning
git push --force-with-lease
goal push --no-push  # Skip push in Goal
```

## Publish Issues

### PyPI publish fails

```bash
# Check token
echo $PYPI_TOKEN

# Test upload
twine check dist/*

# Use test PyPI first
goal config set registries.testpypi.token_env "TEST_PYPI_TOKEN"
goal config set strategies.python.publish "twine upload --repository testpypi dist/*"
```

### npm publish fails

```bash
# Check authentication
npm whoami

# Check package.json
cat package.json | grep version

# Dry run publish
npm publish --dry-run
```

### Cargo publish fails

```bash
# Check cargo login
cargo login --registry crates.io

# Check Cargo.toml
cat Cargo.toml | grep version

# Dry run
cargo publish --dry-run
```

## Performance Issues

### Goal is slow

```bash
# Check file count
git ls-files | wc -l

# Configure max_files for splitting
goal config set advanced.performance.max_files 30

# Use specific paths
goal push --no-all
```

### Large repository issues

```bash
# Use split commits
goal push --split

# Or exclude files
echo "*.log" >> .gitignore
git add .gitignore
```

## Hook Issues

### Pre-commit hook failing

```bash
# Check hook configuration
goal config get hooks.pre_commit

# Run hook manually
bash -c "$(goal config get hooks.pre_commit)"

# Temporarily disable
goal config set hooks.pre_commit ""
```

### Hook not running

```bash
# Check if script is executable
chmod +x scripts/my-hook.sh

# Check permissions
ls -la scripts/

# Use absolute path
goal config set hooks.pre_commit "/full/path/to/script.sh"
```

## CI/CD Issues

### Goal not found in CI

```yaml
# GitHub Actions
- name: Install Goal
  run: pip install goal

# Or include in requirements.txt
echo "goal" >> requirements.txt
pip install -r requirements.txt
```

### Git configuration in CI

```bash
# Configure git user
git config user.name "CI Bot"
git config user.email "ci@bot.com"

# Or use environment
git config user.name "$GITHUB_ACTOR"
git config user.email "$GITHUB_ACTOR@users.noreply.github.com"
```

### Environment variables not available

```bash
# Check environment
env | grep TOKEN

# Set in CI config
env:
  PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}

# Or export
export PYPI_TOKEN="your-token"
```

## Debug Mode

### Enable verbose output

```bash
# Goal doesn't have verbose flag yet
# Use git commands directly
git -c trace=true status

# Check config
goal config show
```

### Debug configuration

```bash
# Show full config
goal config show > config-debug.yaml

# Validate
goal config validate

# Check specific values
goal config get project.name
goal config get versioning.files
```

### Debug git state

```bash
# Check git status
git status

# Check staged files
git diff --cached --stat

# Check last commit
git log --oneline -1

# Check tags
git tag -l
```

## Common Error Messages

### "No changes to commit"

```bash
# Solution: Stage your changes
git add .
goal push
```

### "Tests failed - aborting"

```bash
# Solution: Fix tests or skip them
goal push  # Will prompt to continue
# or
goal push --yes -m "fix: skip tests"
```

### "Version file not found"

```bash
# Solution: Create VERSION file or configure version files
echo "1.0.0" > VERSION
git add VERSION
# or
goal config update
```

### "Invalid configuration"

```bash
# Solution: Validate and fix config
goal config validate
goal config set project.name "my-project"
```

## Getting Help

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

### Create issue report

```bash
# Collect information
goal --version > issue-info.txt
goal config show >> issue-info.txt
git status >> issue-info.txt

# Include in GitHub issue
```

### Community resources

- [GitHub Issues](https://github.com/wronai/goal/issues)
- [GitHub Discussions](https://github.com/wronai/goal/discussions)
- [Documentation](https://github.com/wronai/goal/docs)

## Recovery Procedures

### Restore from failed release

```bash
# Reset to last good state
git log --oneline
git reset --hard HEAD~1

# Check version
cat VERSION

# Try again
goal push --dry-run
```

### Manual version recovery

```bash
# Set correct version manually
echo "1.0.1" > VERSION
git add VERSION
git commit -m "chore: fix version"

# Create missing tag
git tag v1.0.1
git push origin v1.0.1
```

### Configuration recovery

```bash
# Backup current config
cp goal.yaml goal.yaml.backup

# Regenerate config
goal init --force

# Restore custom settings
goal config set git.commit.scope "my-scope"
```

# Configuration Guide

Goal uses `goal.yaml` for configuration. Run `goal init` to create it automatically with detected settings.

## Creating Configuration

```bash
# Initialize with auto-detected settings
goal init

# Force regenerate (overwrite existing)
goal init --force
```

## Configuration Structure

### Project Settings

```yaml
project:
  name: "my-project"           # Auto-detected from pyproject.toml/package.json
  type: ["python"]             # Auto-detected project types
  description: "My project"    # Auto-detected description
```

**Project Types:** `python`, `nodejs`, `rust`, `go`, `ruby`, `php`, `dotnet`, `java`

### Versioning

```yaml
versioning:
  strategy: "semver"           # semver, calver, or date
  files:                       # Files to sync version to
    - "VERSION"
    - "pyproject.toml:version"
    - "package.json:version"
    - "Cargo.toml:version"
  bump_rules:                  # Auto-bump thresholds
    patch: 10                  # Files changed
    minor: 50                  # Lines added
    major: 200                 # Large changes
```

### Git Configuration

```yaml
git:
  commit:
    strategy: "conventional"   # conventional, semantic, custom
    scope: "my-project"        # Default scope for commits
    templates:                 # Custom commit templates
      feat: "feat({scope}): {description}"
      fix: "fix({scope}): {description}"
      docs: "docs({scope}): {description}"
      style: "style({scope}): {description}"
      refactor: "refactor({scope}): {description}"
      perf: "perf({scope}): {description}"
      test: "test({scope}): {description}"
      build: "build({scope}): {description}"
      chore: "chore({scope}): {description}"
    classify_by:               # Classification methods
      - "file_extensions"
      - "directory_paths"
      - "line_stats"
      - "keywords_diff"
  changelog:
    enabled: true
    template: "keep-a-changelog"
    output: "CHANGELOG.md"
    sections: ["Added", "Changed", "Fixed", "Deprecated", "Removed", "Security"]
  tag:
    enabled: true
    prefix: "v"
    format: "{prefix}{version}"
```

### Build Strategies

```yaml
strategies:
  python:
    test: "pytest tests/ -v"
    build: "python -m build"
    publish: "twine upload dist/*"
    dependencies:
      file: "requirements.txt"
      lock: "pip freeze > requirements.txt"
  nodejs:
    test: "npm test"
    build: "npm run build"
    publish: "npm publish"
    dependencies:
      file: "package-lock.json"
      lock: "npm install"
  rust:
    test: "cargo test"
    build: "cargo build --release"
    publish: "cargo publish"
    dependencies:
      file: "Cargo.lock"
      lock: "cargo update"
```

### Registry Configuration

```yaml
registries:
  pypi:
    url: "https://pypi.org/simple/"
    token_env: "PYPI_TOKEN"
  npm:
    url: "https://registry.npmjs.org/"
    token_env: "NPM_TOKEN"
  cargo:
    url: "https://crates.io/"
    token_env: "CARGO_REGISTRY_TOKEN"
```

### Hooks

```yaml
hooks:
  pre_commit: "black . && isort ."     # Format code before commit
  post_commit: "git push origin HEAD"  # Push after commit
  pre_push: "pytest tests/"            # Run tests before push
  post_push: "npm run deploy"          # Deploy after push
```

### Advanced Settings

```yaml
advanced:
  auto_update_config: true     # Auto-update config on detection changes
  performance:
    max_files: 50              # Split commits if > N files
    timeout_test: 300          # Test timeout in seconds
```

## Configuration Commands

### Show Configuration

```bash
# Show full configuration
goal config show

# Show specific section
goal config show -k git.commit

# Show specific key
goal config show -k project.name
```

### Get Values

```bash
# Get project name
goal config get project.name
# Output: my-project

# Get version files
goal config get versioning.files
# Output:
# - VERSION
# - pyproject.toml:version
# - package.json:version
```

### Set Values

```bash
# Set commit scope
goal config set git.commit.scope "my-app"

# Set custom test command
goal config set strategies.python.test "pytest -xvs"

# Disable changelog
goal config set git.changelog.enabled false

# Set array value
goal config set versioning.files '["VERSION", "pyproject.toml:version"]'
```

### Validate Configuration

```bash
goal config validate
# ✓ Configuration is valid
# or
# ✗ Configuration errors:
#   ✗ project.name is required
```

### Update Configuration

```bash
# Update based on project detection
goal config update
# ✓ Configuration updated with detected changes
```

## Examples

### Python Project

```yaml
project:
  name: "my-python-app"
  type: ["python"]
  
versioning:
  strategy: "semver"
  files:
    - "VERSION"
    - "pyproject.toml:version"
    - "myapp/__init__.py:__version__"
    
strategies:
  python:
    test: "pytest tests/ -v --cov"
    build: "python -m build"
    publish: "twine upload dist/*"
    
hooks:
  pre_commit: "black . && isort . && flake8"
  pre_push: "pytest tests/"
```

### Node.js Project

```yaml
project:
  name: "my-node-app"
  type: ["nodejs"]
  
versioning:
  strategy: "semver"
  files:
    - "VERSION"
    - "package.json:version"
    
strategies:
  nodejs:
    test: "npm test"
    build: "npm run build"
    publish: "npm publish"
    
hooks:
  pre_commit: "npm run lint"
  pre_push: "npm test && npm run build"
```

### Multi-Language Project

```yaml
project:
  name: "fullstack-app"
  type: ["python", "nodejs"]
  
versioning:
  strategy: "semver"
  files:
    - "VERSION"
    - "backend/pyproject.toml:version"
    - "frontend/package.json:version"
    
strategies:
  python:
    test: "cd backend && pytest"
    build: "cd backend && python -m build"
  nodejs:
    test: "cd frontend && npm test"
    build: "cd frontend && npm run build"
    
hooks:
  pre_commit: "cd backend && black . && cd ../frontend && npm run lint"
  pre_push: "cd backend && pytest && cd ../frontend && npm test"
```

## Custom Config Files

```bash
# Use custom config
goal --config staging.yaml push

# Environment-specific configs
goal -c .goal/production.yaml --all
goal -c .goal/development.yaml --bump patch
```

### Example: Production Config

```yaml
# .goal/production.yaml
versioning:
  strategy: "semver"
  bump_rules:
    patch: 5
    minor: 25
    major: 100
    
git:
  tag:
    prefix: "release-"
    
hooks:
  pre_push: "pytest tests/ -x && npm run build:prod"
  post_push: "npm run deploy:prod"
```

## Environment Variables

Goal supports environment variables in configuration:

```yaml
registries:
  pypi:
    token_env: "PYPI_TOKEN"  # Reads from $PYPI_TOKEN
  npm:
    token_env: "NPM_TOKEN"   # Reads from $NPM_TOKEN
    
hooks:
  post_push: "${DEPLOY_SCRIPT}"  # Reads from $DEPLOY_SCRIPT
```

## Configuration Precedence

1. Command-line flags (`--config`, `--bump`, etc.)
2. Custom config file (`goal --config custom.yaml`)
3. Local `goal.yaml` in project root
4. Parent directory `goal.yaml` (up to git root)
5. Default values

## Tips

- Use `goal config update` after adding new project files
- Store sensitive data in environment variables, not config
- Keep `goal.yaml` in version control
- Use separate configs for different environments
- Validate config with `goal config validate` in CI

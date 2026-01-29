# Examples

This page contains practical examples of using Goal in various scenarios.

## Basic Workflows

### 1. Simple Python Project

```bash
# Initialize
goal init

# Make changes...
echo "print('Hello')" > app.py
git add app.py

# Commit and push
goal push

# Output:
# ✓ Detected project types: python
# ✓ Generated commit message: feat: add app.py
# ✓ Updated VERSION to 1.0.1
# ✓ Updated CHANGELOG.md
# ✓ Created tag: v1.0.1
# ✓ Successfully pushed to main
```

### 2. Node.js Project

```bash
# Initialize with custom settings
goal init

# Configure test command
goal config set strategies.nodejs.test "npm run test:coverage"

# Make changes...
npm run lint
git add .

# Commit with custom message
goal push -m "feat: add user authentication"

# Automatic version bump
goal --bump minor --yes
```

### 3. Documentation Updates

```bash
# Update README
echo "## New Section" >> README.md
git add README.md

# Goal will detect it's a docs change
goal push

# Output:
# ✓ Generated commit message: docs: update README
```

## Advanced Workflows

### 4. Split Commits by Type

```bash
# Make changes in multiple areas
touch src/api.py src/utils.py
touch docs/api.md
touch .github/workflows/ci.yml
git add .

# Create separate commits for each type
goal push --split

# Result:
# ✓ Committed (code): feat: add api and utils modules
# ✓ Committed (docs): docs: update API documentation
# ✓ Committed (ci): build: add CI workflow
# ✓ Committed (release): chore(release): bump version to 1.1.0
```

### 5. Custom Commit Templates

```yaml
# goal.yaml
git:
  commit:
    templates:
      feat: "✨ {scope}: {description}"
      fix: "🐛 {scope}: {description}"
      docs: "📚 {scope}: {description}"
```

```bash
# Result will use emojis
goal push
# ✨ api: add authentication endpoints
```

### 6. Ticket Integration

```bash
# Create TICKET file
echo "prefix=ABC-123" > TICKET

# Or override per command
goal push --ticket JIRA-456

# Result:
# feat: [ABC-123] add user profile
```

## CI/CD Examples

### 7. GitHub Actions

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
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install Goal
        run: pip install goal
        
      - name: Configure PyPI token
        run: echo "PYPI_TOKEN=${{ secrets.PYPI_TOKEN }}" >> $GITHUB_ENV
        
      - name: Release
        run: goal --all --bump patch
```

### 8. GitLab CI

```yaml
# .gitlab-ci.yml
release:
  stage: deploy
  script:
    - pip install goal
    - goal config set registries.pypi.token_env "$PYPI_TOKEN"
    - goal --all --bump minor
  only:
    - main
```

### 9. Docker-based CI

```dockerfile
# Dockerfile.ci
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install goal
RUN goal config set strategies.python.test "pytest --cov"

CMD ["goal", "--all"]
```

## Project-Specific Examples

### 10. Python Package

```yaml
# goal.yaml for Python package
project:
  name: "my-package"
  type: ["python"]

versioning:
  files:
    - "VERSION"
    - "pyproject.toml:version"
    - "src/mypackage/__init__.py:__version__"

strategies:
  python:
    test: "pytest -xvs --cov=mypackage"
    build: "python -m build"
    publish: "twine upload dist/*"

hooks:
  pre_commit: "black src/ tests/ && isort src/ tests/"
  pre_push: "pytest && mypy src/"
```

### 11. React App

```yaml
# goal.yaml for React app
project:
  name: "my-react-app"
  type: ["nodejs"]

strategies:
  nodejs:
    test: "npm test -- --coverage --watchAll=false"
    build: "npm run build"
    publish: "npm publish"

hooks:
  pre_commit: "npm run lint && npm run format"
  pre_push: "npm test && npm run build"
```

### 12. Rust Crate

```yaml
# goal.yaml for Rust project
project:
  name: "my-crate"
  type: ["rust"]

versioning:
  files:
    - "VERSION"
    - "Cargo.toml:version"

strategies:
  rust:
    test: "cargo test"
    build: "cargo build --release"
    publish: "cargo publish"

hooks:
  pre_commit: "cargo fmt && cargo clippy"
  pre_push: "cargo test && cargo doc"
```

### 13. Full-Stack Application

```yaml
# goal.yaml for full-stack app
project:
  name: "fullstack-app"
  type: ["python", "nodejs"]

versioning:
  strategy: "calver"  # Use calendar versioning
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
  pre_commit: |
    cd backend && black . &&
    cd ../frontend && npm run lint
  pre_push: |
    cd backend && pytest &&
    cd ../frontend && npm test &&
    cd ../frontend && npm run build
```

## Special Scenarios

### 14. Monorepo with Multiple Packages

```bash
# Structure:
# my-monorepo/
# ├── packages/pkg1/
# ├── packages/pkg2/
# └── goal.yaml

# goal.yaml
project:
  name: "my-monorepo"
  type: ["python"]

versioning:
  files:
    - "VERSION"
    - "packages/pkg1/pyproject.toml:version"
    - "packages/pkg2/pyproject.toml:version"

# Update all packages
goal push --bump minor --yes
```

### 15. Automated Release with Changelog

```bash
# Make many changes...
git add .

# Dry run to see what will happen
goal push --dry-run --bump minor

# Check the generated changelog
cat CHANGELOG.md

# If happy, run the actual release
goal push --bump minor --yes
```

### 16. Hotfix Workflow

```bash
# On main branch, create hotfix
git checkout -b hotfix/critical-bug

# Fix the bug
echo "# Fixed critical bug" >> CHANGELOG.md
git add .

# Quick patch release
goal push --bump patch --yes

# Merge back to main
git checkout main
git merge hotfix/critical-bug
git push origin main
```

### 17. Feature Branch Workflow

```bash
# Create feature branch
git checkout -b feature/new-api

# Work on feature...
git add .
goal push --no-tag --no-changelog  # Don't create tags on feature branch

# When ready to merge
git checkout main
git merge feature/new-api
goal push --bump minor  # Now create the release
```

## Custom Workflows

### 18. Pre-release Workflow

```bash
# Create release candidate
goal config set git.tag.prefix "rc-"
goal push --bump minor

# Test the release...
# If good, promote to stable
goal config set git.tag.prefix "v"
goal push --bump patch  # Creates v1.2.0 from rc-1.2.0
```

### 19. Automated Dependency Updates

```bash
# Update dependencies
pip-compile requirements.in
npm update

# Goal will detect dependency files and use "chore" type
goal push -m "chore: update dependencies"

# Or let Goal generate the message
goal push  # Will generate: chore: update requirements.txt
```

### 20. Migration Script

```bash
# Run migration
python manage.py migrate

# Commit migration
goal push -m "feat: add user profile migration"

# Goal will update version and create tag
```

## Troubleshooting Examples

### 21. Tests Failing

```bash
# Tests fail, but you want to continue
goal push

# Tests failed. Continue anyway? [y/N]
y

# Or skip tests entirely
goal push --yes -m "fix: critical hotfix"
```

### 22. Large Changes

```bash
# Many files changed (>50)
goal push

# Will automatically split due to max_files setting
# ✓ Committed (code): feat: add authentication system
# ✓ Committed (docs): docs: update API docs
# ✓ Committed (release): chore(release): bump version to 2.0.0
```

### 23. Manual Version Override

```bash
# Set specific version
echo "2.5.0" > VERSION
git add VERSION

# Commit without bumping
goal push --no-version-sync -m "chore: set version to 2.5.0"
```

## Tips and Tricks

- Use `goal push --dry-run` to preview changes
- `goal config show` to see current configuration
- `goal status` to check repository state
- Use TICKET file for automatic ticket prefixes
- Configure hooks for automated quality checks
- Use different configs for different environments
- Keep goal.yaml in version control for team consistency

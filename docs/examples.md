# Examples

This page contains practical examples of using Goal in various scenarios.

# Make changes...
echo "print('Hello')" > app.py
git add app.py

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

# Update README
echo "## New Section" >> README.md
git add README.md

# Make changes in multiple areas
touch src/api.py src/utils.py
touch docs/api.md
touch .github/workflows/ci.yml
git add .

# goal.yaml
git:
  commit:
    templates:
      feat: "✨ {scope}: {description}"
      fix: "🐛 {scope}: {description}"
      docs: "📚 {scope}: {description}"
```

```bash
# Create TICKET file
echo "prefix=ABC-123" > TICKET

# Or override per command
goal push --ticket JIRA-456

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

# Dockerfile.ci
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install goal
RUN goal config set strategies.python.test "pytest --cov"

CMD ["goal", "--all"]
```

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

# Dry run to see what will happen
goal push --dry-run --bump minor

# If happy, run the actual release
goal push --bump minor --yes
```

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

# Create release candidate
goal config set git.tag.prefix "rc-"
goal push --bump minor

# If good, promote to stable
goal config set git.tag.prefix "v"
goal push --bump patch  # Creates v1.2.0 from rc-1.2.0
```

# Update dependencies
pip-compile requirements.in
npm update

# Goal will detect dependency files and use "chore" type
goal push -m "chore: update dependencies"

# Or let Goal generate the message
goal push  # Will generate: chore: update requirements.txt
```

# Run migration
python manage.py migrate

# Commit migration
goal push -m "feat: add user profile migration"

# Or skip tests entirely
goal push --yes -m "fix: critical hotfix"
```

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

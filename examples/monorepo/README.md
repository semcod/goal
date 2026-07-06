# Monorepo Setup

Multi-package repository configuration for Goal.

## Structure

```
monorepo/
├── packages/
│   ├── frontend/          # Node.js React app
│   │   └── package.json
│   ├── backend/          # Python FastAPI
│   │   └── pyproject.toml
│   └── shared/           # Shared library
│       └── package.json
├── VERSION               # Shared version
├── goal.yaml            # Monorepo config
└── .github/
    └── workflows/
        └── release.yml   # Unified release
```

## Configuration

### goal.yaml

```yaml
version: "1.0"

project:
  name: "my-monorepo"
  type: "monorepo"
  versioning:
    strategy: "synchronized"  # All packages same version
    files:
      - VERSION
      - packages/frontend/package.json
      - packages/backend/pyproject.toml
      - packages/shared/package.json

commit:
  conventional:
    scopes:
      - frontend
      - backend
      - shared
      - root
    require_scope: true

advanced:
  monorepo:
    packages_dir: "packages"
    release_command: "goal --all"
```

### Package Configurations

#### packages/frontend/package.json

```json
{
  "name": "@myorg/frontend",
  "version": "1.0.0",
  "scripts": {
    "test": "jest",
    "build": "vite build"
  }
}
```

#### packages/backend/pyproject.toml

```toml
[project]
name = "myorg-backend"
version = "1.0.0"
dependencies = [
    "fastapi>=0.100.0",
    "@myorg/shared@^1.0.0",
]

[project.optional-dependencies]
dev = ["pytest", "goal>=2.1.0"]
```

## Workflows

### Development

```bash
# Work on frontend
cd packages/frontend
goal push --yes --no-publish

# Work on backend
cd packages/backend
goal push --yes --no-publish
```

### Coordinated Release

```bash
# Root directory - releases all packages
cd /monorepo

# Update root VERSION
echo "1.1.0" > VERSION

# Sync all packages
goal push --yes --bump minor

# All packages get version 1.1.0
```

### Independent Releases

```yaml
# goal.yaml for independent versioning
version: "1.0"

project:
  type: "monorepo"
  versioning:
    strategy: "independent"  # Each package own version
```

```bash
# Release just frontend
cd packages/frontend
goal push --bump minor --yes

# Release just backend  
cd packages/backend
goal push --bump patch --yes
```

## CI/CD Setup

### .github/workflows/monorepo-release.yml

```yaml
name: Monorepo Release

on:
  push:
    branches: [main]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.changes.outputs.frontend }}
      backend: ${{ steps.changes.outputs.backend }}
    steps:
      - uses: actions/checkout@v3
      - uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            frontend:
              - 'packages/frontend/**'
            backend:
              - 'packages/backend/**'

  release-frontend:
    needs: detect-changes
    if: ${{ needs.detect-changes.outputs.frontend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install -g goal
      - run: |
          cd packages/frontend
          goal push --yes --bump patch

  release-backend:
    needs: detect-changes
    if: ${{ needs.detect-changes.outputs.backend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install goal
      - run: |
          cd packages/backend
          goal push --yes --bump patch
```

## Commands

### Root Commands

```bash
# Status of all packages
goal status

# Release all
goal --all

# Sweep: run `goal -a` in every sub-repo that has uncommitted changes
goal all ./*          # lists dirty sub-repos, asks once, runs goal -a in each
goal -a ./*           # identical shorthand
goal auto all         # word-form of -a; defaults to * (all sub-folders)
goal all ./* --dry-run   # preview first (no commits/pushes)

# Upgrade dependencies in all subprojects (auto-discovers manifests)
goal -au

# Upgrade dependencies interactively (ask per subproject)
goal -aiu

# Sync versions to all packages
goal version --sync
```

### Dependency Updates in Monorepos

When the repository root has no `pyproject.toml` or lockfile, Goal scans
subfolders for manifests and runs the appropriate updater (`uv sync --upgrade`,
`pip install --upgrade`, `npm update`, etc.) in each detected project.

```bash
cd /monorepo

# CI / nightly: upgrade everything automatically
goal -au

# Developer: pick which packages to upgrade
goal -aiu

# Root also has a manifest — include subfolders explicitly
goal -aur

# Preview planned upgrade commands
goal -au --dry-run
```

Ignored directories during the scan include `.git`, `.venv`, `node_modules`,
`__pycache__`, `.pytest_cache`, and similar build/cache folders.

### Package Commands

```bash
# Frontend specific
cd packages/frontend
goal doctor
goal push --yes

# Backend specific
cd packages/backend  
goal doctor
goal push --yes
```

## Best Practices

1. **Use Conventional Commits with Scope**
   ```
   feat(frontend): add login button
   fix(backend): resolve auth bug
   ```

2. **Synchronized vs Independent**
   - Synchronized: User-facing products
   - Independent: Library collections

3. **Testing**
   ```bash
   # Test all packages
   for pkg in packages/*; do
     cd $pkg && goal push --yes --no-publish
   done
   ```

4. **Changelog Strategy**
   - Root: High-level changes
   - Each package: Detailed changes

## Troubleshooting

### Version Sync Issues

```bash
# Force version sync
goal version --sync --force

# Check mismatches
goal doctor --check-versions
```

### Cross-Package Dependencies

```toml
# In pyproject.toml
[project.dependencies]
shared = { path = "../shared" }
```

```json
// In package.json
{
  "dependencies": {
    "@myorg/shared": "file:../shared"
  }
}
```

## See Also

- [Advanced Workflows](../advanced-workflows/)
- [CI/CD Integration](../../github-actions/)

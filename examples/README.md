# Goal Examples

This directory contains example configurations and workflows for using Goal with different project types.

## Directory Structure

```
examples/
├── README.md              # This file
├── python-package/        # Python package example
│   └── pyproject.toml     # Python project configuration
├── nodejs-app/           # Node.js application example
│   └── package.json      # Node.js project configuration
├── rust-crate/           # Rust crate example
│   └── Cargo.toml        # Rust project configuration
├── makefile/             # Makefile integration example
│   └── Makefile          # Makefile with Goal targets
└── github-actions/       # CI/CD integration example
    └── .github/workflows/
        └── release.yml   # GitHub Actions workflow
```

## Usage Examples

### 1. Python Package

```bash
cd examples/python-package
goal init
goal --all
```

This example shows a typical Python package structure with:
- `pyproject.toml` for modern Python packaging
- pytest configuration for testing
- build and twine for publishing to PyPI

### 2. Node.js Application

```bash
cd examples/nodejs-app
goal init
goal push --yes --bump minor
```

This example demonstrates:
- `package.json` with npm scripts
- Jest for testing
- npm publish for distribution

### 3. Rust Crate

```bash
cd examples/rust-crate
goal init
goal --all
```

Features shown:
- `Cargo.toml` configuration
- Cargo test for testing
- Cargo publish for crates.io

### 4. Makefile Integration

```bash
cd examples/makefile
make help      # Show available targets
make release   # Interactive release
make patch     # Automatic patch release
make all       # Full automation with goal --all
```

The Makefile example includes:
- Development targets (test, lint, format)
- Release targets (patch, minor, major)
- CI/CD helper targets

### 5. GitHub Actions

The GitHub Actions workflow demonstrates:
- Automated testing on multiple Python versions
- Automatic releases on main branch push
- Manual releases with workflow dispatch
- Docker image building and publishing
- PyPI publishing

## Common Patterns

### Interactive Development

```bash
# Make changes
git add .
goal  # Interactive prompts for each stage
```

### Full Automation

```bash
# Automate everything
goal --all
# or
goal -a

# With specific version bump
goal --all --bump minor
```

### CI/CD Integration

```yaml
# GitHub Actions
- name: Release
  run: goal push --yes --bump patch

# Makefile in CI
make ci-release
```

### Custom Workflows

```bash
# Skip tests for docs
goal push --yes -m "docs: update README"

# Dry run to check
goal push --dry-run

# Custom commit message
goal push -m "feat: add new feature"
```

## Best Practices

1. **Always use `goal init`** when starting a new project
2. **Use `--dry-run`** to preview changes before releasing
3. **Configure CI/CD** to use `goal push --yes` for automation
4. **Use semantic versioning** with appropriate bump types
5. **Keep tests fast** so they don't block releases
6. **Authenticate before publishing** to package registries

## Troubleshooting

### Tests Fail

```bash
# Run tests manually first
pytest
npm test
cargo test

# Then release with confidence
goal --all
```

### Publish Fails

```bash
# Check authentication
twine check
npm whoami
cargo login

# Retry publishing
goal push --yes
```

### Git Issues

```bash
# Check git status
goal status

# Ensure clean working directory
git add .
goal push
```

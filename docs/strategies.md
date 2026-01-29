# Project Strategies

Goal supports multiple project types with configurable strategies for testing, building, and publishing.

## Supported Project Types

| Type | Detection Files | Default Test | Default Build | Default Publish |
|------|----------------|--------------|---------------|-----------------|
| Python | `pyproject.toml`, `setup.py`, `requirements.txt` | `pytest` | `python -m build` | `twine upload dist/*` |
| Node.js | `package.json`, `package-lock.json` | `npm test` | `npm run build` | `npm publish` |
| Rust | `Cargo.toml`, `Cargo.lock` | `cargo test` | `cargo build --release` | `cargo publish` |
| Go | `go.mod`, `go.sum` | `go test ./...` | `go build ./...` | `git push origin --tags` |
| Ruby | `Gemfile`, `*.gemspec` | `bundle exec rspec` | `gem build` | `gem push` |
| PHP | `composer.json`, `composer.lock` | `composer test` | `composer build` | `composer publish` |
| .NET | `*.csproj`, `*.fsproj` | `dotnet test` | `dotnet pack` | `dotnet nuget push` |
| Java | `pom.xml`, `build.gradle` | `mvn test` | `mvn package` | `mvn deploy` |

## Configuring Strategies

### Python Strategy

```yaml
strategies:
  python:
    test: "pytest tests/ -v --cov"
    build: "python -m build"
    publish: "twine upload dist/*"
    dependencies:
      file: "requirements.txt"
      lock: "pip freeze > requirements.txt"
```

#### Advanced Python Setup

```yaml
strategies:
  python:
    test: "pytest -xvs --cov=src --cov-report=html"
    build: |
      python -m build
      python -m twine check dist/*
    publish: "twine upload --skip-existing dist/*"
    dependencies:
      file: "requirements-dev.txt"
      lock: "pip-compile requirements.in"
    pre_release:
      - "mypy src/"
      - "black --check src/"
      - "isort --check-only src/"
    post_release:
      - "git push origin --tags"
      - "gh release create v{version} --generate-notes"
```

### Node.js Strategy

```yaml
strategies:
  nodejs:
    test: "npm test"
    build: "npm run build"
    publish: "npm publish"
    dependencies:
      file: "package-lock.json"
      lock: "npm install"
```

#### Advanced Node.js Setup

```yaml
strategies:
  nodejs:
    test: "npm run test:coverage"
    build: |
      npm run build
      npm run bundle
    publish: |
      npm publish --access public
      npm publish --tag beta
    dependencies:
      file: "package-lock.json"
      lock: "npm ci"
    pre_release:
      - "npm run lint"
      - "npm run type-check"
    post_release:
      - "npm run deploy:prod"
```

### Rust Strategy

```yaml
strategies:
  rust:
    test: "cargo test"
    build: "cargo build --release"
    publish: "cargo publish"
    dependencies:
      file: "Cargo.lock"
      lock: "cargo update"
```

#### Advanced Rust Setup

```yaml
strategies:
  rust:
    test: "cargo test --all-features"
    build: |
      cargo build --release
      cargo clippy -- -D warnings
    publish: "cargo publish"
    dependencies:
      file: "Cargo.lock"
      lock: "cargo update"
    pre_release:
      - "cargo fmt -- --check"
      - "cargo clippy -- -D warnings"
      - "cargo doc --no-deps"
    post_release:
      - "cargo publish --dry-run"
```

### Multi-Language Projects

```yaml
strategies:
  python:
    test: "cd backend && pytest"
    build: "cd backend && python -m build"
    publish: "cd backend && twine upload dist/*"
  nodejs:
    test: "cd frontend && npm test"
    build: "cd frontend && npm run build"
    publish: "cd frontend && npm publish"
  rust:
    test: "cd cli && cargo test"
    build: "cd cli && cargo build --release"
    publish: "cd cli && cargo publish"
```

## Custom Strategies

### Creating Custom Strategy

```yaml
strategies:
  my-framework:
    test: "my-framework test"
    build: "my-framework build"
    publish: "my-framework publish"
    dependencies:
      file: "my-deps.txt"
      lock: "my-framework lock"
```

### Strategy Variables

You can use variables in strategy commands:

```yaml
strategies:
  python:
    test: "pytest -k '{test_filter}'"
    build: "python -m build --outdir '{build_dir}'"
    publish: "twine upload {build_dir}/*"
    variables:
      test_filter: "not slow"
      build_dir: "dist"
```

## Version Files Configuration

### Python Projects

```yaml
versioning:
  files:
    - "VERSION"
    - "pyproject.toml:version"
    - "src/mypackage/__init__.py:__version__"
    - "docs/conf.py:version"
```

### Node.js Projects

```yaml
versioning:
  files:
    - "VERSION"
    - "package.json:version"
    - "package-lock.json:version"
```

### Rust Projects

```yaml
versioning:
  files:
    - "VERSION"
    - "Cargo.toml:version"
    - "Cargo.lock"  # Will be updated by cargo update
```

### Multi-Language Projects

```yaml
versioning:
  files:
    - "VERSION"
    - "backend/pyproject.toml:version"
    - "frontend/package.json:version"
    - "cli/Cargo.toml:version"
```

## Registry Configuration

### PyPI Configuration

```yaml
registries:
  pypi:
    url: "https://pypi.org/simple/"
    token_env: "PYPI_TOKEN"
  testpypi:
    url: "https://test.pypi.org/simple/"
    token_env: "TEST_PYPI_TOKEN"
```

### Private Registries

```yaml
registries:
  private_pypi:
    url: "https://pypi.mycompany.com/simple/"
    token_env: "PRIVATE_PYPI_TOKEN"
  private_npm:
    url: "https://npm.mycompany.com/"
    token_env: "PRIVATE_NPM_TOKEN"
```

### Multiple Registries

```yaml
strategies:
  python:
    publish: |
      twine upload --repository testpypi dist/*
      sleep 30
      twine upload --repository pypi dist/*
```

## Hooks Integration

### Pre-commit Hooks

```yaml
hooks:
  pre_commit: |
    # Python formatting
    black . && isort .
    # Node.js formatting
    npm run format
    # Rust formatting
    cargo fmt
```

### Pre-push Hooks

```yaml
hooks:
  pre_push: |
    # Run all tests
    pytest tests/
    npm test
    cargo test
    # Quality checks
    mypy src/
    npm run lint
    cargo clippy
```

### Post-push Hooks

```yaml
hooks:
  post_push: |
    # Deploy to staging
    npm run deploy:staging
    # Notify team
    curl -X POST "$SLACK_WEBHOOK" -d "text='New version deployed'"
```

## Examples by Use Case

### Data Science Project

```yaml
strategies:
  python:
    test: "pytest tests/ -v"
    build: "python setup.py sdist bdist_wheel"
    publish: "twine upload dist/* --repository pypi"
    dependencies:
      file: "environment.yml"
      lock: "conda env export > environment.yml"

hooks:
  pre_commit: "black . && isort . && flake8"
  pre_push: "pytest tests/ && nbstripout notebooks/*.ipynb"
```

### Web Application

```yaml
strategies:
  nodejs:
    test: "npm run test:ci"
    build: "npm run build:prod"
    publish: "npm publish"
  python:
    test: "pytest api/tests/"
    build: "docker build -t myapp:$VERSION ."
    publish: "docker push myapp:$VERSION"

hooks:
  pre_commit: "npm run lint && black api/"
  pre_push: "npm run test:e2e && pytest api/tests/"
  post_push: "kubectl set image deployment/myapp myapp:$VERSION"
```

### CLI Tool

```yaml
strategies:
  rust:
    test: "cargo test"
    build: |
      cargo build --release
      strip target/release/mycli
    publish: "cargo publish"
    post_release:
      - "cargo doc --no-deps"
      - "gh-pages --doc target/doc"
```

### Library with Multiple Languages

```yaml
strategies:
  python:
    test: "pytest -xvs python/tests/"
    build: "cd python && python -m build"
    publish: "cd python && twine upload dist/*"
  nodejs:
    test: "cd js && npm test"
    build: "cd js && npm run build"
    publish: "cd js && npm publish"
  ruby:
    test: "cd ruby && bundle exec rspec"
    build: "cd ruby && gem build"
    publish: "cd ruby && gem push"

versioning:
  files:
    - "VERSION"
    - "python/pyproject.toml:version"
    - "js/package.json:version"
    - "ruby/lib/version.rb"
```

## Best Practices

1. **Use specific test commands** instead of generic ones
2. **Include quality checks** in pre-commit hooks
3. **Separate build and publish** for better control
4. **Use environment variables** for sensitive data
5. **Test publish commands** with dry-run flags
6. **Document custom strategies** for your team

## Troubleshooting

### Common Issues

1. **Command not found**
   ```yaml
   # Use full paths or activate virtualenv
   test: "/path/to/venv/bin/pytest"
   ```

2. **Permission denied**
   ```yaml
   # Use proper permissions
   publish: "sudo -E twine upload dist/*"
   ```

3. **Registry authentication**
   ```yaml
   # Check token environment variable
   registries:
     pypi:
       token_env: "PYPI_TOKEN"  # Must be set in environment
   ```

# Registry Configuration

Goal supports configuring multiple package registries for publishing your projects.

## Supported Registries

| Registry | Language | Default URL | Token Environment |
|----------|----------|-------------|-------------------|
| PyPI | Python | https://pypi.org/simple/ | `PYPI_TOKEN` |
| Test PyPI | Python | https://test.pypi.org/simple/ | `TEST_PYPI_TOKEN` |
| npm | Node.js | https://registry.npmjs.org/ | `NPM_TOKEN` |
| GitHub Packages | Node.js | https://npm.pkg.github.com/ | `GITHUB_TOKEN` |
| crates.io | Rust | https://crates.io/ | `CARGO_REGISTRY_TOKEN` |
| Gemfury | Ruby | https://rubygems.org/ | `GEMFURY_TOKEN` |
| Private Registry | Any | Custom URL | Custom |

## Basic Configuration

### Single Registry

```yaml
# goal.yaml
registries:
  pypi:
    url: "https://pypi.org/simple/"
    token_env: "PYPI_TOKEN"
```

### Multiple Registries

```yaml
registries:
  pypi:
    url: "https://pypi.org/simple/"
    token_env: "PYPI_TOKEN"
  testpypi:
    url: "https://test.pypi.org/simple/"
    token_env: "TEST_PYPI_TOKEN"
  private:
    url: "https://pypi.mycompany.com/simple/"
    token_env: "PRIVATE_PYPI_TOKEN"
```

## Python Registries

### PyPI Production

```yaml
registries:
  pypi:
    url: "https://pypi.org/simple/"
    token_env: "PYPI_TOKEN"

strategies:
  python:
    publish: "twine upload dist/*"
```

### Test PyPI

```yaml
registries:
  testpypi:
    url: "https://test.pypi.org/simple/"
    token_env: "TEST_PYPI_TOKEN"

strategies:
  python:
    publish: "twine upload --repository testpypi dist/*"
```

### Private PyPI Server

```yaml
registries:
  private:
    url: "https://pypi.company.com/simple/"
    token_env: "COMPANY_PYPI_TOKEN"
    username_env: "COMPANY_PYPI_USER"

strategies:
  python:
    publish: |
      twine upload \
        --repository-url https://pypi.company.com/legacy/ \
        --username $COMPANY_PYPI_USER \
        --password $COMPANY_PYPI_TOKEN \
        dist/*
```

### Multiple Python Registries

```yaml
strategies:
  python:
    publish: |
      # Publish to Test PyPI first
      twine upload --repository testpypi dist/*
      
      # Wait for propagation
      sleep 30
      
      # Then publish to production
      twine upload dist/*
```

## Node.js Registries

### npm Public

```yaml
registries:
  npm:
    url: "https://registry.npmjs.org/"
    token_env: "NPM_TOKEN"

strategies:
  nodejs:
    publish: "npm publish"
```

### GitHub Packages

```yaml
registries:
  github:
    url: "https://npm.pkg.github.com/"
    token_env: "GITHUB_TOKEN"

strategies:
  nodejs:
    publish: "npm publish --registry https://npm.pkg.github.com/"
```

### Private npm Registry

```yaml
registries:
  private:
    url: "https://npm.company.com/"
    token_env: "COMPANY_NPM_TOKEN"

strategies:
  nodejs:
    publish: "npm publish --registry https://npm.company.com/"
```

### Scoped Packages

```yaml
strategies:
  nodejs:
    publish: "npm publish --access public"
    # For private scoped packages:
    # publish: "npm publish --access private"
```

## Rust Registries

### crates.io

```yaml
registries:
  cargo:
    url: "https://crates.io/"
    token_env: "CARGO_REGISTRY_TOKEN"

strategies:
  rust:
    publish: "cargo publish"
```

### Alternative Registry

```yaml
registries:
  private_cargo:
    url: "https://crates.company.com/"
    token_env: "COMPANY_CARGO_TOKEN"

strategies:
  rust:
    publish: "cargo publish --registry private"
```

## Ruby Registries

### RubyGems

```yaml
registries:
  rubygems:
    url: "https://rubygems.org/"
    token_env: "RUBYGEMS_API_KEY"

strategies:
  ruby:
    publish: "gem push *.gem"
```

### Gemfury

```yaml
registries:
  gemfury:
    url: "https://push.fury.io/"
    token_env: "GEMFURY_TOKEN"

strategies:
  ruby:
    publish: "gem push *.gem --host https://push.fury.io/username/"
```

## Authentication

### API Tokens

Most registries use API tokens:

```bash
# Set environment variables
export PYPI_TOKEN="pypi-xxxxxx"
export NPM_TOKEN="npm_xxxxxx"
export GITHUB_TOKEN="ghp_xxxxxx"
export CARGO_REGISTRY_TOKEN="xxxxxx"
```

### In CI/CD

#### GitHub Actions

```yaml
env:
  PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
  NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

#### GitLab CI

```yaml
variables:
  PYPI_TOKEN: $PYPI_TOKEN
  NPM_TOKEN: $NPM_TOKEN
```

#### Jenkins

```groovy
environment {
    PYPI_TOKEN = credentials('pypi-token')
    NPM_TOKEN = credentials('npm-token')
}
```

### Username/Password

Some registries require username/password:

```yaml
registries:
  private:
    url: "https://registry.company.com/"
    username_env: "REGISTRY_USER"
    password_env: "REGISTRY_PASS"

strategies:
  python:
    publish: |
      twine upload \
        --username $REGISTRY_USER \
        --password $REGISTRY_PASS \
        dist/*
```

## Advanced Configuration

### Conditional Publishing

```yaml
strategies:
  python:
    publish: |
      if [ "$BRANCH" = "main" ]; then
        twine upload dist/*
      else
        echo "Not publishing from branch $BRANCH"
      fi
```

### Dry Run Publishing

```yaml
strategies:
  python:
    publish: "twine upload --skip-existing dist/*"
  nodejs:
    publish: "npm publish --dry-run"
  rust:
    publish: "cargo publish --dry-run"
```

### Publishing with Delay

```yaml
strategies:
  python:
    publish: |
      twine upload dist/*
      echo "Waiting for index update..."
      sleep 60
      curl -X POST "$NOTIFICATION_WEBHOOK" \
        -d "text='Package published to PyPI'"
```

### Multi-Registry Publishing

```yaml
strategies:
  nodejs:
    publish: |
      # Publish to npm
      npm publish
      
      # Publish to GitHub Packages
      npm publish --registry https://npm.pkg.github.com/
      
      # Publish to private registry
      npm publish --registry https://npm.company.com/
```

## Environment-Specific Registries

### Development

```yaml
# .goal/development.yaml
registries:
  npm:
    url: "http://localhost:4873/"
    token_env: "DEV_NPM_TOKEN"
```

### Staging

```yaml
# .goal/staging.yaml
registries:
  pypi:
    url: "https://test.pypi.org/simple/"
    token_env: "STAGING_PYPI_TOKEN"
```

### Production

```yaml
# .goal/production.yaml
registries:
  pypi:
    url: "https://pypi.org/simple/"
    token_env: "PROD_PYPI_TOKEN"
```

## Security Best Practices

### 1. Use Environment Variables

Never hardcode tokens in configuration:

```yaml
# Bad
registries:
  pypi:
    token: "pypi-xxxxxx"

# Good
registries:
  pypi:
    token_env: "PYPI_TOKEN"
```

### 2. Scoped Tokens

Use minimal permission tokens:

```bash
# PyPI - scoped to specific package
pypi-token --project my-package

# npm - automation-only token
npm token create --read-only false
```

### 3. Token Rotation

Regularly rotate tokens:

```yaml
hooks:
  post_push: |
    # Notify to rotate token
    curl -X POST "$SECURITY_WEBHOOK" \
      -d "text='Remember to rotate $REGISTRY token'"
```

### 4. Audit Trail

Log publishing activity:

```yaml
strategies:
  python:
    publish: |
      echo "Publishing to PyPI at $(date)" >> publish.log
      twine upload dist/*
      echo "Published successfully at $(date)" >> publish.log
```

## Troubleshooting

### Authentication Errors

```bash
# Test PyPI token
twine check dist/*

# Test npm token
npm whoami

# Test cargo token
cargo login --registry crates.io
```

### Registry Not Found

```yaml
# Verify URL format
registries:
  pypi:
    url: "https://pypi.org/simple/"  # Must end with /
```

### Permission Denied

```yaml
# Check token permissions
strategies:
  python:
    publish: |
      twine upload --verbose dist/*  # Shows error details
```

### Network Issues

```yaml
# Use proxy if needed
strategies:
  python:
    publish: |
      https_proxy=$HTTPS_PROXY twine upload dist/*
```

## Examples

### Complete Python Package Setup

```yaml
# goal.yaml
project:
  name: "my-package"
  type: ["python"]

registries:
  pypi:
    url: "https://pypi.org/simple/"
    token_env: "PYPI_TOKEN"
  testpypi:
    url: "https://test.pypi.org/simple/"
    token_env: "TEST_PYPI_TOKEN"

strategies:
  python:
    test: "pytest -xvs --cov"
    build: "python -m build"
    publish: |
      if [ "$ENVIRONMENT" = "production" ]; then
        twine upload dist/*
      else
        twine upload --repository testpypi dist/*
      fi

hooks:
  post_push: |
    curl -X POST "$SLACK_WEBHOOK" \
      -d "text='Published my-package v$VERSION'"
```

### Multi-Language Project

```yaml
project:
  name: "fullstack-app"
  type: ["python", "nodejs"]

registries:
  pypi:
    url: "https://pypi.org/simple/"
    token_env: "PYPI_TOKEN"
  npm:
    url: "https://registry.npmjs.org/"
    token_env: "NPM_TOKEN"

strategies:
  python:
    test: "cd backend && pytest"
    build: "cd backend && python -m build"
    publish: "cd backend && twine upload dist/*"
  nodejs:
    test: "cd frontend && npm test"
    build: "cd frontend && npm run build"
    publish: "cd frontend && npm publish"
```

## Registry-Specific Documentation

- [PyPI API tokens](https://pypi.org/help/#apitoken)
- [npm access tokens](https://docs.npmjs.com/creating-and-viewing-access-tokens)
- [GitHub Packages authentication](https://docs.github.com/en/packages/learn-github-packages/authenticating-to-github-packages)
- [Cargo publish tokens](https://doc.rust-lang.org/cargo/reference/publishing.html)
- [RubyGems API credentials](https://guides.rubygems.org/rubygems-org-api-key/)

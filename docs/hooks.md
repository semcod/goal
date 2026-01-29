# Hooks

Goal supports pre/post hooks for commit and push operations, allowing you to automate tasks like formatting, testing, and deployment.

## Hook Types

| Hook | When it Runs | Use Cases |
|------|--------------|-----------|
| `pre_commit` | Before creating a commit | Code formatting, linting, quick tests |
| `post_commit` | After commit is created | Notifications, documentation generation |
| `pre_push` | Before pushing to remote | Full test suite, security scans |
| `post_push` | After successful push | Deployment, release announcements |

## Configuration

### Basic Hook Setup

```yaml
# goal.yaml
hooks:
  pre_commit: "black . && isort ."
  post_commit: "git push origin HEAD"
  pre_push: "pytest tests/"
  post_push: "npm run deploy"
```

### Multiple Commands

```yaml
hooks:
  pre_commit: |
    black .
    isort .
    flake8 .
    mypy src/
  
  pre_push: |
    pytest tests/ -v
    npm audit
    safety check
```

### Conditional Hooks

```bash
#!/bin/bash
# scripts/pre-commit.sh

# Only run Python hooks if Python files changed
if git diff --cached --name-only | grep -E '\.py$'; then
    echo "Running Python hooks..."
    black .
    isort .
    flake8 .
fi

# Only run Node.js hooks if JS/TS files changed
if git diff --cached --name-only | grep -E '\.(js|ts|jsx|tsx)$'; then
    echo "Running Node.js hooks..."
    npm run format
    npm run lint
fi
```

```yaml
hooks:
  pre_commit: "./scripts/pre-commit.sh"
```

## Hook Examples

### Python Project Hooks

```yaml
hooks:
  pre_commit: |
    # Format code
    black .
    isort .
    
    # Lint
    flake8 .
    mypy src/
    
    # Security check
    bandit -r src/
  
  pre_push: |
    # Full test suite
    pytest tests/ -v --cov
    pytest integration/ -v
    
    # Documentation
    mkdocs build
    
    # Package check
    python -m build
    twine check dist/*
  
  post_push: |
    # Update documentation
    mkdocs gh-deploy
    
    # Notify team
    curl -X POST "$SLACK_WEBHOOK" \
      -d "text='New version deployed to production'"
```

### Node.js Project Hooks

```yaml
hooks:
  pre_commit: |
    # Format and lint
    npm run format
    npm run lint:fix
    
    # Type check
    npm run type-check
  
  pre_push: |
    # Tests
    npm test
    npm run test:coverage
    
    # Security audit
    npm audit --audit-level moderate
    
    # Build
    npm run build
  
  post_push: |
    # Deploy to staging
    npm run deploy:staging
    
    # Update storybook
    npm run build-storybook
    npm run deploy-storybook
```

### Rust Project Hooks

```yaml
hooks:
  pre_commit: |
    # Format
    cargo fmt
    
    # Lint
    cargo clippy -- -D warnings
  
  pre_push: |
    # Test all features
    cargo test --all-features
    
    # Documentation
    cargo doc --no-deps
    
    # Security audit
    cargo audit
  
  post_push: |
    # Publish docs
    cargo doc --no-deps
    gh-pages --no-jekyll --dir target/doc
```

### Full-Stack Application

```yaml
hooks:
  pre_commit: |
    # Backend
    cd backend && black . && isort .
    cd backend && mypy src/
    
    # Frontend
    cd frontend && npm run format
    cd frontend && npm run lint:fix
    
    # Database migrations
    cd backend && alembic check
  
  pre_push: |
    # Backend tests
    cd backend && pytest tests/ -v
    
    # Frontend tests
    cd frontend && npm test
    cd frontend && npm run test:e2e
    
    # Integration tests
    docker-compose -f docker-compose.test.yml up --abort-on-container-exit
    docker-compose -f docker-compose.test.yml down
  
  post_push: |
    # Deploy to staging
    ./scripts/deploy-staging.sh
    
    # Run smoke tests
    ./scripts/smoke-tests.sh staging
    
    # Notify
    ./scripts/notify-deployment.sh staging
```

## Advanced Hook Patterns

### Using Environment Variables

```yaml
hooks:
  pre_push: |
    if [ "$ENVIRONMENT" = "production" ]; then
      pytest tests/ -v --cov
      npm audit --audit-level high
    else
      pytest tests/ -v
    fi
  
  post_push: |
    curl -X POST "$SLACK_WEBHOOK" \
      -d "text='Deployed to $ENVIRONMENT'"
```

### Hook Scripts

Create reusable hook scripts:

```bash
#!/bin/bash
# scripts/format-code.sh

set -e

echo "Formatting code..."

# Python
if command -v black &> /dev/null; then
    echo "Formatting Python files..."
    black .
fi

if command -v isort &> /dev/null; then
    echo "Sorting imports..."
    isort .
fi

# JavaScript/TypeScript
if [ -f "package.json" ]; then
    if npm run | grep -q "format"; then
        echo "Formatting JS/TS files..."
        npm run format
    fi
fi

# Rust
if [ -f "Cargo.toml" ]; then
    echo "Formatting Rust files..."
    cargo fmt
fi

echo "Code formatted successfully!"
```

```yaml
hooks:
  pre_commit: "./scripts/format-code.sh"
```

### Parallel Execution

```bash
#!/bin/bash
# scripts/parallel-tests.sh

# Run tests in parallel
pytest tests/unit/ &
PID1=$!

npm test &
PID2=$!

cargo test &
PID3=$!

# Wait for all
wait $PID1
EXIT1=$?

wait $PID2
EXIT2=$?

wait $PID3
EXIT3=$?

# Check results
if [ $EXIT1 -ne 0 ] || [ $EXIT2 -ne 0 ] || [ $EXIT3 -ne 0 ]; then
    echo "Some tests failed!"
    exit 1
fi
```

### Time-based Hooks

```bash
#!/bin/bash
# scripts/smart-hooks.sh

HOUR=$(date +%H)

# During business hours (9-17), run full checks
if [ $HOUR -ge 9 ] && [ $HOUR -le 17 ]; then
    echo "Business hours - running full checks..."
    pytest tests/ -v --cov
    npm audit
else
    echo "After hours - running basic checks..."
    pytest tests/ -v
fi
```

### Hook Success/Failure Handling

```bash
#!/bin/bash
# scripts/robust-pre-push.sh

set -e  # Exit on any error

echo "Running pre-push checks..."

# Test with coverage
if pytest tests/ --cov; then
    echo "✓ Tests passed"
else
    echo "✗ Tests failed"
    exit 1
fi

# Security check (non-blocking)
if npm audit; then
    echo "✓ No security issues"
else
    echo "⚠ Security issues found (continuing)"
fi

# Build check
if npm run build; then
    echo "✓ Build successful"
else
    echo "✗ Build failed"
    exit 1
fi

echo "All checks passed!"
```

## Integration with Tools

### Pre-commit Framework

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

```yaml
# goal.yaml
hooks:
  pre_commit: "pre-commit run --all-files"
```

### Husky (Node.js)

```bash
# Install Husky
npm install --save-dev husky

# Enable Git hooks
npx husky install

# Add pre-commit hook
npx husky add .husky/pre-commit "npm run format && npm run lint"
```

```yaml
# goal.yaml
hooks:
  pre_commit: "npx husky run pre-commit"
```

### Lefthook

```yaml
# lefthook.yml
pre-commit:
  commands:
    format:
      run: "black . && isort ."
    lint:
      run: "flake8 ."
```

```yaml
# goal.yaml
hooks:
  pre_commit: "lefthook run pre-commit"
```

## Best Practices

1. **Keep hooks fast** - Pre-commit hooks should be quick
2. **Fail fast** - Use `set -e` to exit on first error
3. **Provide feedback** - Echo what hooks are doing
4. **Use absolute paths** - Avoid PATH issues in CI
5. **Test hooks** - Ensure they work in different environments
6. **Document hooks** - Explain what each hook does

## Troubleshooting

### Hook Not Running

```bash
# Check if hook is executable
chmod +x scripts/my-hook.sh

# Check permissions
ls -la scripts/
```

### Hook Fails Silently

```bash
# Add debug output
#!/bin/bash
set -ex  # Exit on error, print commands

echo "Starting hook..."
# Your commands here
echo "Hook completed!"
```

### PATH Issues

```bash
# Use full paths
hooks:
  pre_commit: "/usr/local/bin/black ."
  
# Or activate virtualenv
hooks:
  pre_commit: "source venv/bin/activate && black ."
```

### Git Hooks Conflict

Goal hooks don't interfere with Git hooks, but you can use them together:

```yaml
# Use Goal to run Git hooks
hooks:
  pre_commit: ".git/hooks/pre-commit"
```

## Security Considerations

1. **Don't store secrets** in hook scripts
2. **Use environment variables** for sensitive data
3. **Validate inputs** in custom hook scripts
4. **Review hooks** before committing to shared repos
5. **Use HTTPS** for external calls in hooks

## Examples Repository

See [github.com/wronai/goal-hook-examples](https://github.com/wronai/goal-hook-examples) for complete hook configurations for various project types.

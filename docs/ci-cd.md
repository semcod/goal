# CI/CD Integration

Goal is designed to work seamlessly in CI/CD pipelines for automated releases.

# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      bump:
        description: 'Version bump type'
        required: true
        default: 'patch'
        type: choice
        options:
          - patch
          - minor
          - major

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Goal
        run: pip install goal
      
      - name: Configure Git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
      
      - name: Release
        env:
          PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: |
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            goal --all --bump ${{ github.event.inputs.bump }}
          else
            goal --all --bump patch
          fi
      
      - name: Upload Release Notes
        uses: actions/upload-artifact@v3
        with:
          name: release-notes
          path: release-*.md
```

# .github/workflows/pipeline.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest
      
      - name: Run tests
        run: pytest
  
  release:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: write
      packages: write
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Goal
        run: pip install goal
      
      - name: Configure Git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
      
      - name: Release
        env:
          PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: goal --all --bump patch
```

# .gitlab-ci.yml
stages:
  - test
  - release

variables:
  PYTHON_VERSION: "3.11"

test:
  stage: test
  image: python:$PYTHON_VERSION
  script:
    - pip install -e .
    - pip install pytest
    - pytest

release:
  stage: release
  image: python:$PYTHON_VERSION
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  variables:
    PYPI_TOKEN: $PYPI_TOKEN
  script:
    - pip install goal
    - git config --global user.email "gitlab-ci@gitlab.com"
    - git config --global user.name "GitLab CI"
    - goal --all --bump patch
  artifacts:
    reports:
      junit: test-results.xml
    paths:
      - release-*.md
```

# .gitlab-ci.yml
stages:
  - test
  - build
  - release-staging
  - release-production

test:
  stage: test
  script:
    - pytest

build:
  stage: build
  script:
    - python -m build
  artifacts:
    paths:
      - dist/*

release-staging:
  stage: release-staging
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"
  script:
    - goal -c .goal/staging.yaml --all --bump minor

release-production:
  stage: release-production
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - goal -c .goal/production.yaml --all --bump patch
```

### Declarative Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        PYPI_TOKEN = credentials('pypi-token')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python') {
            steps {
                sh 'python${PYTHON_VERSION} -m venv venv'
                sh '. venv/bin/activate && pip install --upgrade pip'
            }
        }
        
        stage('Install') {
            steps {
                sh '. venv/bin/activate && pip install -e .'
                sh '. venv/bin/activate && pip install goal pytest'
            }
        }
        
        stage('Test') {
            steps {
                sh '. venv/bin/activate && pytest'
            }
        }
        
        stage('Release') {
            when {
                branch 'main'
            }
            steps {
                sh '. venv/bin/activate && goal --all --bump patch'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'release-*.md', fingerprint: true
                }
            }
        }
    }
}
```

# azure-pipelines.yml
trigger:
  branches:
    include:
      - main

variables:
  pythonVersion: '3.11'

stages:
- stage: Test
  jobs:
  - job: Test
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
      displayName: 'Use Python $(pythonVersion)'
    
    - script: |
        pip install -e .
        pip install pytest
      displayName: 'Install dependencies'
    
    - script: pytest
      displayName: 'Run tests'

- stage: Release
  dependsOn: Test
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  jobs:
  - job: Release
    pool:
      vmImage: 'ubuntu-latest'
    variables:
    - group: release-secrets  # Contains PYPI_TOKEN
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
    
    - script: pip install goal
      displayName: 'Install Goal'
    
    - script: |
        git config user.email "azure-devops@microsoft.com"
        git config user.name "Azure DevOps"
        goal --all --bump patch
      env:
        PYPI_TOKEN: $(PYPI_TOKEN)
      displayName: 'Release with Goal'
```

# Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
COPY . .

# Install build dependencies
RUN pip install --no-cache-dir -e .[dev]

# Release stage
FROM python:3.11-slim as release

WORKDIR /app

# Install Goal only
RUN pip install goal

# Copy built package
COPY --from=builder /app/dist ./dist

# Set up credentials from environment
ARG PYPI_TOKEN
ENV PYPI_TOKEN=${PYPI_TOKEN}

# Release
CMD ["goal", "--all", "--bump", "patch"]
```

# docker-compose.yml
version: '3.8'

services:
  test:
    build: .
    command: pytest
    volumes:
      - .:/app
  
  release:
    build: .
    command: goal --all --bump patch
    environment:
      PYPI_TOKEN: ${PYPI_TOKEN}
    volumes:
      - .:/app
      - git-config:/root/.git
    depends_on:
      - test

volumes:
  git-config:
```

### Environment-Specific Configs

Create separate configs for different environments:

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
    prefix: "v"
  changelog:
    enabled: true

hooks:
  pre_push: "pytest tests/ -x"
  post_push: "npm run deploy:prod"

registries:
  pypi:
    token_env: "PYPI_TOKEN"
```

```yaml
# .goal/staging.yaml
versioning:
  strategy: "calver"
  
git:
  tag:
    prefix: "staging-"
  changelog:
    enabled: false
    
hooks:
  pre_push: "pytest tests/"
  post_push: "npm run deploy:staging"
```

# Production
goal -c .goal/production.yaml --all

# Staging
goal -c .goal/staging.yaml --all --bump minor

# Custom config
goal -c ci-config.yaml --yes
```

# GitHub Actions - use secrets
env:
  PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
  NPM_TOKEN: ${{ secrets.NPM_TOKEN }}

# GitLab CI - use protected variables
variables:
  PYPI_TOKEN: $PYPI_TOKEN

# Jenkins - use credentials
environment {
    PYPI_TOKEN = credentials('pypi-token')
}
```

# Only release on main branch
- if: github.ref == 'refs/heads/main'
  run: goal --all

# Or with manual approval
- name: Request release approval
  uses: trstringer/manual-approval@v1
  with:
    secret: ${{ github.TOKEN }}
    
- name: Release
  if: needs.approval.result == 'approved'
  run: goal --all
```

# Auto-detect bump type based on changes
- name: Determine bump type
  id: bump
  run: |
    if git log --oneline -1 | grep -q "BREAKING"; then
      echo "::set-output name=type::major"
    elif git log --oneline -1 | grep -q "feat"; then
      echo "::set-output name=type::minor"
    else
      echo "::set-output name=type::patch"
    fi

- name: Release
  run: goal --all --bump ${{ steps.bump.outputs.type }}
```

# rollback.sh
NEW_VERSION=$1
PREVIOUS_VERSION=$2

# Create rollback tag
git tag -a "rollback-$NEW_VERSION" -m "Rollback $NEW_VERSION to $PREVIOUS_VERSION"
git push origin "rollback-$NEW_VERSION"

# Use Goal to document rollback
goal config set git.tag.prefix "rollback-"
goal push -m "chore: rollback $NEW_VERSION to $PREVIOUS_VERSION" --no-version-sync
```

# Slack notification after release
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: |
      🚀 Released version ${{ steps.release.outputs.version }}
      
      Changes: ${{ steps.release.outputs.changelog }}
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
  if: always()
```

### Common Issues

1. **Git authentication failures**
   ```bash
   # Configure git in CI
   git config user.email "ci@bot.com"
   git config user.name "CI Bot"
   # Or use token-based auth
   git remote set-url origin https://token@github.com/user/repo.git
   ```

2. **Tests failing in CI**
   ```yaml
   # Skip tests for documentation-only changes
   - name: Check if docs only
     id: docs
     run: |
       if git diff --name-only HEAD~1 | grep -E '\.(md|rst)$'; then
         echo "::set-output name=only::true"
       fi
   
   - name: Release
     run: goal --all ${{ steps.docs.outputs.only == 'true' && '--no-test' || '' }}
   ```

3. **Version conflicts**
   ```bash
   # Force version sync
   goal config set versioning.strategy "semver"
   goal push --yes --bump patch
   ```

## Examples Repository

See [github.com/wronai/goal-examples](https://github.com/wronai/goal-examples) for complete CI/CD configurations for various platforms.

## Pyqual Quality Pipeline

Goal używa **pyqual** do automatycznego zarządzania jakością kodu z iteracyjnym pipeline.

### Konfiguracja (`pyqual.yaml`)

```yaml
pipeline:
  name: quality-loop-with-llx

  metrics:
    cc_max: 20           # cyclomatic complexity per function
    critical_max: 20     # critical issues threshold
    vallm_pass_min: 50   # vallm validation pass rate (%)

  stages:
    - name: setup        # Install dependencies
    - name: test         # Run pytest with coverage
    - name: prefact      # AI refactoring (when metrics fail)
    - name: claude_fix   # Claude Code fixes (fallback)
    - name: verify       # Re-validate after fixes
    - name: report       # Generate metrics report
    - name: push         # Git push (when metrics pass)
    - name: publish      # Build package for PyPI

  loop:
    max_iterations: 3
    on_fail: report
```

# Uruchom pipeline
pyqual run --config pyqual.yaml

# Walidacja bez uruchamiania
pyqual validate --config pyqual.yaml

# Status metryk
pyqual status --config pyqual.yaml
```

# .github/workflows/quality.yml
name: Quality Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install pyqual tox
      
      - name: Run quality pipeline
        run: pyqual run --config pyqual.yaml
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

### Tox - testowanie wielu środowisk

Skonfigurowane w `pyproject.toml`:

```toml
[tool.tox]
legacy_tox_ini = """
[tox]
envlist = py38,py39,py310,py311,py312
isolated_build = true

[testenv]
deps =
    pytest>=7.0.0
    build
    twine
extras = nfo
commands = pytest {posargs}
"""
```

Uruchomienie:

```bash
# Z pokryciem
tox -e py311 -- --cov=goal
```

### Stage'y pipeline

| Stage | Opis | Warunek |
|-------|------|---------|
| `setup` | Instalacja zależności | `first_iteration` |
| `test` | Pytest + coverage | `always` |
| `prefact` | AI refactoring | `metrics_fail` |
| `claude_fix` | Claude Code CLI fix | `metrics_fail` |
| `verify` | Re-walidacja | `after_fix` |
| `push` | Git push | `metrics_pass` |
| `publish` | Build do PyPI | `metrics_pass` |
| `markdown_report` | Raport z metrykami | `always` |

### Gate'y jakości

- **CC** ≤ 20 - cyclomatic complexity na funkcję
- **Critical** ≤ 20 - krytyczne problemy
- **Vallm pass** ≥ 50% - procent poprawnych walidacji


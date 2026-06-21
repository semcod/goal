# Goal

Goal - Automated git push with enterprise-grade commit intelligence, smart conventional commit generation based on deep code analysis, and interactive release workflow management.

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `goal`
- **version**: `2.1.257`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/x-ai/grok-code-fast-1`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, testql(2), app.doql.less, pyqual.yaml, goal.yaml, .env.example, src(19 mod), project/(3 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: goal;
  version: 2.1.257;
}

dependencies {
  runtime: "click>=8.0.0, typer>=0.24, PyYAML>=6.0, clickmd>=0.1.0, costs>=0.1.21, tomlkit>=0.12.0";
  nfo: nfo>=0.2.22;
  dev: "pytest>=7.0.0, build, twine, pfix>=0.1.60, tox>=4.0.0";
}

interface[type="cli"] {
  framework: click;
}
interface[type="cli"] page[name="goal"] {
  entry: goal.cli:main;
}

interface[type="web"] {
  type: spa;
  framework: static;
}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=pip install .;
}

workflow[name="dev"] {
  trigger: manual;
  step-1: run cmd=pip install -e ".[dev]";
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=python -m pytest -q;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=python -m pip install --upgrade build twine;
  step-2: run cmd=python -m build --sdist --wheel;
}

workflow[name="publish"] {
  trigger: manual;
  step-1: run cmd=python -m twine upload dist/*;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=rm -rf dist build *.egg-info .pytest_cache __pycache__ goal/__pycache__;
}

workflow[name="push"] {
  trigger: manual;
  step-1: run cmd=if command -v goal &> /dev/null; then \;
  step-2: run cmd=goal push; \;
  step-3: run cmd=else \;
  step-4: run cmd=echo "Goal not installed. Run 'make install' first."; \;
  step-5: run cmd=fi;
}

workflow[name="docker-matrix"] {
  trigger: manual;
  step-1: run cmd=bash integration/run_docker_matrix.sh;
}

workflow[name="bump-version"] {
  trigger: manual;
  step-1: run cmd=if [ -z "$(PART)" ]; then \;
  step-2: run cmd=echo "${YELLOW}Error: PART variable not set. Usage: make bump-version PART=<major|minor|patch>${RESET}"; \;
  step-3: run cmd=exit 1; \;
  step-4: run cmd=fi;
  step-5: run cmd=echo "${YELLOW}Bumping $(PART) version...${RESET}";
  step-6: run cmd=current_version=$$(grep '^version = ' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/'); \;
  step-7: run cmd=echo "Current version: $$current_version"; \;
  step-8: run cmd=IFS='.' read -r major minor patch <<< "$$current_version"; \;
}

workflow[name="koru-gate"] {
  trigger: manual;
  step-1: run cmd=./scripts/koru_verify_ci.sh;
}

workflow[name="help"] {
  trigger: manual;
  step-1: run cmd=echo "Targets:";
  step-2: run cmd=echo "  make install  - install goal locally";
  step-3: run cmd=echo "  make dev      - install in development mode";
  step-4: run cmd=echo "  make test     - run tests";
  step-5: run cmd=echo "  make build    - build package for PyPI";
  step-6: run cmd=echo "  make publish  - build and upload to PyPI";
  step-7: run cmd=echo "  make clean    - remove build artifacts";
  step-8: run cmd=echo "  make push     - use goal to push changes";
}

workflow[name="health"] {
  trigger: manual;
  step-1: run cmd=docker compose ps;
  step-2: run cmd=docker compose exec app echo "Health check passed";
}

workflow[name="import-makefile-hint"] {
  trigger: manual;
  step-1: run cmd=echo 'Run: taskfile import Makefile to import existing targets.';
}

workflow[name="all"] {
  trigger: manual;
  step-1: run cmd=taskfile run install;
  step-2: run cmd=taskfile run lint;
  step-3: run cmd=taskfile run test;
}

workflow[name="sumd"] {
  trigger: manual;
  step-1: run cmd=echo "# $(basename $(pwd))" > SUMD.md
echo "" >> SUMD.md
echo "$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('description','Project description'))" 2>/dev/null || echo 'Project description')" >> SUMD.md
echo "" >> SUMD.md
echo "## Contents" >> SUMD.md
echo "" >> SUMD.md
echo "- [Metadata](#metadata)" >> SUMD.md
echo "- [Architecture](#architecture)" >> SUMD.md
echo "- [Dependencies](#dependencies)" >> SUMD.md
echo "- [Source Map](#source-map)" >> SUMD.md
echo "- [Intent](#intent)" >> SUMD.md
echo "" >> SUMD.md
echo "## Metadata" >> SUMD.md
echo "" >> SUMD.md
echo "- **name**: \`$(basename $(pwd))\`" >> SUMD.md
echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMD.md
echo "- **python_requires**: \`>=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d. -f1,2)\`" >> SUMD.md
echo "- **license**: $(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('license',{}).get('text','MIT'))" 2>/dev/null || echo 'MIT')" >> SUMD.md
echo "- **ecosystem**: SUMD + DOQL + testql + taskfile" >> SUMD.md
echo "- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/" >> SUMD.md
echo "" >> SUMD.md
echo "## Architecture" >> SUMD.md
echo "" >> SUMD.md
echo '```' >> SUMD.md
echo "SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)" >> SUMD.md
echo '```' >> SUMD.md
echo "" >> SUMD.md
echo "## Source Map" >> SUMD.md
echo "" >> SUMD.md
find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -not -path './__pycache__/*' -not -path './.git/*' | head -50 | sed 's|^./||' | sed 's|^|- |' >> SUMD.md
echo "Generated SUMD.md";
  step-2: run cmd=python3 -c "
import json, os, subprocess
from pathlib import Path
project_name = Path.cwd().name
py_files = list(Path('.').rglob('*.py'))
py_files = [f for f in py_files if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])]
data = {
    'project_name': project_name,
    'description': 'SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization',
    'files': [{'path': str(f), 'type': 'python'} for f in py_files[:100]]
}
with open('sumd.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Generated sumd.json')
" 2>/dev/null || echo 'Python generation failed, using fallback';
}

workflow[name="sumr"] {
  trigger: manual;
  step-1: run cmd=echo "# $(basename $(pwd)) - Summary Report" > SUMR.md
echo "" >> SUMR.md
echo "SUMR - Summary Report for project analysis" >> SUMR.md
echo "" >> SUMR.md
echo "## Contents" >> SUMR.md
echo "" >> SUMR.md
echo "- [Metadata](#metadata)" >> SUMR.md
echo "- [Quality Status](#quality-status)" >> SUMR.md
echo "- [Metrics](#metrics)" >> SUMR.md
echo "- [Refactoring Analysis](#refactoring-analysis)" >> SUMR.md
echo "- [Intent](#intent)" >> SUMR.md
echo "" >> SUMR.md
echo "## Metadata" >> SUMR.md
echo "" >> SUMR.md
echo "- **name**: \`$(basename $(pwd))\`" >> SUMR.md
echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMR.md
echo "- **generated_at**: \`$(date -Iseconds)\`" >> SUMR.md
echo "" >> SUMR.md
echo "## Quality Status" >> SUMR.md
echo "" >> SUMR.md
if [ -f pyqual.yaml ]; then
  echo "- **pyqual_config**: ✅ Present" >> SUMR.md
  echo "- **last_run**: $(stat -c %y .pyqual/pipeline.db 2>/dev/null | cut -d' ' -f1 || echo 'N/A')" >> SUMR.md
else
  echo "- **pyqual_config**: ❌ Missing" >> SUMR.md
fi
echo "" >> SUMR.md
echo "## Metrics" >> SUMR.md
echo "" >> SUMR.md
py_files=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' | wc -l)
echo "- **python_files**: $py_files" >> SUMR.md
lines=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -exec cat {} \; 2>/dev/null | wc -l)
echo "- **total_lines**: $lines" >> SUMR.md
echo "" >> SUMR.md
echo "## Refactoring Analysis" >> SUMR.md
echo "" >> SUMR.md
echo "Run \`code2llm ./ -f evolution\` for detailed refactoring queue." >> SUMR.md
echo "Generated SUMR.md";
  step-2: run cmd=python3 -c "
import json, os, subprocess
from pathlib import Path
from datetime import datetime
project_name = Path.cwd().name
py_files = len([f for f in Path('.').rglob('*.py') if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])])
data = {
    'project_name': project_name,
    'report_type': 'SUMR',
    'generated_at': datetime.now().isoformat(),
    'metrics': {
        'python_files': py_files,
        'has_pyqual_config': Path('pyqual.yaml').exists()
    }
}
with open('SUMR.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Generated SUMR.json')
" 2>/dev/null || echo 'Python generation failed, using fallback';
}

tests {
  import: testql-scenarios/**/*.testql.toon.yaml;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  template_file: .env.example;
  python_version: >=3.10;
  vars: LLM_MODEL, OPENROUTER_API_KEY;
  runtime_llm: OPENROUTER_API_KEY;
}
```

### Source Modules

- `goal.changelog`
- `goal.cli`
- `goal.cli_helpers`
- `goal.commit_generator`
- `goal.config`
- `goal.deep_analyzer`
- `goal.deep_analyzer_aggregate`
- `goal.deep_analyzer_patterns`
- `goal.dependency_update`
- `goal.enhanced_summary`
- `goal.formatter`
- `goal.git_ops`
- `goal.package_managers`
- `goal.project_bootstrap`
- `goal.project_doctor`
- `goal.smart_commit`
- `goal.toml_validation`
- `goal.user_config`
- `goal.version_validation`

## Interfaces

### CLI Entry Points

- `goal`

### testql Scenarios

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -m goal
  timeout_ms, 10000

# Test 1: CLI help command
SHELL "python -m goal --help" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "Usage:"

# Test 2: CLI version command
SHELL "python -m goal --version" 5000
ASSERT_EXIT_CODE 0

# Test 3: CLI main workflow (dry-run)
SHELL "python -m goal --help" 10000
ASSERT_EXIT_CODE 0
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Functional probes derived from pytest coverage areas
# TYPE: cli
# GENERATED: false
# CURATED: true
#
# NOTE: This file was previously auto-generated by `testql generate`, which
# inadvertently scraped `assert` statements from .venv site-packages
# (pandas, jsonschema, gitdb) and produced 52 non-executable rows. Until the
# upstream generator can scope strictly to project tests and filter non-literal
# operands, this scenario is curated by hand to exercise the same CLI surface
# that the pytest suite covers (entry points, subcommand wiring, help/version
# contract). See STARTER-013.

CONFIG[2]{key, value}:
  cli_command, python -m goal
  timeout_ms, 10000

# Probe 1: top-level help advertises the package name and usage
SHELL "python -m goal --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "Usage:"
ASSERT_STDOUT_CONTAINS "Goal"

# Probe 2: --version prints semver-style "goal, version X.Y.Z"
SHELL "python -m goal --version" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "goal, version"

# Probe 3: doctor subcommand is wired and self-documenting
SHELL "python -m goal doctor --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "Diagnose"

# Probe 4: commit subcommand is wired (smart commit generator entry point)
SHELL "python -m goal commit --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "smart commit"

# Probe 5: bootstrap subcommand exposes project bootstrap workflow
SHELL "python -m goal bootstrap --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "Bootstrap"

# Probe 6: authors subcommand group is wired
SHELL "python -m goal authors --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "authors"

# Probe 7: config subcommand group is wired
SHELL "python -m goal config --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "configuration"

# Probe 8: hooks subcommand group is wired
SHELL "python -m goal hooks --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "hooks"

# Probe 9: clone subcommand accepts a URL argument
SHELL "python -m goal clone --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "URL"

# Probe 10: fix-summary subcommand is wired
SHELL "python -m goal fix-summary --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "summary"

# Probe 11: check-versions subcommand reports version drift
SHELL "python -m goal check-versions --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "version"

# Probe 12: doctor on this repo runs end-to-end without crashing
# (uses --help variant to keep the scenario hermetic — runtime diagnostics
# require a writable cwd which the runner does not always provide)
SHELL "python -m goal doctor --help" 8000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "Options"
```

## Workflows

### Taskfile Tasks (`Taskfile.yml`)

```yaml markpact:taskfile path=Taskfile.yml
version: '3'
name: goal
description: Minimal Taskfile
variables:
  APP_NAME: goal
environments:
  local:
    container_runtime: docker
    compose_command: docker compose
pipeline:
  python_version: "3.12"
  runner_image: ubuntu-latest
  branches: [main]
  cache: [~/.cache/pip]
  artifacts: [dist/]

  stages:
    - name: lint
      tasks: [lint]

    - name: test
      tasks: [test]

    - name: build
      tasks: [build]
      when: "branch:main"

tasks:
  install:
    desc: Install Python dependencies (editable)
    cmds:
    - pip install -e .[dev]
  test:
    desc: Run pytest suite
    cmds:
    - pytest -q
  koru-gate:
    desc: Run strict Koru quality gates (fails on regix hard violations)
    cmds:
    - ./scripts/koru_verify_ci.sh
  build:
    desc: Build wheel + sdist
    cmds:
    - python -m build
  clean:
    desc: Remove build artefacts
    cmds:
    - rm -rf build/ dist/ *.egg-info
  help:
    desc: '[imported from Makefile] help'
    cmds:
    - echo "Targets:"
    - echo "  make install  - install goal locally"
    - echo "  make dev      - install in development mode"
    - echo "  make test     - run tests"
    - echo "  make build    - build package for PyPI"
    - echo "  make publish  - build and upload to PyPI"
    - echo "  make clean    - remove build artifacts"
    - echo "  make push     - use goal to push changes"
  dev:
    desc: '[imported from Makefile] dev'
    cmds:
    - pip install -e ".[dev]"
  publish:
    desc: '[imported from Makefile] publish'
    cmds:
    - python -m twine upload dist/*
    deps:
    - bump-version
    - build
  push:
    desc: '[imported from Makefile] push'
    cmds:
    - if command -v goal &> /dev/null; then \
    - goal push; \
    - else \
    - echo "Goal not installed. Run 'make install' first."; \
    - fi
    deps:
    - bump-version
  docker-matrix:
    desc: '[imported from Makefile] docker-matrix'
    cmds:
    - bash integration/run_docker_matrix.sh
  bump-version:
    desc: '[imported from Makefile] bump-version'
    cmds:
    - if [ -z "$(PART)" ]; then \
    - 'echo "${YELLOW}Error: PART variable not set. Usage: make bump-version PART=<major|minor|patch>${RESET}";
      \'
    - exit 1; \
    - fi
    - echo "${YELLOW}Bumping $(PART) version...${RESET}"
    - current_version=$$(grep '^version = ' pyproject.toml | head -1 | sed 's/version
      = "\(.*\)"/\1/'); \
    - 'echo "Current version: $$current_version"; \'
    - IFS='.' read -r major minor patch <<< "$$current_version"; \
    - case "$(PART)" in \
    - major) major=$$((major + 1)); minor=0; patch=0 ;; \
    - minor) minor=$$((minor + 1)); patch=0 ;; \
    - patch) patch=$$((patch + 1)) ;; \
    - '*) echo "${YELLOW}Error: PART must be major, minor, or patch${RESET}"; exit
      1 ;; \'
    - esac; \
    - new_version="$${major}.$${minor}.$${patch}"; \
    - sed -i "s/^version = \"$$current_version\"/version = \"$$new_version\"/" pyproject.toml;
      \
    - echo "${GREEN}Version bumped to $$new_version${RESET}"; \
    - git add pyproject.toml; \
    - git commit -m "Bump version to $$new_version"; \
    - if git rev-parse "v$$new_version" >/dev/null 2>&1; then \
    - 'echo "${YELLOW}Error: tag ''v$$new_version'' already exists${RESET}"; \'
    - exit 1; \
    - fi; \
    - git tag -a "v$$new_version" -m "Version $$new_version"; \
    - echo "${GREEN}Created tag v$$new_version${RESET}"
  health:
    desc: '[from doql] workflow: health'
    cmds:
    - docker compose ps
    - docker compose exec app echo "Health check passed"
  import-makefile-hint:
    desc: '[from doql] workflow: import-makefile-hint'
    cmds:
    - 'echo ''Run: taskfile import Makefile to import existing targets.'''
  all:
    desc: Run install, lint, test
    cmds:
    - taskfile run install
    - taskfile run lint
    - taskfile run test
  sumd:
    desc: Generate SUMD (Structured Unified Markdown Descriptor) for AI-aware project description
    cmds:
    - |
      echo "# $(basename $(pwd))" > SUMD.md
      echo "" >> SUMD.md
      echo "$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('description','Project description'))" 2>/dev/null || echo 'Project description')" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Contents" >> SUMD.md
      echo "" >> SUMD.md
      echo "- [Metadata](#metadata)" >> SUMD.md
      echo "- [Architecture](#architecture)" >> SUMD.md
      echo "- [Dependencies](#dependencies)" >> SUMD.md
      echo "- [Source Map](#source-map)" >> SUMD.md
      echo "- [Intent](#intent)" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Metadata" >> SUMD.md
      echo "" >> SUMD.md
      echo "- **name**: \`$(basename $(pwd))\`" >> SUMD.md
      echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMD.md
      echo "- **python_requires**: \`>=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d. -f1,2)\`" >> SUMD.md
      echo "- **license**: $(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('license',{}).get('text','MIT'))" 2>/dev/null || echo 'MIT')" >> SUMD.md
      echo "- **ecosystem**: SUMD + DOQL + testql + taskfile" >> SUMD.md
      echo "- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Architecture" >> SUMD.md
      echo "" >> SUMD.md
      echo '```' >> SUMD.md
      echo "SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)" >> SUMD.md
      echo '```' >> SUMD.md
      echo "" >> SUMD.md
      echo "## Source Map" >> SUMD.md
      echo "" >> SUMD.md
      find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -not -path './__pycache__/*' -not -path './.git/*' | head -50 | sed 's|^./||' | sed 's|^|- |' >> SUMD.md
      echo "Generated SUMD.md"
    - |
      python3 -c "
      import json, os, subprocess
      from pathlib import Path
      project_name = Path.cwd().name
      py_files = list(Path('.').rglob('*.py'))
      py_files = [f for f in py_files if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])]
      data = {
          'project_name': project_name,
          'description': 'SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization',
          'files': [{'path': str(f), 'type': 'python'} for f in py_files[:100]]
      }
      with open('sumd.json', 'w') as f:
          json.dump(data, f, indent=2)
      print('Generated sumd.json')
      " 2>/dev/null || echo 'Python generation failed, using fallback'
  sumr:
    desc: Generate SUMR (Summary Report) with project metrics and health status
    cmds:
    - |
      echo "# $(basename $(pwd)) - Summary Report" > SUMR.md
      echo "" >> SUMR.md
      echo "SUMR - Summary Report for project analysis" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Contents" >> SUMR.md
      echo "" >> SUMR.md
      echo "- [Metadata](#metadata)" >> SUMR.md
      echo "- [Quality Status](#quality-status)" >> SUMR.md
      echo "- [Metrics](#metrics)" >> SUMR.md
      echo "- [Refactoring Analysis](#refactoring-analysis)" >> SUMR.md
      echo "- [Intent](#intent)" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Metadata" >> SUMR.md
      echo "" >> SUMR.md
      echo "- **name**: \`$(basename $(pwd))\`" >> SUMR.md
      echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMR.md
      echo "- **generated_at**: \`$(date -Iseconds)\`" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Quality Status" >> SUMR.md
      echo "" >> SUMR.md
      if [ -f pyqual.yaml ]; then
        echo "- **pyqual_config**: ✅ Present" >> SUMR.md
        echo "- **last_run**: $(stat -c %y .pyqual/pipeline.db 2>/dev/null | cut -d' ' -f1 || echo 'N/A')" >> SUMR.md
      else
        echo "- **pyqual_config**: ❌ Missing" >> SUMR.md
      fi
      echo "" >> SUMR.md
      echo "## Metrics" >> SUMR.md
      echo "" >> SUMR.md
      py_files=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' | wc -l)
      echo "- **python_files**: $py_files" >> SUMR.md
      lines=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -exec cat {} \; 2>/dev/null | wc -l)
      echo "- **total_lines**: $lines" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Refactoring Analysis" >> SUMR.md
      echo "" >> SUMR.md
      echo "Run \`code2llm ./ -f evolution\` for detailed refactoring queue." >> SUMR.md
      echo "Generated SUMR.md"
    - |
      python3 -c "
      import json, os, subprocess
      from pathlib import Path
      from datetime import datetime
      project_name = Path.cwd().name
      py_files = len([f for f in Path('.').rglob('*.py') if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])])
      data = {
          'project_name': project_name,
          'report_type': 'SUMR',
          'generated_at': datetime.now().isoformat(),
          'metrics': {
              'python_files': py_files,
              'has_pyqual_config': Path('pyqual.yaml').exists()
          }
      }
      with open('SUMR.json', 'w') as f:
          json.dump(data, f, indent=2)
      print('Generated SUMR.json')
      " 2>/dev/null || echo 'Python generation failed, using fallback'
```

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
pipeline:
  name: quality-loop-with-llx

  # Quality gates — pipeline iterates until ALL pass
  metrics:
    cc_max: 20           # cyclomatic complexity per function
    critical_max: 18     # Phase 2-3 done; lowered from 20 (current: 17)
    vallm_pass_min: 50   # obecny poziom: 56.6%
    # coverage_min: 30   # pyqual nie wspiera pytest-cov (zawsze null)
    # Security gates (uncomment to enable):
    # vuln_high_max: 0     # pip-audit high severity CVEs
    # bandit_high_max: 0   # bandit high severity issues
    # secrets_found_max: 0 # trufflehog/gitleaks secrets

  # Pipeline stages — use 'tool:' for built-in presets or 'run:' for custom
  stages:
    # Verify/install all tool dependencies before pipeline starts
    - name: setup
      run: |
        set -e
        echo "=== pyqual dependency check ==="
        # Python tools (pip)
        for pkg in code2llm vallm prefact llx pytest-cov goal; do
          if python -m pip show "$pkg" >/dev/null 2>&1; then
            echo "  ✓ $pkg"
          else
            echo "  ✗ $pkg — installing…"
            pip install -q "$pkg" || echo "  ⚠ $pkg install failed (optional)"
          fi
        done
        # Node tools (claude)
        if command -v claude >/dev/null 2>&1; then
          echo "  ✓ claude $(claude --version 2>/dev/null)"
        else
          echo "  ✗ claude — installing…"
          npm install -g --prefix="$HOME/.local" @anthropic-ai/claude-code 2>/dev/null \
            && echo "  ✓ claude installed" \
            || echo "  ⚠ claude install failed (fix stage will use llx fallback)"
        fi
        # Claude Code auth can be either:
        # - local OAuth session via `claude auth login` 
        # - ANTHROPIC_API_KEY in CI/GitHub Actions
        # We only verify the CLI is available here.
        echo "=== setup done ==="
      when: first_iteration
      timeout: 300

    # - name: analyze
    #   tool: code2llm
    #   when: first_iteration

    # - name: validate
    #   run: vallm batch pyqual tests --recursive --format toon --output ./project
    #   when: always

    # Security scans (uncomment to enable):
    # - name: audit
    #   tool: pip-audit
    #   optional: true
    # - name: bandit
    #   tool: bandit
    #   optional: true

    - name: test
      run: python3 -m pytest -q --cov=goal --cov-report=term-missing --cov-fail-under=30
      optional: true

    - name: prefact
      tool: prefact
      optional: true
      when: metrics_fail
      timeout: 900

    # Claude Code fix - uproszczona wersja bez heredoc
    - name: claude_fix
      run: |
        export PATH="$HOME/.local/bin:$PATH"
        if ! command -v claude >/dev/null 2>&1; then
          echo "Claude nie zainstalowany, pominięto"
          exit 0
        fi
        if [ -f TODO.md ] && [ -s TODO.md ]; then
          echo "Uruchamianie Claude z TODO.md..."
          timeout 900 claude -p "Fix these issues: $(head -50 TODO.md)" \
            --model sonnet --allowedTools "Edit,Read,Write,Bash(git diff)" \
            --output-format text || echo "Claude fix nie powiódł się"
        else
          echo "Brak TODO.md do przetworzenia"
        fi
      when: metrics_fail
      timeout: 1200

    # LLX fallback (uncomment if Claude Code unavailable)
    # - name: fix
    #   tool: llx-fix
    #   when: metrics_fail
    #   timeout: 1800

    - name: verify
      run: vallm batch pyqual tests --recursive --format toon --output ./project
      optional: true
      when: after_fix
      timeout: 300

    # Generate metrics report (YAML) and update README.md badges
    - name: report
      tool: report
      when: metrics_pass
      optional: true

    # Continuous improvement: process TODO.md items when all gates pass
    # Uses parallel execution with multiple tools (Claude Code + llx)
    - name: todo_fix
      run: python3 -m pyqual.run_parallel_fix
      when: metrics_pass
      optional: true
      timeout: 1800

    # Simple git push (goal push had "Argument list too long" issue with many files)
    - name: push
      run: |
        if [ -n "$(git status --porcelain)" ]; then
          git add -A
          git commit -m "chore: pyqual auto-commit [skip ci]" 2>/dev/null || true
          git push origin HEAD
        else
          echo "No changes to push"
        fi
      when: metrics_pass
      optional: true
      timeout: 120

    # Publish - tylko build, bez upload (wymaga credentials)
    # Użyj: twine upload dist/* --username __token__ --password $PYPI_TOKEN
    - name: publish
      run: |
        echo "=== Building package for PyPI ==="
        make build
        echo "=== Package built in dist/ ==="
        echo "To publish: twine upload dist/* --username __token__ --password \$PYPI_TOKEN"
      when: metrics_pass
      optional: true
      timeout: 300

    # Generate comprehensive markdown report with Mermaid diagram and ASCII flow
    - name: markdown_report
      run: python3 -m pyqual.report_generator
      when: always
      optional: true
      timeout: 30

  # Loop behavior
  loop:
    max_iterations: 3
    on_fail: report      # report | create_ticket | block

  # Environment (optional)
  env:
    LLM_MODEL: openrouter/x-ai/grok-code-fast-1
    LLX_DEFAULT_TIER: balanced
    LLX_VERBOSE: true
```

## Configuration

```yaml
project:
  name: goal
  version: 2.1.257
  env: local
```

## Dependencies

### Runtime

```text markpact:deps python
click>=8.0.0
typer>=0.24
PyYAML>=6.0
clickmd>=0.1.0
costs>=0.1.21
tomlkit>=0.12.0
```

### Development

```text markpact:deps python scope=dev
pytest>=7.0.0
build
twine
pfix>=0.1.60
tox>=4.0.0
```

## Deployment

```bash markpact:run
pip install goal

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | OpenRouter API Key (required for real cost calculation) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Default AI model for cost analysis |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`goal`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `goal/__init__.py:__version__`

## Makefile Targets

- `SHELL`
- `GREEN` — Define colors for better output
- `YELLOW`
- `WHITE`
- `RESET`
- `help`
- `install`
- `dev`
- `test`
- `build`
- `publish`
- `clean`
- `push`
- `docker-matrix`
- `bump-version` — Bump version (e.g., make bump-version PART=patch)

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# goal | 201f 37110L | python:192,shell:7,less:1,go:1 | 2026-06-20
# stats: 720 func | 139 cls | 201 mod | CC̄=4.6 | critical:66 | cycles:0
# alerts[5]: CC _run_publish_command=33; CC output_final_summary=29; CC add_slow_test_tickets_to_planfile=22; CC _select_managers_to_update=21; CC execute_push_workflow=20
# hotspots[5]: execute_push_workflow fan=34; doctor fan=20; _install_python_deps_legacy fan=18; _install_python_deps fan=17; update_cost_badges fan=17
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[201]:
  app.doql.less,249
  examples/api-usage/01_basic_api.py,75
  examples/api-usage/02_git_operations.py,101
  examples/api-usage/03_commit_generation.py,71
  examples/api-usage/04_version_validation.py,80
  examples/api-usage/05_programmatic_workflow.py,121
  examples/api-usage/test_integration.py,250
  examples/custom-hooks/post-commit.py,145
  examples/custom-hooks/pre-commit.py,129
  examples/custom-hooks/pre-publish.py,168
  examples/git-hooks/install.sh,32
  examples/go-project/main.go,11
  examples/markdown-demo.sh,71
  examples/my-new-project/src/my-new-project/__init__.py,4
  examples/my-new-project/tests/test_my-new-project.py,3
  examples/template-generator/generate.py,241
  examples/testing/03_advanced_mocking.py,284
  examples/testing/04_debugging_diagnostics.py,302
  examples/validation/run_all_validation.py,121
  examples/validation/test_api_signatures.py,290
  examples/validation/test_imports.py,207
  examples/validation/test_readme_consistency.py,295
  examples/validation/test_syntax_check.py,212
  examples/webhooks/discord-webhook.py,110
  examples/webhooks/slack-webhook.py,117
  goal/__init__.py,4
  goal/__main__.py,19
  goal/authors/__init__.py,20
  goal/authors/manager.py,349
  goal/authors/utils.py,218
  goal/bootstrap/__init__.py,12
  goal/bootstrap/configurator.py,143
  goal/bootstrap/costs_badge.py,246
  goal/bootstrap/detector.py,150
  goal/bootstrap/installer.py,392
  goal/bootstrap/pyproject_costs_setup.py,235
  goal/bootstrap/templates.py,195
  goal/changelog.py,130
  goal/cli/__init__.py,474
  goal/cli/authors_cmd.py,128
  goal/cli/commit_cmd.py,229
  goal/cli/config_cmd.py,126
  goal/cli/config_validate_cmd.py,48
  goal/cli/doctor_cmd.py,126
  goal/cli/hooks_cmd.py,88
  goal/cli/license_cmd.py,207
  goal/cli/postcommit_cmd.py,83
  goal/cli/publish.py,619
  goal/cli/publish_cmd.py,67
  goal/cli/push_cmd.py,154
  goal/cli/recover_cmd.py,133
  goal/cli/tests.py,518
  goal/cli/tests_discovery.py,108
  goal/cli/tests_pytest_setup.py,132
  goal/cli/utils_cmd.py,230
  goal/cli/validation_cmd.py,86
  goal/cli/version.py,36
  goal/cli/version_sync.py,333
  goal/cli/version_types.py,136
  goal/cli/version_utils.py,486
  goal/cli/wizard_cmd.py,368
  goal/cli.py,17
  goal/cli_helpers.py,98
  goal/commit_generator.py,36
  goal/config/__init__.py,37
  goal/config/constants.py,481
  goal/config/manager.py,551
  goal/config/validation.py,557
  goal/config.py,25
  goal/deep_analyzer.py,305
  goal/deep_analyzer_aggregate.py,281
  goal/deep_analyzer_patterns.py,64
  goal/dependency_update.py,341
  goal/doctor/__init__.py,56
  goal/doctor/core.py,94
  goal/doctor/dotnet.py,32
  goal/doctor/go.py,42
  goal/doctor/java.py,40
  goal/doctor/logging.py,30
  goal/doctor/models.py,48
  goal/doctor/nodejs.py,92
  goal/doctor/php.py,55
  goal/doctor/python.py,45
  goal/doctor/python_diag_core.py,339
  goal/doctor/python_diag_extended.py,394
  goal/doctor/ruby.py,29
  goal/doctor/rust.py,42
  goal/doctor/todo.py,145
  goal/enhanced_summary.py,24
  goal/formatter.py,519
  goal/generator/__init__.py,15
  goal/generator/analyzer.py,564
  goal/generator/generator.py,433
  goal/generator/git_ops.py,178
  goal/git_ops.py,691
  goal/hooks/__init__.py,20
  goal/hooks/config.py,107
  goal/hooks/manager.py,314
  goal/installers/__init__.py,10
  goal/installers/broker.py,159
  goal/installers/config.py,45
  goal/installers/managers/__init__.py,17
  goal/installers/managers/base.py,61
  goal/installers/managers/pdm.py,30
  goal/installers/managers/pip.py,29
  goal/installers/managers/poetry.py,33
  goal/installers/managers/uv.py,38
  goal/io/__init__.py,30
  goal/io/stdio.py,87
  goal/license/__init__.py,21
  goal/license/manager.py,588
  goal/license/spdx.py,284
  goal/package_managers.py,645
  goal/postcommit/__init__.py,28
  goal/postcommit/actions.py,240
  goal/postcommit/manager.py,212
  goal/project_bootstrap.py,1275
  goal/project_doctor.py,44
  goal/publish/__init__.py,6
  goal/publish/changes.py,239
  goal/publish/github_fallback.py,317
  goal/push/__init__.py,57
  goal/push/commands.py,77
  goal/push/core.py,899
  goal/push/stages/__init__.py,37
  goal/push/stages/changelog.py,25
  goal/push/stages/commit.py,304
  goal/push/stages/costs.py,131
  goal/push/stages/dry_run.py,152
  goal/push/stages/publish.py,128
  goal/push/stages/push_remote.py,474
  goal/push/stages/tag.py,33
  goal/push/stages/test.py,92
  goal/push/stages/todo.py,101
  goal/push/stages/version.py,57
  goal/recovery/__init__.py,49
  goal/recovery/auth.py,84
  goal/recovery/base.py,51
  goal/recovery/corrupted.py,58
  goal/recovery/divergent.py,130
  goal/recovery/exceptions.py,79
  goal/recovery/force_push.py,52
  goal/recovery/large_file.py,398
  goal/recovery/lfs.py,60
  goal/recovery/manager.py,347
  goal/recovery/strategies.py,24
  goal/smart_commit/__init__.py,15
  goal/smart_commit/abstraction.py,279
  goal/smart_commit/generator.py,16
  goal/smart_commit/generator_core.py,268
  goal/smart_commit/generator_generate.py,279
  goal/smart_commit.py,21
  goal/summary/__init__.py,43
  goal/summary/body_formatter.py,215
  goal/summary/generator.py,590
  goal/summary/quality_filter.py,390
  goal/summary/validator.py,490
  goal/toml_validation.py,118
  goal/user_config.py,324
  goal/validation/__init__.py,28
  goal/validation/manager.py,208
  goal/validation/rules.py,253
  goal/validators/__init__.py,58
  goal/validators/dot_folders.py,162
  goal/validators/exceptions.py,47
  goal/validators/file_validator.py,304
  goal/validators/gitignore.py,50
  goal/validators/tokens.py,287
  goal/version_validation.py,342
  integration/run_docker_matrix.sh,6
  integration/run_matrix.sh,217
  project.sh,48
  scripts/koru_verify_ci.sh,50
  test_recovery.py,128
  tests/conftest.py,12
  tests/test_changelog.py,137
  tests/test_cli_options.py,140
  tests/test_cli_tests_runner.py,213
  tests/test_clone_repo.py,287
  tests/test_config_shim.py,30
  tests/test_config_validation.py,160
  tests/test_dependency_update.py,495
  tests/test_detect_version_files.py,106
  tests/test_file_validation.py,254
  tests/test_formatter.py,257
  tests/test_git_ops.py,183
  tests/test_github_fallback.py,213
  tests/test_installers_e2e.py,246
  tests/test_project_bootstrap.py,806
  tests/test_project_bootstrap_costs.py,29
  tests/test_project_doctor.py,436
  tests/test_publish_changes.py,57
  tests/test_publish_pattern.py,122
  tests/test_push_e2e.py,755
  tests/test_push_todo_stage.py,52
  tests/test_smart_commit_shim.py,24
  tests/test_token_validator_patterns.py,41
  tests/test_user_config.py,105
  tests/test_version_sync.py,263
  tests/test_version_validation.py,254
  tree.sh,2
D:
  examples/api-usage/01_basic_api.py:
    e: main
    main()
  examples/api-usage/02_git_operations.py:
    e: _check_git_repository,_display_staged_files,_display_unstaged_files,_display_diff_stats,_display_diff_content,main
    _check_git_repository()
    _display_staged_files()
    _display_unstaged_files()
    _display_diff_stats()
    _display_diff_content()
    main()
  examples/api-usage/03_commit_generation.py:
    e: main
    main()
  examples/api-usage/04_version_validation.py:
    e: main
    main()
  examples/api-usage/05_programmatic_workflow.py:
    e: run_custom_workflow,create_minimal_workflow
    run_custom_workflow()
    create_minimal_workflow()
  examples/api-usage/test_integration.py:
    e: TestGoalAPIIntegration,TestCustomValidators,TestHookIntegration,TestConfiguration,TestWorkflowIntegration,ExampleGoalAPITest
    TestGoalAPIIntegration: test_bootstrap_project_detection(1),test_version_validation(0),test_commit_message_generation(0),test_git_operations(1)  # Integration tests for Goal API.
    TestCustomValidators: test_file_size_validator(1),test_secret_detection_validator(0)  # Tests for custom validators.
    TestHookIntegration: test_pre_commit_hook_execution_placeholder(1),test_validator_registration_placeholder(0)  # Tests for hook integration (placeholder - actual API may var
    TestConfiguration: test_config_loading(1),test_user_config_loading(0)  # Tests for configuration management.
    TestWorkflowIntegration: test_full_workflow_dry_run(1)  # End-to-end workflow tests.
    ExampleGoalAPITest: test_my_custom_workflow(0)  # Example showing how to test your own Goal integration.
  examples/custom-hooks/post-commit.py:
    e: get_commit_info,notify_slack,update_changelog,log_to_file,main
    get_commit_info()
    notify_slack(info)
    update_changelog(info)
    log_to_file(info)
    main()
  examples/custom-hooks/pre-commit.py:
    e: check_secrets,check_file_sizes,run_tests,main
    check_secrets()
    check_file_sizes(max_size_mb)
    run_tests()
    main()
  examples/custom-hooks/pre-publish.py:
    e: test_build,test_install,check_version,run_security_check,main
    test_build()
    test_install()
    check_version()
    run_security_check()
    main()
  examples/my-new-project/src/my-new-project/__init__.py:
  examples/my-new-project/tests/test_my-new-project.py:
    e: test_example
    test_example()
  examples/template-generator/generate.py:
    e: generate_project,main
    generate_project(template_type;project_name)
    main()
  examples/testing/03_advanced_mocking.py:
    e: test_mocking_external_services,test_mocking_git_operations,test_mocking_click_interactions,test_spies_and_call_counting,test_mocking_file_system,test_conditional_mocking,test_mock_context_manager
    test_mocking_external_services()
    test_mocking_git_operations()
    test_mocking_click_interactions()
    test_spies_and_call_counting()
    test_mocking_file_system()
    test_conditional_mocking()
    test_mock_context_manager()
  examples/testing/04_debugging_diagnostics.py:
    e: test_debug_output_capture,test_stack_trace_analysis,test_performance_timing,test_import_tracing,test_config_diagnostics,create_debug_report
    test_debug_output_capture()
    test_stack_trace_analysis()
    test_performance_timing()
    test_import_tracing()
    test_config_diagnostics()
    create_debug_report()
  examples/validation/run_all_validation.py:
    e: main,ValidationRunner
    ValidationRunner: __init__(1),run_test(2),run_all(0),print_summary(0)  # Runs all validation tests and aggregates results.
    main()
  examples/validation/test_api_signatures.py:
    e: main,APISignatureValidator
    APISignatureValidator: __init__(1),extract_function_calls(1),resolve_function(1),validate_call(3),validate_file(1),validate_all_examples(0),print_report(0)  # Validates API signatures in example files.
    main()
  examples/validation/test_imports.py:
    e: main,ImportValidator
    ImportValidator: __init__(1),extract_imports(1),validate_import(3),validate_file(1),validate_all_examples(0),print_report(0)  # Validates imports in Python files.
    main()
  examples/validation/test_readme_consistency.py:
    e: main,READMEConsistencyValidator
    READMEConsistencyValidator: __init__(1),extract_file_references(1),extract_markdown_links(1),get_actual_structure(1),validate_readme(2),extract_documented_directories(1),extract_documented_files(1),validate_all(0),print_report(0)  # Validates README consistency with actual directory structure
    main()
  examples/validation/test_syntax_check.py:
    e: main,SyntaxChecker
    SyntaxChecker: __init__(1),check_python(1),check_shell(1),check_json(1),check_yaml(1),check_file(1),check_all_examples(0),print_report(0)  # Checks syntax of various file types.
    main()
  examples/webhooks/discord-webhook.py:
    e: send_discord_notification,main
    send_discord_notification(message;commit_info)
    main()
  examples/webhooks/slack-webhook.py:
    e: send_slack_notification,main
    send_slack_notification(message;commit_info)
    main()
  goal/__init__.py:
  goal/__main__.py:
  goal/authors/__init__.py:
  goal/authors/manager.py:
    e: get_project_authors,add_project_author,AuthorsManager
    AuthorsManager: __init__(1),get_authors(0),add_author(4),remove_author(1),update_author(4),find_author(1),list_authors(0),get_current_author(0),import_from_git(0),export_to_contributors(0)  # Manages project authors and team members.
    get_project_authors(project_dir)
    add_project_author(name;email;role;alias;project_dir)
  goal/authors/utils.py:
    e: format_co_author_trailer,parse_co_authors,add_co_authors_to_message,remove_co_authors_from_message,validate_author_format,deduplicate_co_authors,get_co_authors_from_command_line,format_commit_message_with_co_authors,extract_current_author_from_config
    format_co_author_trailer(name;email)
    parse_co_authors(message)
    add_co_authors_to_message(message;co_authors)
    remove_co_authors_from_message(message)
    validate_author_format(author_str)
    deduplicate_co_authors(co_authors)
    get_co_authors_from_command_line(co_author_args)
    format_commit_message_with_co_authors(title;body;co_authors)
    extract_current_author_from_config()
  goal/bootstrap/__init__.py:
  goal/bootstrap/configurator.py:
    e: scaffold_test_file,_find_python_bin,_read_openrouter_api_key,_find_openrouter_api_key,_find_git_root
    scaffold_test_file(project_dir;project_type)
    _find_python_bin(project_dir)
    _read_openrouter_api_key(env_file)
    _find_openrouter_api_key(project_dir)
    _find_git_root(project_dir)
  goal/bootstrap/costs_badge.py:
    e: _install_costs_package,_load_costs_api,_commit_blob_lower,_filter_ai_commits,_parsed_diff_is_usable,_fetch_commit_diff,_single_commit_ai_cost,_calculate_ai_costs,_read_model_from_pyproject,_generate_costs_badge
    _install_costs_package(project_dir;python_bin)
    _load_costs_api()
    _commit_blob_lower(commit_obj;parsed_tail)
    _filter_ai_commits(all_commits_data;indicators)
    _parsed_diff_is_usable(parsed_diff)
    _fetch_commit_diff(repo_root;commit_obj;parsed_diff;get_commit_diff)
    _single_commit_ai_cost(repo_root;commit_obj;parsed_diff;get_commit_diff;ai_cost)
    _calculate_ai_costs(repo_root)
    _read_model_from_pyproject(project_dir)
    _generate_costs_badge(project_dir)
  goal/bootstrap/detector.py:
    e: _match_marker,detect_project_types_deep,_python_package_dir_exists,_guess_python_name,_python_scaffold_import_name,_guess_nodejs_name,_guess_rust_name,_guess_go_name,guess_package_name
    _match_marker(base;pattern)
    detect_project_types_deep(root;max_depth)
    _python_package_dir_exists(project_dir;package_name)
    _guess_python_name(project_dir)
    _python_scaffold_import_name(project_dir;name)
    _guess_nodejs_name(project_dir)
    _guess_rust_name(project_dir)
    _guess_go_name(project_dir)
    guess_package_name(project_dir;project_type)
  goal/bootstrap/installer.py:
    e: _match_marker,_should_skip_install,_ensure_costs_installed,_install_python_deps_legacy,_install_python_deps_broker,_ensure_python_test_dependency,_ensure_python_env,_needs_install,_run_dep_install,_get_matching_dep_command,_ensure_generic_env,ensure_project_environment
    _match_marker(base;pattern)
    _should_skip_install(project_dir;markers)
    _ensure_costs_installed(project_dir;python_bin)
    _install_python_deps_legacy(project_dir;cfg;python_bin)
    _install_python_deps_broker(project_dir;extras)
    _ensure_python_test_dependency(project_dir;python_bin;test_dep)
    _ensure_python_env(project_dir;cfg;yes)
    _needs_install(project_dir;cfg)
    _run_dep_install(project_dir;dep_cfg)
    _get_matching_dep_command(project_dir;dep_commands)
    _ensure_generic_env(project_dir;project_type;cfg;yes)
    ensure_project_environment(project_dir;project_type;yes)
  goal/bootstrap/pyproject_costs_setup.py:
    e: _find_dep_list_end,_try_merge_optional_dev_deps,_try_merge_hatch_default_deps,_try_add_deps,_add_deps_to_section_match,_ensure_costs_config,_ensure_env_template
    _find_dep_list_end(content;start_idx)
    _try_merge_optional_dev_deps(content)
    _try_merge_hatch_default_deps(content)
    _try_add_deps(content)
    _add_deps_to_section_match(section_start;existing;required_deps)
    _ensure_costs_config(project_dir)
    _ensure_env_template(project_dir)
  goal/bootstrap/templates.py:
    e: ProjectTemplate
    ProjectTemplate:  # Template configuration for a project type.
  goal/changelog.py:
    e: _classify_file_domain,_build_domain_entry,_build_simple_entry,_insert_entry,_find_unreleased_insert_pos,update_changelog
    _classify_file_domain(filepath;domain_mapping)
    _build_domain_entry(version;date_str;files;config)
    _build_simple_entry(version;date_str;files)
    _insert_entry(existing_content;entry)
    _find_unreleased_insert_pos(content)
    update_changelog(version;files;commit_msg;config;changelog_entry)
  goal/cli/__init__.py:
    e: _has_cli_flag,_goal_update_command,_warn_goal_binary_mismatch,_setup_nfo_logging,_nfo_log_call,load_command_modules,_auto_update_goal,_show_goal_version_banner,_explicit_ascii_flag,_resolve_output_markdown,_configure_main_context,main,GoalGroup
    GoalGroup: get_command(2),parse_args(2)  # Custom Click Group that shows docs URL for unknown commands 
    _has_cli_flag(args;short;long)
    _goal_update_command()
    _warn_goal_binary_mismatch()
    _setup_nfo_logging(nfo_format;nfo_sink)
    _nfo_log_call()
    load_command_modules()
    _auto_update_goal(current_version;latest_version)
    _show_goal_version_banner()
    _explicit_ascii_flag(argv)
    _resolve_output_markdown(output_markdown;all_flags)
    _configure_main_context(ctx;bump;target_version;yes;all_flags;upgrade_deps;recursive;interactive;no_publish;force_publish;todo;markdown;dry_run;config_path;abstraction)
    main(ctx;bump;target_version;yes;all_flags;upgrade_deps;recursive;interactive;no_publish;force_publish;todo;output_markdown;dry_run;config_path;abstraction;nfo_format;nfo_sink)
  goal/cli/authors_cmd.py:
    e: display_author_details,display_current_author,authors,authors_list,authors_add,authors_remove,authors_update,authors_import,authors_export,authors_find,authors_co_author,authors_current
    display_author_details(identifier;author)
    display_current_author(current)
    authors()
    authors_list()
    authors_add(name;email;role;alias)
    authors_remove(email)
    authors_update(email;name;role;alias)
    authors_import()
    authors_export()
    authors_find(identifier)
    authors_co_author(name;email)
    authors_current()
  goal/cli/commit_cmd.py:
    e: _output_detailed,_output_simple,commit,fix_summary,validate
    _output_detailed(title;body;use_markdown)
    _output_simple(title;co_authors;use_markdown)
    commit(ctx;detailed;unstaged;markdown;ticket;abstraction;co_author)
    fix_summary(ctx;fix;preview;cached)
    validate(ctx;fix;cached)
  goal/cli/config_cmd.py:
    e: config,config_show,config_validate,config_update,config_set,config_get,setup
    config()
    config_show(ctx;key)
    config_validate(ctx;strict;fix)
    config_update(ctx)
    config_set(ctx;key;value)
    config_get(ctx;key)
    setup(reset;show_config)
  goal/cli/config_validate_cmd.py:
    e: validate_cmd
    validate_cmd(ctx;config;strict;fix)
  goal/cli/doctor_cmd.py:
    e: doctor
    doctor(ctx;fix;path;todo;manager)
  goal/cli/hooks_cmd.py:
    e: display_success_message,display_failure_message,display_install_success,hooks,hooks_install,hooks_uninstall,hooks_run,hooks_status
    display_success_message(message)
    display_failure_message(message)
    display_install_success()
    hooks()
    hooks_install(force)
    hooks_uninstall()
    hooks_run(all_files)
    hooks_status()
  goal/cli/license_cmd.py:
    e: license,license_create,license_update,license_validate,license_info,license_check,license_list,license_template
    license()
    license_create(license_id;fullname;year;force)
    license_update(license_id;fullname;year)
    license_validate()
    license_info(license_id)
    license_check(license1;license2)
    license_list(custom)
    license_template(license_id;file)
  goal/cli/postcommit_cmd.py:
    e: postcommit,postcommit_run,postcommit_list,postcommit_validate,postcommit_info
    postcommit()
    postcommit_run()
    postcommit_list()
    postcommit_validate()
    postcommit_info()
  goal/cli/publish.py:
    e: makefile_has_target,_get_project_strategy,_get_configured_project_types,_get_python_bin,_ensure_publish_deps,_read_pyproject_package_name,_read_setup_py_package_name,_read_python_package_name,_normalized_name_candidates,_python_artifacts_for_version,_format_artifact_args,_resolve_python_publish_cmd,_run_python_build,_available_dist_artifacts,_ensure_python_artifacts_for_version,_prepare_python_publish,_read_nodejs_package_name,_nodejs_artifacts_for_version,_is_rate_limited,_run_publish_command,publish_project
    makefile_has_target(target)
    _get_project_strategy(config;project_type)
    _get_configured_project_types(config)
    _get_python_bin()
    _ensure_publish_deps(python_bin)
    _read_pyproject_package_name()
    _read_setup_py_package_name()
    _read_python_package_name()
    _normalized_name_candidates(package_name)
    _python_artifacts_for_version(version;package_name)
    _format_artifact_args(artifacts)
    _resolve_python_publish_cmd(publish_cmd;version)
    _run_python_build(build_cmd;python_bin)
    _available_dist_artifacts()
    _ensure_python_artifacts_for_version(version;build_cmd;python_bin)
    _prepare_python_publish(strategy;version)
    _read_nodejs_package_name()
    _nodejs_artifacts_for_version(version)
    _is_rate_limited(result)
    _run_publish_command(ptype;publish_cmd)
    publish_project(project_types;version;yes;config)
  goal/cli/publish_cmd.py:
    e: _publish_impl,publish
    _publish_impl(ctx_obj;use_make;target;version_arg)
    publish(ctx;use_make;target;version_arg)
  goal/cli/push_cmd.py:
    e: push
    push(ctx;bump;no_tag;no_changelog;no_version_sync;no_publish;force_publish;message;dry_run;output_markdown;split;ticket;abstraction;todo;model;api_key)
  goal/cli/recover_cmd.py:
    e: recover,_get_error_output
    recover(ctx;full;error_file;error_message;no_backup;verbose)
    _get_error_output(error_file;error_message)
  goal/cli/tests.py:
    e: _get_project_strategy,_active_venv_python,_resolve_project_python,_pytest_importable,_prefer_uv_run,_rewrite_bash_pytest_for_uv,_coerce_python_strategy_to_project_pytest,_display_test_error,_has_package,_run_python_test,_run_nodejs_test,_run_subdir_test,_run_tests_in_subdirs,_resolve_root_python,_build_python_test_command,_ensure_root_pytest_or_mark_failed,_run_root_test,_run_project_type_tests,run_tests,get_test_execution_details
    _get_project_strategy(config;project_type)
    _active_venv_python()
    _resolve_project_python(project_root;fallback_python)
    _pytest_importable(python_bin;project_root)
    _prefer_uv_run(python_bin;has_uv)
    _rewrite_bash_pytest_for_uv(test_cmd_str;has_uv;python_bin)
    _coerce_python_strategy_to_project_pytest(test_cmd_str;python_bin)
    _display_test_error(result;test_dir;project_type)
    _has_package(python_bin;package_name)
    _run_python_test(test_dir;base_cmd)
    _run_nodejs_test(test_dir;base_cmd)
    _run_subdir_test(project_type;base_cmd;test_dir)
    _run_tests_in_subdirs(project_type;base_cmd)
    _resolve_root_python()
    _build_python_test_command(test_cmd_str;strategy_test_cmd)
    _ensure_root_pytest_or_mark_failed(python_bin;run_subdir_scan;ptype;test_cmd)
    _run_root_test(test_cmd;test_cmd_str;use_subprocess)
    _run_project_type_tests(ptype;config)
    run_tests(project_types;config)
    get_test_execution_details()
  goal/cli/tests_discovery.py:
    e: _has_usable_test_script,_has_project_marker,_find_project_root,find_python_test_dirs,find_nodejs_test_dirs
    _has_usable_test_script(project_dir;project_type)
    _has_project_marker(project_dir;marker)
    _find_project_root(path;project_type)
    find_python_test_dirs()
    find_nodejs_test_dirs()
  goal/cli/tests_pytest_setup.py:
    e: check_python_venv,_is_uv_project,_try_uv_install,ensure_pytest_for_project
    check_python_venv(project_root)
    _is_uv_project(project_root)
    _try_uv_install(project_root)
    ensure_pytest_for_project(project_root;python_bin)
  goal/cli/utils_cmd.py:
    e: status,init,info,version,package_managers,check_versions,clone,bootstrap
    status(ctx;markdown)
    init(ctx;force)
    info()
    version(bump_type)
    package_managers(language;available)
    check_versions(update_badges)
    clone(ctx;url;directory)
    bootstrap(yes;path)
  goal/cli/validation_cmd.py:
    e: validation,validation_run,validation_list,validation_validate,validation_info
    validation()
    validation_run()
    validation_list()
    validation_validate()
    validation_info()
  goal/cli/version.py:
  goal/cli/version_sync.py:
    e: _update_version_file,_update_json_version_file,_update_toml_version,_update_cargo_version,_update_setup_py_version,_update_csproj_versions,_update_pom_xml,_update_readme_metadata,_warn_lock_refresh,_snapshot_paths,_append_changed_paths,_sync_dependency_lockfiles,_sync_uv_lock,_sync_dependency_locks_after_manifest_updates,_update_init_py_versions,sync_all_versions
    _update_version_file(new_version;updated)
    _update_json_version_file(filename;new_version;user_config;updated)
    _update_toml_version(filename;new_version;user_config;updated)
    _update_cargo_version(filename;new_version;user_config;updated)
    _update_setup_py_version(new_version;user_config;updated)
    _update_csproj_versions(new_version;updated)
    _update_pom_xml(new_version;updated)
    _update_readme_metadata(user_config;new_version;updated)
    _warn_lock_refresh(message)
    _snapshot_paths(paths)
    _append_changed_paths(updated;before;paths)
    _sync_dependency_lockfiles(updated)
    _sync_uv_lock(updated)
    _sync_dependency_locks_after_manifest_updates(updated)
    _update_init_py_versions(new_version;updated)
    sync_all_versions(new_version;user_config)
  goal/cli/version_types.py:
  goal/cli/version_utils.py:
    e: detect_project_types,find_version_files,get_version_from_file,get_current_version,bump_version,update_version_in_file,update_json_version,_build_author_block,_update_tomlkit_license,_update_tomlkit_authors,_update_tomlkit_classifier,_update_pyproject_with_tomlkit,_update_regex_license,_update_regex_authors,_update_regex_classifier,_update_pyproject_with_regex,_update_pyproject_metadata,_update_package_json_metadata,_update_setup_py_metadata,update_project_metadata,_update_license_section,_update_author_section,update_readme_metadata
    detect_project_types()
    find_version_files()
    get_version_from_file(filepath;pattern)
    get_current_version()
    bump_version(version;bump_type)
    update_version_in_file(filepath;pattern;old_version;new_version)
    update_json_version(filepath;new_version)
    _build_author_block(existing_authors;author_name;author_email)
    _update_tomlkit_license(doc;license_id)
    _update_tomlkit_authors(doc;author_name;author_email)
    _update_tomlkit_classifier(doc;license_classifier)
    _update_pyproject_with_tomlkit(content;author_name;author_email;license_id;license_classifier)
    _update_regex_license(content;license_id)
    _update_regex_authors(content;author_name;author_email)
    _update_regex_classifier(content;license_classifier)
    _update_pyproject_with_regex(content;author_name;author_email;license_id;license_classifier)
    _update_pyproject_metadata(content;author_name;author_email;license_id;license_classifier)
    _update_package_json_metadata(content;author_name;author_email;license_id)
    _update_setup_py_metadata(content;author_name;author_email;license_id)
    update_project_metadata(filepath;user_config)
    _update_license_section(content;license_id)
    _update_author_section(content;author_name)
    update_readme_metadata(user_config)
  goal/cli/wizard_cmd.py:
    e: wizard,_setup_git_repository,_find_git_root,_add_git_remote,_setup_user_config,_setup_project_config,_show_setup_summary
    wizard(reset;skip_git;skip_user;skip_project)
    _setup_git_repository()
    _find_git_root()
    _add_git_remote()
    _setup_user_config(reset)
    _setup_project_config()
    _show_setup_summary()
  goal/cli.py:
    e: _format_import_warning_message,_print_import_warning
    _format_import_warning_message(exc)
    _print_import_warning(exc;stderr)
  goal/cli_helpers.py:
    e: strip_ansi,split_paths_by_type,stage_paths,confirm
    strip_ansi(text)
    split_paths_by_type(paths)
    stage_paths(paths)
    confirm(prompt;default)
  goal/commit_generator.py:
    e: is_detailed_output_requested,display_commit_message,print_detailed_message,display_detailed_message
    is_detailed_output_requested(args)
    display_commit_message(generator)
    print_detailed_message(result)
    display_detailed_message(generator)
  goal/config/__init__.py:
  goal/config/constants.py:
  goal/config/manager.py:
    e: init_config,load_config,ensure_config,GoalConfig
    GoalConfig: __init__(1),_find_config(1),_find_git_root(0),exists(0),load(0),reload(0),_get_default_config(0),_deep_copy(1),_merge_configs(2),_detect_project_name(0),_detect_project_types(0),_detect_description(0),_detect_version_files(0),save(1),get(2),set(2),update_from_detection(0),validate(0),get_commit_template(1),get_strategy(1),get_registry(1),get_publish_fallback(0),should_auto_update(0),to_dict(0)  # Manages goal.yaml configuration file.
    init_config(force)
    load_config(config_path)
    ensure_config(auto_update)
  goal/config/validation.py:
    e: validate_config_file,validate_config_interactive,_auto_fix_config,ConfigValidationError,ConfigValidator
    ConfigValidationError: __init__(2)  # Error raised when configuration validation fails.
    ConfigValidator: __init__(1),validate(1),_validate_required_sections(0),_validate_project_section(0),_validate_git_section(0),_validate_versioning_section(0),_validate_publishing_section(0),_check_bool(3),_check_numeric(6),_validate_advanced_section(0),_validate_no_unknown_keys(0)  # Validates Goal configuration files.
    validate_config_file(config_path;strict)
    validate_config_interactive(config_path)
    _auto_fix_config(config;warnings)
  goal/config.py:
  goal/deep_analyzer.py:
    e: CodeChangeAnalyzer
    CodeChangeAnalyzer: __init__(0),analyze_file_diff(3),_detect_language(1),_analyze_python_diff(2),_detect_value_indicators(1),_extract_python_entities(1),_get_decorator_name(1),_calculate_complexity(1),_analyze_js_diff(2),_analyze_generic_diff(2),_detect_functional_areas(2)  # Analyzes code changes to extract functional meaning.
  goal/deep_analyzer_aggregate.py:
    e: CodeChangeAggregatorMixin
    CodeChangeAggregatorMixin: aggregate_changes(1),_detect_file_patterns(1),_check_analyzer_value(2),_check_cli_value(2),_check_area_values(2),_check_complexity_value(1),_check_architecture_value(1),_build_entity_fallback(2),infer_functional_value(2),detect_relations(1),generate_functional_summary(1),_format_entity_names(2),_format_relations(1),_format_complexity_change(1),_format_areas(1),_build_summary(3)
  goal/deep_analyzer_patterns.py:
  goal/dependency_update.py:
    e: _run_update_command,_select_managers_to_update,_path_has_skipped_dir,_iter_project_marker_files,discover_dependency_project_roots,_format_project_label,_update_dependencies_in_root,update_project_dependencies,DependencyUpdateResult
    DependencyUpdateResult:  # Result of a dependency update operation.
    _run_update_command(command;cwd)
    _select_managers_to_update(project_path)
    _path_has_skipped_dir(path)
    _iter_project_marker_files(project_root)
    discover_dependency_project_roots(project_path)
    _format_project_label(project_root)
    _update_dependencies_in_root(project_root)
    update_project_dependencies(project_path)
  goal/doctor/__init__.py:
  goal/doctor/core.py:
    e: diagnose_project,diagnose_and_report
    diagnose_project(project_dir;project_type;auto_fix)
    diagnose_and_report(project_dir;project_type;auto_fix)
  goal/doctor/dotnet.py:
    e: diagnose_dotnet
    diagnose_dotnet(project_dir;auto_fix)
  goal/doctor/go.py:
    e: diagnose_go
    diagnose_go(project_dir;auto_fix)
  goal/doctor/java.py:
    e: diagnose_java
    diagnose_java(project_dir;auto_fix)
  goal/doctor/logging.py:
    e: _log_issue,_log_fix
    _log_issue(issue)
    _log_fix(issue)
  goal/doctor/models.py:
    e: Issue,DoctorReport
    Issue:  # A single diagnosed issue.
    DoctorReport: errors(0),warnings(0),fixed(0),has_problems(0)  # Aggregated report from a doctor run.
  goal/doctor/nodejs.py:
    e: diagnose_nodejs
    diagnose_nodejs(project_dir;auto_fix)
  goal/doctor/php.py:
    e: diagnose_php
    diagnose_php(project_dir;auto_fix)
  goal/doctor/python.py:
    e: diagnose_python
    diagnose_python(project_dir;auto_fix)
  goal/doctor/python_diag_core.py:
    e: PythonDiagnosticsCore
    PythonDiagnosticsCore: __init__(3),check_py001_missing_config(4),check_py002_build_system(0),check_py003_license_classifiers(0),check_py004_deprecated_backends(0),check_py005_license_table(0),check_py006_duplicate_authors(0),check_py007_requires_python(0),check_py008_empty_classifiers(0),check_py009_string_authors(0),_should_skip_string_author_check(0),_convert_string_author_block(1)  # Container for Python diagnostic checks with shared state.
  goal/doctor/python_diag_extended.py:
    e: PythonDiagnostics
    PythonDiagnostics: _collect_py010_inconsistencies(3),_sync_py010_files(3),check_py010_project_name_consistency(0),_collect_py011_inconsistencies(4),_sync_py011_files(4),check_py011_version_consistency(0),check_py012_dist_cleanup(0),_collect_stale_dist_files(2),_remove_stale_dist_files(2),check_py013_goal_publish_pattern(0),_extract_goal_publish_pattern(1),_goal_publish_pattern_is_acceptable(3),_rewrite_goal_publish_pattern(2),check_py014_pypi_token(0),_is_publish_enabled(1),_has_pypi_credentials(0),run_all_checks(0),write_fixes(1)  # Python project diagnostics — extended PY010–PY014 checks lay
  goal/doctor/ruby.py:
    e: diagnose_ruby
    diagnose_ruby(project_dir;auto_fix)
  goal/doctor/rust.py:
    e: diagnose_rust
    diagnose_rust(project_dir;auto_fix)
  goal/doctor/todo.py:
    e: _generate_ticket_id,_read_existing_tickets,_format_todo_entry,add_issues_to_todo,diagnose_and_report_with_todo
    _generate_ticket_id(issue)
    _read_existing_tickets(todo_file)
    _format_todo_entry(issue)
    add_issues_to_todo(project_dir;issues;todo_file)
    diagnose_and_report_with_todo(project_dir;project_type;auto_fix;todo_file)
  goal/enhanced_summary.py:
  goal/formatter.py:
    e: _build_functional_overview,_build_files_section,_determine_next_steps,format_push_result,format_goal_all_summary,_format_complexity_metric,_format_metrics_section,_format_relations_section,_build_capabilities_content,_build_roles_content,_build_details_content,_get_optional_sections,_build_enhanced_summary_section,_add_optional_sections,format_enhanced_summary,format_status_output,MarkdownFormatter
    MarkdownFormatter: __init__(0),add_header(2),add_metadata(0),add_section(4),add_list(3),add_command_output(3),add_summary(2),render(0)  # Formats Goal output as structured markdown for LLM consumpti
    _build_functional_overview(features;summary;entities;files;stats;current_version;new_version;commit_msg;project_types)
    _build_files_section(formatter;files;stats;analysis)
    _determine_next_steps(error;test_exit_code;new_version)
    format_push_result(project_types;files;stats;current_version;new_version;commit_msg;commit_body;test_result;test_exit_code;actions;error;analysis)
    format_goal_all_summary()
    _format_complexity_metric(metrics)
    _format_metrics_section(metrics;relations)
    _format_relations_section(relations)
    _build_capabilities_content(capabilities)
    _build_roles_content(roles)
    _build_details_content(commit_body;capabilities)
    _get_optional_sections(capabilities;roles;metrics;relations;commit_body)
    _build_enhanced_summary_section(commit_title;files;stats;current_version;new_version)
    _add_optional_sections(formatter;capabilities;roles;metrics;relations;commit_body)
    format_enhanced_summary(commit_title;commit_body;capabilities;roles;relations;metrics;files;stats;current_version;new_version)
    format_status_output(version;branch;staged_files;unstaged_files)
  goal/generator/__init__.py:
  goal/generator/analyzer.py:
    e: ChangeAnalyzer,ContentAnalyzer
    ChangeAnalyzer: classify_change_type(3),_detect_signals(2),_has_package_code(1),_is_docs_only(1),_is_ci_only(1),_has_new_goal_python_file(2),_score_by_file_patterns(2),_score_by_diff_content(2),_score_by_statistics(3),_score_by_signals(4),_score_package_signals(3),_score_text_signals(2),_score_file_signals(2),_score_path_signals(2),_score_new_functionality(3),_resolve_change_type(4),detect_scope(1),extract_functions_changed(1)  # Analyze git changes to classify type, detect scope, and extr
    ContentAnalyzer: short_action_summary(2),_detect_tags(2),_summary_from_tags(1),_summary_from_paths(2),per_file_notes(2),_get_added_lines(2),_notes_python(3),_notes_docs(4),_notes_shell(3)  # Analyze content for short summaries and per-file notes.
  goal/generator/generator.py:
    e: generate_smart_commit_message,CommitMessageGenerator
    CommitMessageGenerator: __init__(1),get_diff_stats(1),get_name_status(2),get_numstat_map(2),get_changed_files(2),get_diff_content(2),classify_change_type(3),detect_scope(1),extract_functions_changed(1),_short_action_summary(2),_per_file_notes(2),generate_commit_message(3),generate_abstraction_message(2),generate_changelog_entry(2),generate_enhanced_summary(2),_try_enhanced_summary(2),_classify_files(2),_build_statistics_section(1),_build_summary_section(5),_build_file_lists(4),_build_per_file_notes(3),_build_implementation_notes(0),generate_detailed_message(2)  # Generate conventional commit messages using diff analysis an
    generate_smart_commit_message(cached)
  goal/generator/git_ops.py:
    e: GitDiffOperations
    GitDiffOperations: __init__(0),get_diff_stats(1),get_name_status(2),get_numstat_map(2),get_changed_files(2),get_diff_content(2),clear_cache(0)  # Git diff operations with caching.
  goal/git_ops.py:
    e: run_git,run_command,_echo_cmd,_run_git_verbose,run_git_with_status,run_command_tee,is_git_repository,validate_repo_url,get_remote_url,list_remotes,_prompt_remote_url,_list_remote_branches,get_remote_branch,clone_repository,_select_branch,_handle_merge_strategy,_handle_init_remote,_handle_clone,_handle_local_init,ensure_git_repository,ensure_remote,get_staged_files,get_unstaged_files,get_working_tree_files,get_diff_stats,get_diff_content,read_ticket,apply_ticket_prefix
    run_git()
    run_command(command;capture)
    _echo_cmd(args)
    _run_git_verbose()
    run_git_with_status()
    run_command_tee(command)
    is_git_repository()
    validate_repo_url(url)
    get_remote_url(remote)
    list_remotes()
    _prompt_remote_url()
    _list_remote_branches(remote)
    get_remote_branch()
    clone_repository(url;target_dir)
    _select_branch(branches)
    _handle_merge_strategy(branches;has_files)
    _handle_init_remote(has_files)
    _handle_clone()
    _handle_local_init()
    ensure_git_repository(auto)
    ensure_remote(auto)
    get_staged_files()
    get_unstaged_files()
    get_working_tree_files()
    get_diff_stats(cached)
    get_diff_content(cached;max_lines)
    read_ticket(path)
    apply_ticket_prefix(title;ticket)
  goal/hooks/__init__.py:
  goal/hooks/config.py:
    e: get_hook_config,create_precommit_config
    get_hook_config(project_dir)
    create_precommit_config(project_dir;include_goal)
  goal/hooks/manager.py:
    e: install_hooks,uninstall_hooks,run_hooks,HooksManager
    HooksManager: __init__(1),is_precommit_installed(0),is_hooks_configured(0),install_precommit(0),create_hook_script(0),create_precommit_config(1),install_hooks(1),uninstall_hooks(0),run_validation(1),run_hooks(1),status(0)  # Manages pre-commit hooks for Goal.
    install_hooks(project_dir;force)
    uninstall_hooks(project_dir)
    run_hooks(project_dir;all_files)
  goal/installers/__init__.py:
  goal/installers/broker.py:
    e: PackageManagerBroker
    PackageManagerBroker: __init__(1),detect_available(0),install(4),_select_manager(2),_report(2),detect_lockfile(0),install_smart(2),show_available(0)  # Intelligent package manager broker.
  goal/installers/config.py:
    e: load_installer_config,InstallerConfig
    InstallerConfig: from_dict(2)  # Configuration for package manager installer behavior.
    load_installer_config(project_dir)
  goal/installers/managers/__init__.py:
  goal/installers/managers/base.py:
    e: InstallResult,AbstractPackageManager
    InstallResult:  # Result of a package manager operation.
    AbstractPackageManager: is_available(0),install_editable(1),install_requirements(1),install_from_lockfile(0),_run(1)  # Abstract base class for package managers.
  goal/installers/managers/pdm.py:
    e: PdmManager
    PdmManager: install_editable(1),install_requirements(1),install_from_lockfile(0)  # PDM package manager implementation.
  goal/installers/managers/pip.py:
    e: PipManager
    PipManager: is_available(0),install_editable(1),install_requirements(1)  # Pip package manager implementation - always available fallba
  goal/installers/managers/poetry.py:
    e: PoetryManager
    PoetryManager: install_editable(1),install_requirements(1),install_from_lockfile(0)  # Poetry package manager implementation.
  goal/installers/managers/uv.py:
    e: UvManager
    UvManager: install_editable(1),install_requirements(1),sync_lockfile(0),install_self(0),install_from_lockfile(0)  # UV package manager implementation.
  goal/io/__init__.py:
  goal/io/stdio.py:
    e: set_stdio_markdown,use_markdown_stdio,echo_via_markdown,echo_heading,echo_auto,echo_command_block,echo_output_block,echo_info,echo_status_ok,echo_status_warn,echo_status_error
    set_stdio_markdown(enabled)
    use_markdown_stdio()
    echo_via_markdown(text)
    echo_heading(text)
    echo_auto(text)
    echo_command_block(command)
    echo_output_block(output)
    echo_info(text)
    echo_status_ok(text)
    echo_status_warn(text)
    echo_status_error(text)
  goal/license/__init__.py:
  goal/license/manager.py:
    e: create_license_file,update_license_file,LicenseManager
    LicenseManager: __init__(1),get_available_licenses(0),get_license_template(1),add_custom_template(2),create_license_file(4),update_license_file(3),_detect_license_type(2),_resolve_license_id(2),_extract_owner_from_content(1),validate_license_file(0)  # Manages license operations including template handling and f
    create_license_file(license_id;fullname;year;force)
    update_license_file(license_id;fullname;year)
  goal/license/spdx.py:
    e: _load_spdx_data,validate_spdx_id,get_license_info,check_compatibility,get_compatible_licenses,is_copyleft,is_permissive
    _load_spdx_data()
    validate_spdx_id(license_id)
    get_license_info(license_id)
    check_compatibility(license1;license2)
    get_compatible_licenses(license_id)
    is_copyleft(license_id)
    is_permissive(license_id)
  goal/package_managers.py:
    e: _path_matches,_has_any_matching_path,_detect_package_manager,_has_language_extension,detect_package_managers,get_package_manager,get_package_managers_by_language,is_package_manager_available,get_available_package_managers,get_preferred_package_manager,_pip_update_all_command,get_update_all_command,format_package_manager_command,get_package_manager_info,list_all_package_managers,detect_project_language,suggest_package_managers,PackageManager
    PackageManager: __post_init__(0)  # Package manager configuration and capabilities.
    _path_matches(project_root;pattern)
    _has_any_matching_path(project_root;patterns)
    _detect_package_manager(project_root;pm)
    _has_language_extension(project_root;extensions)
    detect_package_managers(project_path)
    get_package_manager(name)
    get_package_managers_by_language(language)
    is_package_manager_available(pm)
    get_available_package_managers(project_path)
    get_preferred_package_manager(project_path;language)
    _pip_update_all_command(project_root)
    get_update_all_command(pm;project_root)
    format_package_manager_command(pm;command_type)
    get_package_manager_info(pm)
    list_all_package_managers()
    detect_project_language(project_path)
    suggest_package_managers(project_path)
  goal/postcommit/__init__.py:
  goal/postcommit/actions.py:
    e: PostCommitAction,NotificationAction,WebhookAction,ScriptAction,GitPushAction
    PostCommitAction: __init__(1),execute(1),get_name(0),validate_config(0)  # Base class for post-commit actions.
    NotificationAction: get_name(0),validate_config(0),execute(1)  # Send desktop notification after commit.
    WebhookAction: get_name(0),validate_config(0),execute(1)  # Send webhook POST request after commit.
    ScriptAction: get_name(0),validate_config(0),execute(1)  # Run custom script after commit.
    GitPushAction: get_name(0),validate_config(0),execute(1)  # Automatically push after commit.
  goal/postcommit/manager.py:
    e: run_post_commit_actions,PostCommitManager
    PostCommitManager: __init__(1),get_config(0),get_commit_info(0),run_actions(0),list_actions(0),validate_actions(0)  # Manages post-commit actions for Goal.
    run_post_commit_actions(project_dir)
  goal/project_bootstrap.py:
    e: _match_marker,detect_project_types_deep,_find_python_bin,_read_openrouter_api_key,_find_openrouter_api_key,_find_git_root,refresh_test_dependencies,_ensure_python_test_dependency,_ensure_python_env,_should_skip_install,_install_python_deps,_install_python_deps_broker,_ensure_generic_env,ensure_project_environment,find_existing_tests,_resolve_scaffold_test_path,scaffold_test,_new_bootstrap_result,_pfix_auto_apply,_coerce_bool,_goal_yaml_auto_apply,_auto_fix_enabled,_run_bootstrap_diagnostics,_ensure_bootstrap_tests,bootstrap_project,bootstrap_all_projects,_ensure_costs_installed,_ensure_pfix_env,_validate_pfix_env,_ensure_pfix_installed,_ensure_pfix_config,scaffold_test_file
    _match_marker(base;pattern)
    detect_project_types_deep(root;max_depth)
    _find_python_bin(project_dir)
    _read_openrouter_api_key(env_file)
    _find_openrouter_api_key(project_dir)
    _find_git_root(project_dir)
    refresh_test_dependencies(project_types)
    _ensure_python_test_dependency(project_dir;python_bin;test_dep)
    _ensure_python_env(project_dir;cfg;yes)
    _should_skip_install(project_dir;markers)
    _install_python_deps(project_dir;cfg;python_bin)
    _install_python_deps_broker(project_dir;extras)
    _ensure_generic_env(project_dir;project_type;cfg;yes)
    ensure_project_environment(project_dir;project_type;yes)
    find_existing_tests(project_dir;project_type)
    _resolve_scaffold_test_path(project_dir;project_type;cfg;package_name)
    scaffold_test(project_dir;project_type;yes)
    _new_bootstrap_result(project_dir;project_type)
    _pfix_auto_apply(project_dir)
    _coerce_bool(value)
    _goal_yaml_auto_apply(project_dir)
    _auto_fix_enabled(project_dir)
    _run_bootstrap_diagnostics(project_dir;project_type;yes)
    _ensure_bootstrap_tests(project_dir;project_type;yes)
    bootstrap_project(project_dir;project_type;yes)
    bootstrap_all_projects(root;yes)
    _ensure_costs_installed(project_dir;python_bin)
    _ensure_pfix_env(project_dir)
    _validate_pfix_env(project_dir)
    _ensure_pfix_installed(project_dir;yes)
    _ensure_pfix_config(project_dir;yes)
    scaffold_test_file(project_dir;project_type)
  goal/project_doctor.py:
  goal/publish/__init__.py:
  goal/publish/changes.py:
    e: _normalize_path,_basename,_suffix,_matches_any,_is_test_path,_is_metadata_file,_is_publishable_for_type,analyze_publishable_changes,PublishChangeReport
    PublishChangeReport: skip_reason(0)  # Result of analyzing staged files for publish-worthy changes.
    _normalize_path(path)
    _basename(path)
    _suffix(path)
    _matches_any(path;patterns)
    _is_test_path(path)
    _is_metadata_file(path)
    _is_publishable_for_type(path;project_type)
    analyze_publishable_changes(files;project_types)
  goal/publish/github_fallback.py:
    e: _publishing_section,get_github_release_config,detect_github_owner_repo,resolve_github_repo,is_pypi_blocked,_gh_available,_env_token_present,_token_present,_gh_authenticated,github_fallback_actionable,_dist_assets,publish_github_release,try_github_fallback,GitHubReleaseConfig
    GitHubReleaseConfig:
    _publishing_section(config)
    get_github_release_config(config)
    detect_github_owner_repo()
    resolve_github_repo(package_name;gh_config)
    is_pypi_blocked(result)
    _gh_available()
    _env_token_present(token_env)
    _token_present(token_env)
    _gh_authenticated()
    github_fallback_actionable(gh_config)
    _dist_assets(version;package_name;asset_glob)
    publish_github_release(version)
    try_github_fallback(result)
  goal/push/__init__.py:
  goal/push/commands.py:
    e: push
    push(ctx;bump;no_tag;no_changelog;no_version_sync;no_publish;force_publish;message;dry_run;yes;output_markdown;split;ticket;abstraction;todo)
  goal/push/core.py:
    e: run_git_local,show_workflow_preview,add_slow_test_tickets_to_planfile,output_final_summary,_validate_toml_or_exit,_apply_enhanced_quality_gates,_handle_no_files,_abort_if_missing_commit_title,_maybe_show_workflow_preview,_run_test_stage_or_exit,execute_push_workflow,_build_publish_summary,_initialize_context,_detect_project_types,_bootstrap_projects,_detect_and_bootstrap_projects,_handle_no_changes,_validate_staged_files,_handle_commit_phase,PushContext
    PushContext: __init__(1),get(2)  # Context object wrapper for push command.
    run_git_local()
    show_workflow_preview(files;stats;current_version;new_version;commit_msg;commit_body;markdown;ctx_obj)
    add_slow_test_tickets_to_planfile(test_details)
    output_final_summary(ctx_obj;markdown;project_types;files;stats;current_version;new_version;commit_msg;commit_body;test_exit_code;publish_success;no_tag;publish_required;publish_skip_reason)
    _validate_toml_or_exit(dry_run)
    _apply_enhanced_quality_gates(ctx_obj;commit_msg;detailed_result;files;stats;message;markdown)
    _handle_no_files(ctx_obj;project_types;dry_run;markdown;files)
    _abort_if_missing_commit_title(commit_title)
    _maybe_show_workflow_preview(ctx_obj;files;stats;current_version;new_version;commit_msg;commit_body;markdown)
    _run_test_stage_or_exit(project_types;ctx_obj;markdown;files;stats;current_version;new_version;commit_msg;commit_body)
    execute_push_workflow(ctx_obj;bump;no_tag;no_changelog;no_version_sync;message;dry_run;yes;markdown;split;ticket;abstraction;todo;force;model;api_key;no_publish;force_publish)
    _build_publish_summary(publish_success;publish_required;publish_skip_reason)
    _initialize_context(ctx_obj;bump;message;yes;markdown)
    _detect_project_types()
    _bootstrap_projects(project_types;dry_run;yes)
    _detect_and_bootstrap_projects(ctx_obj;dry_run;yes)
    _handle_no_changes(ctx_obj;project_types;dry_run;markdown)
    _validate_staged_files(ctx_obj;dry_run;force)
    _handle_commit_phase(ctx_obj;split;message;commit_title;commit_body;commit_msg;files;ticket;new_version;current_version;no_version_sync;no_changelog)
  goal/push/stages/__init__.py:
  goal/push/stages/changelog.py:
    e: handle_changelog,update_changelog_stage
    handle_changelog(new_version;files;commit_msg;config;no_changelog)
    update_changelog_stage(new_version;files;commit_msg;config)
  goal/push/stages/commit.py:
    e: get_commit_message,_build_validation_summary,_confirm_suggested_title,_echo_applied_title_fix,enforce_quality_gates,handle_single_commit,_commit_file_group,_commit_release_metadata,handle_split_commits
    get_commit_message(ctx_obj;files;diff_content;message;ticket;abstraction)
    _build_validation_summary(commit_msg;detailed_result;total_adds;total_dels)
    _confirm_suggested_title(commit_msg;suggested_title;yes)
    _echo_applied_title_fix(ctx_obj;commit_msg;markdown)
    enforce_quality_gates(ctx_obj;commit_msg;detailed_result;files;total_adds;total_dels;yes;markdown)
    handle_single_commit(commit_title;commit_body;commit_msg;message;yes)
    _commit_file_group(gname;paths;generator;ticket;yes)
    _commit_release_metadata(ctx_obj;files;config_dict;ticket;new_version;current_version;no_version_sync;no_changelog)
    handle_split_commits(ctx_obj;files;ticket;new_version;current_version;no_version_sync;no_changelog;yes)
  goal/push/stages/costs.py:
    e: _is_cost_tracking_enabled,_compute_ai_costs,update_cost_badges
    _is_cost_tracking_enabled()
    _compute_ai_costs(project_dir;model;api_key)
    update_cost_badges(ctx_obj;version;model;api_key)
  goal/push/stages/dry_run.py:
    e: _build_split_plan_body,_format_markdown_dry_run,_print_plain_dry_run,handle_dry_run
    _build_split_plan_body(ctx_obj;files;ticket;new_version;no_version_sync;no_changelog)
    _format_markdown_dry_run(ctx_obj;project_types;files;stats;current_version;new_version;commit_msg;commit_body;detailed_result)
    _print_plain_dry_run(project_types;files;stats;current_version;new_version;commit_msg)
    handle_dry_run(ctx_obj;project_types;files;stats;current_version;new_version;commit_msg;commit_body;detailed_result;split;ticket;bump;no_version_sync;no_changelog;no_tag;markdown)
  goal/push/stages/publish.py:
    e: _format_skip_message,handle_publish
    _format_skip_message(report)
    handle_publish(project_types;new_version;yes;no_publish;config;staged_files;force_publish)
  goal/push/stages/push_remote.py:
    e: _print_push_header,_push_tag_if_needed,_handle_push_failure,push_to_remote,_offer_recovery,_is_large_file_error,_handle_large_file_error,_handle_large_files_in_history,_handle_large_files_staged,_execute_recovery,_show_diff_info,_show_recovery_menu,_handle_recovery_choice,_handle_force_push,_handle_pull_merge,_handle_view_diff,_handle_automatic_recovery
    _print_push_header(branch;yes)
    _push_tag_if_needed(tag_name;no_tag)
    _handle_push_failure(result;branch;yes)
    push_to_remote(branch;tag_name;no_tag;yes)
    _offer_recovery(error_output)
    _is_large_file_error(error_output)
    _handle_large_file_error(error_output)
    _handle_large_files_in_history(error_output)
    _handle_large_files_staged(error_output)
    _execute_recovery(error_output)
    _show_diff_info()
    _show_recovery_menu(error_output)
    _handle_recovery_choice(choice;error_output)
    _handle_force_push()
    _handle_pull_merge()
    _handle_view_diff()
    _handle_automatic_recovery(error_output)
  goal/push/stages/tag.py:
    e: create_tag
    create_tag(new_version;no_tag)
  goal/push/stages/test.py:
    e: run_test_stage
    run_test_stage(project_types;yes;markdown;ctx_obj;files;stats;current_version;new_version;commit_msg;commit_body)
  goal/push/stages/todo.py:
    e: handle_todo_stage
    handle_todo_stage(ctx_obj;yes;dry_run)
  goal/push/stages/version.py:
    e: _get_version_module,sync_all_versions_wrapper,handle_version_sync,get_version_info
    _get_version_module()
    sync_all_versions_wrapper(new_version;user_config)
    handle_version_sync(new_version;no_version_sync;user_config;yes)
    get_version_info(current_version;bump)
  goal/recovery/__init__.py:
  goal/recovery/auth.py:
    e: AuthErrorStrategy
    AuthErrorStrategy: can_handle(1),recover(1)  # Handles authentication errors.
  goal/recovery/base.py:
    e: RecoveryStrategy
    RecoveryStrategy: __init__(2),can_handle(1),recover(1),run_git(0),run_git_with_output(0)  # Base class for all recovery strategies.
  goal/recovery/corrupted.py:
    e: CorruptedObjectStrategy
    CorruptedObjectStrategy: can_handle(1),recover(1)  # Handles corrupted git objects.
  goal/recovery/divergent.py:
    e: DivergentHistoryStrategy
    DivergentHistoryStrategy: can_handle(1),recover(1),_rebase_changes(1),_merge_changes(1),_pull_changes(0),_force_push(0)  # Handles divergent history errors.
  goal/recovery/exceptions.py:
    e: RecoveryError,AuthError,LargeFileError,DivergentHistoryError,CorruptedObjectError,LFSIssueError,RollbackError,NetworkError,QuotaExceededError
    RecoveryError: __init__(2)  # Base exception for all recovery operations.
    AuthError: __init__(2)  # Raised when authentication fails.
    LargeFileError: __init__(2)  # Raised when large files block the push.
    DivergentHistoryError: __init__(2)  # Raised when local and remote histories have diverged.
    CorruptedObjectError: __init__(2)  # Raised when git objects are corrupted.
    LFSIssueError: __init__(2)  # Raised when Git LFS has issues.
    RollbackError: __init__(2)  # Raised when rollback operation fails.
    NetworkError: __init__(2)  # Raised when network connectivity issues occur.
    QuotaExceededError: __init__(2)  # Raised when GitHub API quota is exceeded.
  goal/recovery/force_push.py:
    e: ForcePushStrategy
    ForcePushStrategy: can_handle(1),recover(1)  # Handles force push recovery scenarios.
  goal/recovery/large_file.py:
    e: _run_git_chunked,LargeFileStrategy
    LargeFileStrategy: __init__(2),can_handle(1),recover(1),_files_in_history(1),_remove_from_history(1),_extract_file_paths(1),_find_large_files(1),_get_file_size_mb(1),_remove_large_files(1),_move_to_lfs(1),_skip_large_files(1)  # Handles large file errors.
    _run_git_chunked(run_git_fn;cmd_base;paths;chunk_size)
  goal/recovery/lfs.py:
    e: LFSIssueStrategy
    LFSIssueStrategy: can_handle(1),recover(1)  # Handles Git LFS issues.
  goal/recovery/manager.py:
    e: RecoveryManager
    RecoveryManager: __init__(2),_ensure_recovery_dir(0),run_git(0),recover_from_push_failure(1),_identify_strategy(1),_create_backup(0),_cleanup_backup(1),_rollback_to_backup(1),_attempt_push(0),setup_clean_clone(0),identify_new_commits(0),cherry_pick_commits(1),push_from_clean_clone(0),full_recovery_workflow(0)  # Manages the recovery process for failed git pushes.
  goal/recovery/strategies.py:
  goal/smart_commit/__init__.py:
  goal/smart_commit/abstraction.py:
    e: CodeAbstraction
    CodeAbstraction: __init__(1),get_domain(1),get_language(1),_added_lines_from_diff(1),_dedupe_entities(1),extract_entities(2),extract_markdown_topics(1),infer_benefit(5),detect_features(2),determine_abstraction_level(1),get_action_verb(1)  # Extracts meaningful abstractions from code changes.
  goal/smart_commit/generator.py:
    e: create_smart_generator,SmartCommitGenerator
    SmartCommitGenerator:  # Generates smart commit messages using code abstraction.
    create_smart_generator(config)
  goal/smart_commit/generator_core.py:
    e: SmartCommitGeneratorCore
    SmartCommitGeneratorCore: __init__(1),deep_analyzer(0),_analyze_file_diffs(2),_merge_deep_analysis(2),analyze_changes(1),_summarize_features(1),_summarize_entities(1),_summarize_documentation(1),_summarize_test_files(2),_fallback_functional_summary(3),_generate_functional_summary(1),_get_staged_files(0),_get_file_diff(1),_infer_commit_type(1)  # Generates smart commit messages using code abstraction.
  goal/smart_commit/generator_generate.py:
    e: SmartCommitGeneratorGenerateMixin
    SmartCommitGeneratorGenerateMixin: generate_message(2),_is_docs_only_change(1),_generate_docs_message(1),_generate_high_abstraction_message(1),_generate_medium_abstraction_message(1),_generate_low_abstraction_message(1),_filter_meaningful_entities(1),_infer_message_from_files(1),generate_functional_body(1),generate_changelog_entry(2),format_changelog_entry(1)
  goal/smart_commit.py:
  goal/summary/__init__.py:
    e: generate_business_summary,validate_summary,auto_fix_summary
    generate_business_summary(files;diff_content;config)
    validate_summary(summary;files;config)
    auto_fix_summary(summary;files;config)
  goal/summary/body_formatter.py:
    e: CommitBodyFormatter
    CommitBodyFormatter: __init__(1),_format_entity_list(3),_split_added_entities(1),_append_file_header(3),_append_added_entities(3),_append_entity_change(3),_format_file_change(5),format_changes_section(2),format_testing_section(1),format_dependencies_section(1),format_stats_section(2),format_body(7)  # Format enhanced commit body sections.
  goal/summary/generator.py:
    e: EnhancedSummaryGenerator
    EnhancedSummaryGenerator: __init__(1),map_entity_to_role(1),_file_stems(1),_special_title_from_files(2),_title_from_capabilities(1),detect_capabilities(2),detect_file_relations(2),_infer_domain(1),_build_relation_chain(1),_render_relations_ascii(2),calculate_quality_metrics(2),generate_value_title(3),generate_enhanced_summary(4),validate_summary_quality(2)  # Generate business-value focused commit summaries.
  goal/summary/quality_filter.py:
    e: SummaryQualityFilter
    SummaryQualityFilter: __init__(0),is_noise(2),filter_entities(1),has_banned_words(1),classify_intent(2),prioritize_capabilities(1),format_complexity_delta(2),dedupe_relations(1),dedupe_files(1),categorize_files(1),filter_generic_nodes(1),format_net_lines(2),_classify_by_churn(2),_classify_by_file_type(1),_score_intent_patterns(1),_resolve_scored_intent(3),classify_intent_smart(4),generate_architecture_title(2)  # Filter noise and improve summary quality.
  goal/summary/validator.py:
    e: QualityValidator
    QualityValidator: __init__(1),validate(2),_extract_intent(2),_validate_title(3),_validate_intent(7),_validate_metrics(3),_validate_relations(3),_validate_files(3),_validate_capabilities(3),_validate_body(3),_validate_value_score(4),_calculate_score(2),_apply_title_fixes(7),_get_entities(1),_fix_banned_words_title(6),_fix_wrong_intent(5),_expand_short_title(6),_clean_relations(1),_apply_relation_fixes(2),_apply_file_dedupe(2),_apply_capability_priority(2),_apply_net_lines(4),_apply_categories(3),auto_fix(4)  # Validate commit summary against quality gates.
  goal/toml_validation.py:
    e: get_tomllib,validate_toml_file,validate_project_toml_files,check_pyproject_toml
    get_tomllib()
    validate_toml_file(filepath)
    validate_project_toml_files(project_dir)
    check_pyproject_toml()
  goal/user_config.py:
    e: get_git_user_name,get_git_user_email,prompt_for_license,initialize_user_config,get_user_config,show_user_config,UserConfig
    UserConfig: __init__(0),_load(0),_save(0),get(2),set(2),is_initialized(0)  # Manages user-specific configuration stored in ~/.goal
    get_git_user_name()
    get_git_user_email()
    prompt_for_license()
    initialize_user_config(force)
    get_user_config()
    show_user_config()
  goal/validation/__init__.py:
  goal/validation/manager.py:
    e: run_custom_validations,ValidationRuleManager
    ValidationRuleManager: __init__(1),get_rules(0),get_validation_context(0),validate_all(0),list_rules(0),validate_config(0)  # Manages custom validation rules for Goal.
    run_custom_validations(project_dir)
  goal/validation/rules.py:
    e: ValidationRule,MessagePatternRule,FilePatternRule,ScriptRule,CommitSizeRule,MessageLengthRule
    ValidationRule: __init__(1),validate(1),get_name(0),validate_config(0)  # Base class for custom validation rules.
    MessagePatternRule: get_name(0),validate_config(0),validate(1)  # Validate commit message against pattern.
    FilePatternRule: get_name(0),validate_config(0),validate(1)  # Validate files against pattern rules.
    ScriptRule: get_name(0),validate_config(0),validate(1)  # Run custom validation script.
    CommitSizeRule: get_name(0),validate_config(0),validate(1)  # Validate commit size (lines changed).
    MessageLengthRule: get_name(0),validate_config(0),validate(1)  # Validate commit message length.
  goal/validators/__init__.py:
  goal/validators/dot_folders.py:
    e: _is_dot_path,_is_safe_path,_is_whitelisted_path,_matches_problematic,check_dot_folders,manage_dot_folders
    _is_dot_path(path)
    _is_safe_path(path)
    _is_whitelisted_path(path;whitelist)
    _matches_problematic(path;problematic_folders)
    check_dot_folders(files;config)
    manage_dot_folders(files;config;dry_run)
  goal/validators/exceptions.py:
    e: ValidationError,FileSizeError,TokenDetectedError,DotFolderError
    ValidationError:  # Base validation error.
    FileSizeError: __init__(3)  # Error for files exceeding size limit.
    TokenDetectedError: __init__(3)  # Error when API tokens are detected in files.
    DotFolderError: __init__(1)  # Error when dot folders are detected that should be in .gitig
  goal/validators/file_validator.py:
    e: get_file_size_mb,_is_excluded,_handle_oversized_file,_check_file_for_tokens,validate_files,handle_large_files,_get_deleted_staged_files,validate_staged_files
    get_file_size_mb(file_path)
    _is_excluded(file_path;exclude_patterns)
    _handle_oversized_file(file_path;size_mb;max_size_mb;auto_handle;block)
    _check_file_for_tokens(file_path;token_patterns)
    validate_files(files;max_size_mb;block_large_files;token_patterns;detect_tokens;exclude_patterns;auto_handle_large)
    handle_large_files(large_files)
    _get_deleted_staged_files()
    validate_staged_files(config)
  goal/validators/gitignore.py:
    e: load_gitignore,save_gitignore
    load_gitignore(gitignore_path)
    save_gitignore(ignored;gitignore_path)
  goal/validators/tokens.py:
    e: _calculate_entropy,_is_dummy_value,_get_entropy_threshold,_classify_token,_extract_token_value,detect_tokens_in_content,resolve_token_patterns,migrate_token_patterns,get_default_token_patterns
    _calculate_entropy(text)
    _is_dummy_value(text)
    _get_entropy_threshold(token_type)
    _classify_token(pattern)
    _extract_token_value(match;line)
    detect_tokens_in_content(content;patterns)
    resolve_token_patterns(patterns)
    migrate_token_patterns(patterns)
    get_default_token_patterns()
  goal/version_validation.py:
    e: get_pypi_version,get_npm_version,get_cargo_version,get_rubygems_version,get_registry_version,extract_badge_versions,update_badge_versions,_detect_python_package,_detect_nodejs_package,_detect_rust_package,_detect_ruby_package,_validate_single_type,validate_project_versions,check_readme_badges,format_validation_results
    get_pypi_version(package_name)
    get_npm_version(package_name)
    get_cargo_version(package_name)
    get_rubygems_version(package_name)
    get_registry_version(registry;package_name)
    extract_badge_versions(readme_path)
    update_badge_versions(readme_path;new_version)
    _detect_python_package()
    _detect_nodejs_package()
    _detect_rust_package()
    _detect_ruby_package()
    _validate_single_type(project_type;current_version)
    validate_project_versions(project_types;current_version)
    check_readme_badges(current_version)
    format_validation_results(results)
  test_recovery.py:
    e: test_strategy_detection,test_recovery_manager,main
    test_strategy_detection()
    test_recovery_manager()
    main()
  tests/conftest.py:
  tests/test_changelog.py:
    e: test_update_changelog_creates_new_file,test_update_changelog_appends_to_existing,test_update_changelog_with_domain_grouping,test_update_changelog_limits_files,test_update_changelog_with_unreleased_section
    test_update_changelog_creates_new_file()
    test_update_changelog_appends_to_existing()
    test_update_changelog_with_domain_grouping()
    test_update_changelog_limits_files()
    test_update_changelog_with_unreleased_section()
  tests/test_cli_options.py:
    e: run_cli,test_push_help_includes_markdown_ascii_split_ticket,test_status_help_includes_markdown_ascii,test_unknown_command_shows_docs_url,test_known_commands_work,test_all_help_does_not_fail_when_push_unavailable,test_missing_push_command_shows_install_hint,test_goal_update_command_prefers_active_venv_python,test_version_banner_includes_ready_to_run_update_command,test_warn_goal_binary_mismatch_detects_local_venv_without_active_virtual_env,test_warn_goal_binary_mismatch_prefers_local_goal_binary_hint
    run_cli()
    test_push_help_includes_markdown_ascii_split_ticket()
    test_status_help_includes_markdown_ascii()
    test_unknown_command_shows_docs_url()
    test_known_commands_work()
    test_all_help_does_not_fail_when_push_unavailable()
    test_missing_push_command_shows_install_hint()
    test_goal_update_command_prefers_active_venv_python(monkeypatch)
    test_version_banner_includes_ready_to_run_update_command(monkeypatch;capsys)
    test_warn_goal_binary_mismatch_detects_local_venv_without_active_virtual_env(monkeypatch;tmp_path;capsys)
    test_warn_goal_binary_mismatch_prefers_local_goal_binary_hint(monkeypatch;tmp_path;capsys)
  tests/test_cli_tests_runner.py:
    e: test_find_python_test_dirs_deduplicates_project_roots_and_prefers_tests_dir,test_resolve_project_python_returns_absolute_project_python,test_ensure_pytest_for_project_tries_multiple_install_strategies,test_active_venv_python_is_preferred_for_root_run,test_run_tests_uses_configured_python_strategy_and_skips_subdir_scan,test_rewrite_bash_pytest_for_uv_converts_goal_yaml_style_command,test_build_python_test_command_prefers_venv_pytest_when_importable,test_get_test_execution_details_and_planfile_update
    test_find_python_test_dirs_deduplicates_project_roots_and_prefers_tests_dir(tmp_path;monkeypatch)
    test_resolve_project_python_returns_absolute_project_python()
    test_ensure_pytest_for_project_tries_multiple_install_strategies()
    test_active_venv_python_is_preferred_for_root_run(monkeypatch)
    test_run_tests_uses_configured_python_strategy_and_skips_subdir_scan()
    test_rewrite_bash_pytest_for_uv_converts_goal_yaml_style_command()
    test_build_python_test_command_prefers_venv_pytest_when_importable(monkeypatch)
    test_get_test_execution_details_and_planfile_update(tmp_path;monkeypatch)
  tests/test_clone_repo.py:
    e: TestValidateRepoUrl,TestIsGitRepository,TestCloneRepository,TestEnsureGitRepository,TestCloneCommand
    TestValidateRepoUrl: test_valid_http_urls(1),test_valid_ssh_urls(1),test_invalid_urls(1),test_whitespace_is_stripped(0)  # Tests for URL validation (HTTP/HTTPS/SSH).
    TestIsGitRepository: test_true_inside_git_repo(1),test_false_outside_git_repo(1)
    TestCloneRepository: test_invalid_url_returns_failure(0),test_clone_success(1),test_clone_failure_bad_remote(1)
    TestEnsureGitRepository: test_returns_true_when_already_in_repo(1),test_exit_option(1),test_auto_mode_skips(1),test_init_option(1),test_clone_option_with_valid_url(1),test_clone_option_invalid_url(1),test_init_and_add_remote(1)
    TestCloneCommand: test_clone_help(0),test_clone_invalid_url(0),test_clone_valid_local_bare(1)
  tests/test_config_shim.py:
    e: test_config_shim_exports,test_all_exports
    test_config_shim_exports()
    test_all_exports()
  tests/test_config_validation.py:
    e: TestConfigValidator,TestAutoFixConfig,TestConfigValidationError
    TestConfigValidator: test_valid_default_config(0),test_missing_required_section(0),test_invalid_project_type(0),test_invalid_commit_type(0),test_invalid_version_strategy(0),test_wrong_type_bool(0),test_coverage_threshold_range(0),test_strict_mode_treats_warnings_as_errors(0),test_unknown_keys_warning(0)  # Test configuration validator.
    TestAutoFixConfig: test_fix_branch_prefix(0),test_fix_tag_format(0)  # Test configuration auto-fix functionality.
    TestConfigValidationError: test_error_message_formatting(0)  # Test ConfigValidationError exception.
  tests/test_dependency_update.py:
    e: test_get_update_all_command_for_uv,test_get_update_all_command_for_pip_with_requirements,test_get_update_all_command_for_go,test_select_managers_uses_only_highest_priority_python_lockfile,test_select_managers_uv_only_without_poetry_lock,test_select_managers_prefers_lockfile_manager,test_update_project_dependencies_dry_run,test_update_project_dependencies_runs_detected_manager,test_has_cli_flag_detects_combined_short_options,test_discover_dependency_project_roots_finds_subprojects,test_discover_dependency_project_roots_respects_recursive_flag,test_aur_sets_recursive_and_upgrade_deps_in_context,test_interactive_skips_declined_projects,test_auto_mode_processes_all_projects_without_prompts,test_aiu_sets_interactive_in_context,test_ar_sets_recursive_in_context,test_upgrade_deps_runs_before_bootstrap,test_au_sets_upgrade_deps_in_context,test_au_sets_markdown_in_context,test_all_with_ascii_keeps_ascii_output
    test_get_update_all_command_for_uv()
    test_get_update_all_command_for_pip_with_requirements(tmp_path)
    test_get_update_all_command_for_go()
    test_select_managers_uses_only_highest_priority_python_lockfile(tmp_path;monkeypatch)
    test_select_managers_uv_only_without_poetry_lock(tmp_path;monkeypatch)
    test_select_managers_prefers_lockfile_manager(tmp_path;monkeypatch)
    test_update_project_dependencies_dry_run(tmp_path;monkeypatch)
    test_update_project_dependencies_runs_detected_manager(tmp_path;monkeypatch)
    test_has_cli_flag_detects_combined_short_options()
    test_discover_dependency_project_roots_finds_subprojects(tmp_path;monkeypatch)
    test_discover_dependency_project_roots_respects_recursive_flag(tmp_path;monkeypatch)
    test_aur_sets_recursive_and_upgrade_deps_in_context()
    test_interactive_skips_declined_projects(tmp_path;monkeypatch)
    test_auto_mode_processes_all_projects_without_prompts(tmp_path;monkeypatch)
    test_aiu_sets_interactive_in_context()
    test_ar_sets_recursive_in_context()
    test_upgrade_deps_runs_before_bootstrap(monkeypatch)
    test_au_sets_upgrade_deps_in_context()
    test_au_sets_markdown_in_context()
    test_all_with_ascii_keeps_ascii_output()
  tests/test_detect_version_files.py:
    e: _detect_in,test_skips_venv_and_site_packages,test_skips_build_and_node_modules,test_monorepo_detects_nested_manifest,test_skips_example_and_fixture_manifests,test_prefers_shallowest_package
    _detect_in(tmp_path)
    test_skips_venv_and_site_packages(tmp_path)
    test_skips_build_and_node_modules(tmp_path)
    test_monorepo_detects_nested_manifest(tmp_path)
    test_skips_example_and_fixture_manifests(tmp_path)
    test_prefers_shallowest_package(tmp_path)
  tests/test_file_validation.py:
    e: test_file_size_validation,test_token_detection,test_safe_files,test_false_positive_prevention,test_symlink_to_directory_is_skipped,test_config_integration,main
    test_file_size_validation()
    test_token_detection()
    test_safe_files()
    test_false_positive_prevention()
    test_symlink_to_directory_is_skipped(tmp_path)
    test_config_integration()
    main()
  tests/test_formatter.py:
    e: test_markdown_formatter_basic,test_markdown_formatter_with_metadata,test_markdown_formatter_section,test_markdown_formatter_code_block,test_markdown_formatter_list,test_markdown_formatter_ordered_list,test_markdown_formatter_command_output,test_markdown_formatter_command_failed,test_markdown_formatter_summary,test_build_functional_overview,test_build_functional_overview_single_feature,test_build_functional_overview_no_features,test_determine_next_steps_success,test_determine_next_steps_test_failure,test_determine_next_steps_error,test_format_status_output,test_format_status_output_many_unstaged,test_format_push_result,test_format_push_result_with_error,test_format_goal_all_summary_markdown
    test_markdown_formatter_basic()
    test_markdown_formatter_with_metadata()
    test_markdown_formatter_section()
    test_markdown_formatter_code_block()
    test_markdown_formatter_list()
    test_markdown_formatter_ordered_list()
    test_markdown_formatter_command_output()
    test_markdown_formatter_command_failed()
    test_markdown_formatter_summary()
    test_build_functional_overview()
    test_build_functional_overview_single_feature()
    test_build_functional_overview_no_features()
    test_determine_next_steps_success()
    test_determine_next_steps_test_failure()
    test_determine_next_steps_error()
    test_format_status_output()
    test_format_status_output_many_unstaged()
    test_format_push_result()
    test_format_push_result_with_error()
    test_format_goal_all_summary_markdown()
  tests/test_git_ops.py:
    e: test_validate_repo_url_ssh,test_validate_repo_url_https,test_validate_repo_url_invalid,test_apply_ticket_prefix_with_ticket,test_apply_ticket_prefix_no_ticket,test_read_ticket_file_not_exists,test_read_ticket_file_exists,test_get_diff_stats_empty,test_get_diff_stats_with_changes,test_get_diff_content_small,test_get_diff_content_large,test_get_staged_files_empty,test_get_staged_files_with_files,test_get_unstaged_files,test_is_git_repository_true,test_is_git_repository_false
    test_validate_repo_url_ssh()
    test_validate_repo_url_https()
    test_validate_repo_url_invalid()
    test_apply_ticket_prefix_with_ticket()
    test_apply_ticket_prefix_no_ticket()
    test_read_ticket_file_not_exists()
    test_read_ticket_file_exists()
    test_get_diff_stats_empty()
    test_get_diff_stats_with_changes()
    test_get_diff_content_small()
    test_get_diff_content_large()
    test_get_staged_files_empty()
    test_get_staged_files_with_files()
    test_get_unstaged_files()
    test_is_git_repository_true()
    test_is_git_repository_false()
  tests/test_github_fallback.py:
    e: TestBlockedDetection,TestGitHubConfig,TestPublishFallbackOnBlock
    TestBlockedDetection: test_429_is_blocked(0),test_403_is_blocked(0),test_auth_error_is_blocked(0)
    TestGitHubConfig: test_disabled_when_explicit_off(0),test_repo_map_resolution(0),test_detect_github_remote(0)
    TestPublishFallbackOnBlock: test_429_skips_pypi_retries_when_github_actionable(2),test_429_retries_when_github_not_actionable(0),test_publish_github_release_uploads_assets(2),test_try_github_fallback_noop_when_not_blocked(0)
  tests/test_installers_e2e.py:
    e: TestPackageManagerBrokerE2E,TestInstallResult,TestBootstrapIntegration,TestDoctorIntegration,TestLockfilePriority,TestUvManagerReal,TestPoetryManagerReal,TestPdmManagerReal
    TestPackageManagerBrokerE2E: test_broker_detects_available_managers(0),test_broker_detects_lockfile_uv(1),test_broker_detects_lockfile_poetry(1),test_broker_detects_lockfile_pdm(1),test_broker_no_lockfile(1),test_uv_manager_priority(0),test_pdm_manager_priority(0),test_poetry_manager_priority(0),test_pip_manager_priority(0),test_uv_manager_is_available_when_uv_installed(0),test_pip_manager_always_available(0),test_manager_registry_order(0)  # E2E tests for broker functionality.
    TestInstallResult: test_install_result_success(0),test_install_result_failure(0)  # Tests for InstallResult data class.
    TestBootstrapIntegration: test_bootstrap_imports_broker(0),test_bootstrap_uses_new_installer(1),test_legacy_bootstrap_compatibility(0)  # Integration tests with bootstrap module.
    TestDoctorIntegration: test_doctor_imports_broker(0)  # Integration tests with doctor command.
    TestLockfilePriority: test_uv_lockfile_triggers_uv_manager(1),test_poetry_lockfile_triggers_poetry_manager(1)  # Tests for lockfile-based manager selection.
    TestUvManagerReal: test_uv_manager_detects_uv(0),test_uv_manager_install_editable_mock(1)  # Tests requiring real uv installation.
    TestPoetryManagerReal: test_poetry_manager_detects_poetry(0)  # Tests requiring real poetry installation.
    TestPdmManagerReal: test_pdm_manager_detects_pdm(0)  # Tests requiring real pdm installation.
  tests/test_project_bootstrap.py:
    e: _write_pyproject,test_pfix_auto_apply_defaults_true,test_pfix_auto_apply_false_is_respected,test_run_bootstrap_diagnostics_gated_by_auto_apply,test_auto_fix_enabled_reads_goal_yaml,test_auto_fix_enabled_env_override,TestMatchMarker,TestDetectProjectTypesDeep,TestGuessPackageName,TestFindExistingTests,TestScaffoldTest,TestEnsureProjectEnvironmentPython,TestEnsureProjectEnvironmentGeneric,TestOpenRouterEnvDiscovery,TestPythonTestDependency,TestPfixInstallSource,TestCostsBadgeGeneration,TestBootstrapProject,TestBootstrapAllProjects,TestBootstrapCommand,TestProjectBootstrapConfig
    TestMatchMarker: test_exact_file(1),test_glob_pattern(1)
    TestDetectProjectTypesDeep: test_root_python(1),test_subfolder_nodejs(1),test_ignores_hidden_dirs(1),test_multiple_types(1),test_empty_dir(1),test_rust_in_subfolder(1),test_java_gradle(1),test_dotnet_csproj(1)
    TestGuessPackageName: test_python_from_pyproject(1),test_nodejs_from_package_json(1),test_rust_from_cargo(1),test_go_from_gomod(1),test_fallback_to_dirname(1),test_test_harness_uses_directory_name(1)
    TestFindExistingTests: test_finds_python_tests(1),test_finds_nodejs_tests(1),test_no_tests_returns_empty(1),test_finds_go_tests(1),test_finds_ruby_specs(1)
    TestScaffoldTest: test_creates_python_test(1),test_creates_nodejs_test(1),test_creates_rust_test(1),test_creates_go_test(1),test_creates_ruby_spec(1),test_creates_php_test(1),test_creates_dotnet_test(1),test_creates_java_test(1),test_skips_when_tests_exist(1),test_scaffold_in_tests_project_avoids_nested_dir(1),test_skips_unknown_type(1),test_interactive_decline(1)
    TestEnsureProjectEnvironmentPython: test_creates_venv_and_installs(1),test_skips_if_venv_exists(1),test_interactive_decline(1)
    TestEnsureProjectEnvironmentGeneric: test_unknown_type_returns_true(1),test_nodejs_with_missing_npm(1)
    TestOpenRouterEnvDiscovery: test_finds_parent_env_over_blank_local_env(1),test_does_not_create_local_env_when_parent_key_exists(1),test_creates_llm_model_template_when_no_api_key_exists(1)
    TestPythonTestDependency: test_installs_missing_pytest(1)
    TestPfixInstallSource: test_installs_pfix_from_pypi_by_default(1),test_installs_pfix_from_local_path_when_configured(1)
    TestCostsBadgeGeneration: test_uses_git_root_for_subproject_analysis(1)
    TestBootstrapProject: test_full_bootstrap_python(1),test_bootstrap_with_existing_tests(1)
    TestBootstrapAllProjects: test_detects_and_bootstraps(1),test_empty_dir(1)
    TestBootstrapCommand: test_bootstrap_help(0),test_bootstrap_empty_dir(1),test_bootstrap_python_project(1)
    TestProjectBootstrapConfig: test_required_keys(1)
    _write_pyproject(tmp_path;body)
    test_pfix_auto_apply_defaults_true(tmp_path)
    test_pfix_auto_apply_false_is_respected(tmp_path)
    test_run_bootstrap_diagnostics_gated_by_auto_apply(tmp_path;monkeypatch)
    test_auto_fix_enabled_reads_goal_yaml(tmp_path)
    test_auto_fix_enabled_env_override(tmp_path;monkeypatch)
  tests/test_project_bootstrap_costs.py:
    e: test_calculate_ai_costs_uses_commit_diff_tuple_and_message_filter
    test_calculate_ai_costs_uses_commit_diff_tuple_and_message_filter()
  tests/test_project_doctor.py:
    e: TestDoctorReport,TestDiagnosePython,TestDiagnoseNodejs,TestDiagnoseRust,TestDiagnoseGo,TestDiagnoseRuby,TestDiagnosePhp,TestDiagnoseDotnet,TestDiagnoseJava,TestDiagnoseProject,TestDiagnoseAndReport,TestDoctorCommand
    TestDoctorReport: test_properties(0),test_no_problems(0)
    TestDiagnosePython: test_no_pyproject(1),test_only_requirements_txt(1),test_missing_build_system(1),test_missing_build_system_no_fix(1),test_deprecated_license_classifier(1),test_broken_backend(1),test_license_table_format(1),test_duplicate_authors(1),test_missing_requires_python(1),test_healthy_project(1),test_string_format_authors(1)
    TestDiagnoseNodejs: test_no_package_json(1),test_invalid_json(1),test_missing_version(1),test_missing_test_script(1),test_no_test_specified(1),test_healthy_nodejs(1)
    TestDiagnoseRust: test_no_cargo(1),test_missing_package(1),test_missing_edition(1)
    TestDiagnoseGo: test_no_gomod(1),test_invalid_gomod(1),test_missing_gosum(1)
    TestDiagnoseRuby: test_no_gemfile(1),test_missing_lock(1)
    TestDiagnosePhp: test_no_composer(1),test_invalid_json(1),test_missing_autoload(1)
    TestDiagnoseDotnet: test_no_csproj(1),test_missing_target_framework(1)
    TestDiagnoseJava: test_no_build_file(1),test_missing_model_version(1)
    TestDiagnoseProject: test_unknown_type(1),test_python_dispatch(1)
    TestDiagnoseAndReport: test_prints_report(1),test_healthy_project(1)
    TestDoctorCommand: test_doctor_help(0),test_doctor_empty_dir(1),test_doctor_finds_python_issues(1),test_doctor_no_fix(1),test_doctor_with_fix(1)
  tests/test_publish_changes.py:
    e: TestAnalyzePublishableChanges
    TestAnalyzePublishableChanges: test_detects_python_source_changes(0),test_skips_metadata_only_python_changes(0),test_skips_docs_and_tests(0),test_detects_node_source_changes(0),test_no_registry_types(0),test_detects_nested_subproject_source(0),test_lockfile_only_changes_are_not_publishable(0)
  tests/test_publish_pattern.py:
    e: test_resolve_python_publish_cmd_uses_pyproject_name,test_resolve_python_publish_cmd_uses_setup_py_name,test_resolve_python_publish_cmd_filters_broad_dist_glob,test_ensure_python_artifacts_resyncs_setup_py_and_rebuilds,test_goal_config_reload_reads_updated_goal_yaml
    test_resolve_python_publish_cmd_uses_pyproject_name(tmp_path;monkeypatch)
    test_resolve_python_publish_cmd_uses_setup_py_name(tmp_path;monkeypatch)
    test_resolve_python_publish_cmd_filters_broad_dist_glob(tmp_path;monkeypatch)
    test_ensure_python_artifacts_resyncs_setup_py_and_rebuilds(tmp_path;monkeypatch)
    test_goal_config_reload_reads_updated_goal_yaml(tmp_path;monkeypatch)
  tests/test_push_e2e.py:
    e: TestPublishRetry,TestWorkflowOrder,TestPushWorkflowImports,TestPushWorkflowIntegration,TestPushWorkflowE2E
    TestPublishRetry: test_retries_on_429_then_succeeds(0),test_gives_up_after_max_retries_on_429(0),test_no_retry_on_non_429_failure(0),test_is_rate_limited_detection(0)  # Tests for 429 rate-limit retry logic in _run_publish_command
    TestWorkflowOrder: test_publish_runs_before_tag_and_push(0),test_metadata_only_changes_skip_publish_but_still_tag_and_push(0),test_auto_publish_failure_aborts_before_tag_and_push(0)  # Tests that publish happens before tag+push in the workflow.
    TestPushWorkflowImports: test_push_stages_commit_imports(0),test_push_stages_version_imports(0),test_push_stages_changelog_imports(0),test_push_stages_test_imports(0),test_push_stages_tag_imports(0),test_push_stages_push_remote_imports(0),test_push_stages_publish_imports(0),test_push_stages_dry_run_imports(0),test_push_core_imports(0),test_push_commands_import(0),test_push_package_import(0),test_push_cmd_shim(0)  # Test that all push workflow imports work correctly.
    TestPushWorkflowIntegration: test_version_info_returns_tuple(0),test_format_changes_section(0),test_build_functional_overview_with_features(0),test_build_functional_overview_fallback(0)  # Integration tests for push workflow stages.
    TestPushWorkflowE2E: test_push_workflow_dry_run(1),test_push_stages_handle_empty_inputs(0),test_push_command_forwards_no_publish_flag(0),test_push_workflow_aborts_on_auto_test_failure(0),test_commit_phase_refreshes_costs_before_single_commit(0),test_publish_project_skips_nodejs_publish_when_not_configured(0),test_publish_project_runs_nodejs_publish_when_configured(0),test_publish_command_falls_back_when_make_publish_fails(0),test_run_tests_ignores_top_level_tests_dir_as_subdir(0),test_publish_command_imports_all_required_modules(0)  # End-to-end tests for the complete push workflow.
  tests/test_push_todo_stage.py:
    e: test_todo_stage_returns_false_when_prefact_missing,test_todo_stage_returns_false_on_prefact_nonzero_exit,test_todo_stage_stages_existing_artifacts
    test_todo_stage_returns_false_when_prefact_missing()
    test_todo_stage_returns_false_on_prefact_nonzero_exit()
    test_todo_stage_stages_existing_artifacts(tmp_path;monkeypatch)
  tests/test_smart_commit_shim.py:
    e: test_shim_imports,test_all_exports
    test_shim_imports()
    test_all_exports()
  tests/test_token_validator_patterns.py:
    e: test_urisys_nightly_session_env_is_not_flagged,test_legacy_patterns_are_removed_on_resolve,test_migrate_token_patterns_reports_changes,test_credential_env_assignments_are_still_flagged
    test_urisys_nightly_session_env_is_not_flagged()
    test_legacy_patterns_are_removed_on_resolve()
    test_migrate_token_patterns_reports_changes()
    test_credential_env_assignments_are_still_flagged()
  tests/test_user_config.py:
    e: test_user_config_load_existing,test_user_config_save,test_user_config_is_initialized,test_get_git_user_name,test_get_git_user_name_failure,test_get_git_user_email,test_available_licenses,test_user_config_get_default
    test_user_config_load_existing()
    test_user_config_save()
    test_user_config_is_initialized()
    test_get_git_user_name()
    test_get_git_user_name_failure()
    test_get_git_user_email()
    test_available_licenses()
    test_user_config_get_default()
  tests/test_version_sync.py:
    e: test_sync_updates_init_py,test_sync_skips_example_and_fixture_init,test_python_publish_command_skips_existing,test_sync_updates_setup_py_version,test_sync_updates_uv_lock_after_pyproject_version_change,test_sync_refreshes_detected_dependency_lockfiles,test_bump_version_pre_release_formats
    test_sync_updates_init_py(tmp_path)
    test_sync_skips_example_and_fixture_init(tmp_path)
    test_python_publish_command_skips_existing()
    test_sync_updates_setup_py_version(tmp_path;monkeypatch)
    test_sync_updates_uv_lock_after_pyproject_version_change(tmp_path;monkeypatch)
    test_sync_refreshes_detected_dependency_lockfiles(tmp_path;monkeypatch;manifest;manifest_text;lockfile;command)
    test_bump_version_pre_release_formats(version;bump_type;expected)
  tests/test_version_validation.py:
    e: TestVersionValidation
    TestVersionValidation: setUp(0),test_extract_badge_versions(0),test_update_badge_versions(0),test_check_readme_badges(0),test_check_readme_badges_up_to_date(0),test_check_readme_no_file(0),test_get_pypi_version_success(1),test_get_pypi_version_failure(1),test_get_npm_version_success(1),test_get_cargo_version_success(1),test_get_rubygems_version_success(1),test_validate_python_project(2),test_validate_nodejs_project(3),test_format_validation_results(0)
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('goal', '2.1.257', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 249, 'less').
project_file('examples/api-usage/01_basic_api.py', 75, 'python').
project_file('examples/api-usage/02_git_operations.py', 101, 'python').
project_file('examples/api-usage/03_commit_generation.py', 71, 'python').
project_file('examples/api-usage/04_version_validation.py', 80, 'python').
project_file('examples/api-usage/05_programmatic_workflow.py', 121, 'python').
project_file('examples/api-usage/test_integration.py', 250, 'python').
project_file('examples/custom-hooks/post-commit.py', 145, 'python').
project_file('examples/custom-hooks/pre-commit.py', 129, 'python').
project_file('examples/custom-hooks/pre-publish.py', 168, 'python').
project_file('examples/git-hooks/install.sh', 32, 'shell').
project_file('examples/go-project/main.go', 11, 'go').
project_file('examples/markdown-demo.sh', 71, 'shell').
project_file('examples/my-new-project/src/my-new-project/__init__.py', 4, 'python').
project_file('examples/my-new-project/tests/test_my-new-project.py', 3, 'python').
project_file('examples/template-generator/generate.py', 241, 'python').
project_file('examples/testing/03_advanced_mocking.py', 284, 'python').
project_file('examples/testing/04_debugging_diagnostics.py', 302, 'python').
project_file('examples/validation/run_all_validation.py', 121, 'python').
project_file('examples/validation/test_api_signatures.py', 290, 'python').
project_file('examples/validation/test_imports.py', 207, 'python').
project_file('examples/validation/test_readme_consistency.py', 295, 'python').
project_file('examples/validation/test_syntax_check.py', 212, 'python').
project_file('examples/webhooks/discord-webhook.py', 110, 'python').
project_file('examples/webhooks/slack-webhook.py', 117, 'python').
project_file('goal/__init__.py', 4, 'python').
project_file('goal/__main__.py', 19, 'python').
project_file('goal/authors/__init__.py', 20, 'python').
project_file('goal/authors/manager.py', 349, 'python').
project_file('goal/authors/utils.py', 218, 'python').
project_file('goal/bootstrap/__init__.py', 12, 'python').
project_file('goal/bootstrap/configurator.py', 143, 'python').
project_file('goal/bootstrap/costs_badge.py', 246, 'python').
project_file('goal/bootstrap/detector.py', 150, 'python').
project_file('goal/bootstrap/installer.py', 392, 'python').
project_file('goal/bootstrap/pyproject_costs_setup.py', 235, 'python').
project_file('goal/bootstrap/templates.py', 195, 'python').
project_file('goal/changelog.py', 130, 'python').
project_file('goal/cli/__init__.py', 474, 'python').
project_file('goal/cli/authors_cmd.py', 128, 'python').
project_file('goal/cli/commit_cmd.py', 229, 'python').
project_file('goal/cli/config_cmd.py', 126, 'python').
project_file('goal/cli/config_validate_cmd.py', 48, 'python').
project_file('goal/cli/doctor_cmd.py', 126, 'python').
project_file('goal/cli/hooks_cmd.py', 88, 'python').
project_file('goal/cli/license_cmd.py', 207, 'python').
project_file('goal/cli/postcommit_cmd.py', 83, 'python').
project_file('goal/cli/publish.py', 619, 'python').
project_file('goal/cli/publish_cmd.py', 67, 'python').
project_file('goal/cli/push_cmd.py', 154, 'python').
project_file('goal/cli/recover_cmd.py', 133, 'python').
project_file('goal/cli/tests.py', 518, 'python').
project_file('goal/cli/tests_discovery.py', 108, 'python').
project_file('goal/cli/tests_pytest_setup.py', 132, 'python').
project_file('goal/cli/utils_cmd.py', 230, 'python').
project_file('goal/cli/validation_cmd.py', 86, 'python').
project_file('goal/cli/version.py', 36, 'python').
project_file('goal/cli/version_sync.py', 333, 'python').
project_file('goal/cli/version_types.py', 136, 'python').
project_file('goal/cli/version_utils.py', 486, 'python').
project_file('goal/cli/wizard_cmd.py', 368, 'python').
project_file('goal/cli.py', 17, 'python').
project_file('goal/cli_helpers.py', 98, 'python').
project_file('goal/commit_generator.py', 36, 'python').
project_file('goal/config/__init__.py', 37, 'python').
project_file('goal/config/constants.py', 481, 'python').
project_file('goal/config/manager.py', 551, 'python').
project_file('goal/config/validation.py', 557, 'python').
project_file('goal/config.py', 25, 'python').
project_file('goal/deep_analyzer.py', 305, 'python').
project_file('goal/deep_analyzer_aggregate.py', 281, 'python').
project_file('goal/deep_analyzer_patterns.py', 64, 'python').
project_file('goal/dependency_update.py', 341, 'python').
project_file('goal/doctor/__init__.py', 56, 'python').
project_file('goal/doctor/core.py', 94, 'python').
project_file('goal/doctor/dotnet.py', 32, 'python').
project_file('goal/doctor/go.py', 42, 'python').
project_file('goal/doctor/java.py', 40, 'python').
project_file('goal/doctor/logging.py', 30, 'python').
project_file('goal/doctor/models.py', 48, 'python').
project_file('goal/doctor/nodejs.py', 92, 'python').
project_file('goal/doctor/php.py', 55, 'python').
project_file('goal/doctor/python.py', 45, 'python').
project_file('goal/doctor/python_diag_core.py', 339, 'python').
project_file('goal/doctor/python_diag_extended.py', 394, 'python').
project_file('goal/doctor/ruby.py', 29, 'python').
project_file('goal/doctor/rust.py', 42, 'python').
project_file('goal/doctor/todo.py', 145, 'python').
project_file('goal/enhanced_summary.py', 24, 'python').
project_file('goal/formatter.py', 519, 'python').
project_file('goal/generator/__init__.py', 15, 'python').
project_file('goal/generator/analyzer.py', 564, 'python').
project_file('goal/generator/generator.py', 433, 'python').
project_file('goal/generator/git_ops.py', 178, 'python').
project_file('goal/git_ops.py', 691, 'python').
project_file('goal/hooks/__init__.py', 20, 'python').
project_file('goal/hooks/config.py', 107, 'python').
project_file('goal/hooks/manager.py', 314, 'python').
project_file('goal/installers/__init__.py', 10, 'python').
project_file('goal/installers/broker.py', 159, 'python').
project_file('goal/installers/config.py', 45, 'python').
project_file('goal/installers/managers/__init__.py', 17, 'python').
project_file('goal/installers/managers/base.py', 61, 'python').
project_file('goal/installers/managers/pdm.py', 30, 'python').
project_file('goal/installers/managers/pip.py', 29, 'python').
project_file('goal/installers/managers/poetry.py', 33, 'python').
project_file('goal/installers/managers/uv.py', 38, 'python').
project_file('goal/io/__init__.py', 30, 'python').
project_file('goal/io/stdio.py', 87, 'python').
project_file('goal/license/__init__.py', 21, 'python').
project_file('goal/license/manager.py', 588, 'python').
project_file('goal/license/spdx.py', 284, 'python').
project_file('goal/package_managers.py', 645, 'python').
project_file('goal/postcommit/__init__.py', 28, 'python').
project_file('goal/postcommit/actions.py', 240, 'python').
project_file('goal/postcommit/manager.py', 212, 'python').
project_file('goal/project_bootstrap.py', 1275, 'python').
project_file('goal/project_doctor.py', 44, 'python').
project_file('goal/publish/__init__.py', 6, 'python').
project_file('goal/publish/changes.py', 239, 'python').
project_file('goal/publish/github_fallback.py', 317, 'python').
project_file('goal/push/__init__.py', 57, 'python').
project_file('goal/push/commands.py', 77, 'python').
project_file('goal/push/core.py', 899, 'python').
project_file('goal/push/stages/__init__.py', 37, 'python').
project_file('goal/push/stages/changelog.py', 25, 'python').
project_file('goal/push/stages/commit.py', 304, 'python').
project_file('goal/push/stages/costs.py', 131, 'python').
project_file('goal/push/stages/dry_run.py', 152, 'python').
project_file('goal/push/stages/publish.py', 128, 'python').
project_file('goal/push/stages/push_remote.py', 474, 'python').
project_file('goal/push/stages/tag.py', 33, 'python').
project_file('goal/push/stages/test.py', 92, 'python').
project_file('goal/push/stages/todo.py', 101, 'python').
project_file('goal/push/stages/version.py', 57, 'python').
project_file('goal/recovery/__init__.py', 49, 'python').
project_file('goal/recovery/auth.py', 84, 'python').
project_file('goal/recovery/base.py', 51, 'python').
project_file('goal/recovery/corrupted.py', 58, 'python').
project_file('goal/recovery/divergent.py', 130, 'python').
project_file('goal/recovery/exceptions.py', 79, 'python').
project_file('goal/recovery/force_push.py', 52, 'python').
project_file('goal/recovery/large_file.py', 398, 'python').
project_file('goal/recovery/lfs.py', 60, 'python').
project_file('goal/recovery/manager.py', 347, 'python').
project_file('goal/recovery/strategies.py', 24, 'python').
project_file('goal/smart_commit/__init__.py', 15, 'python').
project_file('goal/smart_commit/abstraction.py', 279, 'python').
project_file('goal/smart_commit/generator.py', 16, 'python').
project_file('goal/smart_commit/generator_core.py', 268, 'python').
project_file('goal/smart_commit/generator_generate.py', 279, 'python').
project_file('goal/smart_commit.py', 21, 'python').
project_file('goal/summary/__init__.py', 43, 'python').
project_file('goal/summary/body_formatter.py', 215, 'python').
project_file('goal/summary/generator.py', 590, 'python').
project_file('goal/summary/quality_filter.py', 390, 'python').
project_file('goal/summary/validator.py', 490, 'python').
project_file('goal/toml_validation.py', 118, 'python').
project_file('goal/user_config.py', 324, 'python').
project_file('goal/validation/__init__.py', 28, 'python').
project_file('goal/validation/manager.py', 208, 'python').
project_file('goal/validation/rules.py', 253, 'python').
project_file('goal/validators/__init__.py', 58, 'python').
project_file('goal/validators/dot_folders.py', 162, 'python').
project_file('goal/validators/exceptions.py', 47, 'python').
project_file('goal/validators/file_validator.py', 304, 'python').
project_file('goal/validators/gitignore.py', 50, 'python').
project_file('goal/validators/tokens.py', 287, 'python').
project_file('goal/version_validation.py', 342, 'python').
project_file('integration/run_docker_matrix.sh', 6, 'shell').
project_file('integration/run_matrix.sh', 217, 'shell').
project_file('project.sh', 48, 'shell').
project_file('scripts/koru_verify_ci.sh', 50, 'shell').
project_file('test_recovery.py', 128, 'python').
project_file('tests/conftest.py', 12, 'python').
project_file('tests/test_changelog.py', 137, 'python').
project_file('tests/test_cli_options.py', 140, 'python').
project_file('tests/test_cli_tests_runner.py', 213, 'python').
project_file('tests/test_clone_repo.py', 287, 'python').
project_file('tests/test_config_shim.py', 30, 'python').
project_file('tests/test_config_validation.py', 160, 'python').
project_file('tests/test_dependency_update.py', 495, 'python').
project_file('tests/test_detect_version_files.py', 106, 'python').
project_file('tests/test_file_validation.py', 254, 'python').
project_file('tests/test_formatter.py', 257, 'python').
project_file('tests/test_git_ops.py', 183, 'python').
project_file('tests/test_github_fallback.py', 213, 'python').
project_file('tests/test_installers_e2e.py', 246, 'python').
project_file('tests/test_project_bootstrap.py', 806, 'python').
project_file('tests/test_project_bootstrap_costs.py', 29, 'python').
project_file('tests/test_project_doctor.py', 436, 'python').
project_file('tests/test_publish_changes.py', 57, 'python').
project_file('tests/test_publish_pattern.py', 122, 'python').
project_file('tests/test_push_e2e.py', 755, 'python').
project_file('tests/test_push_todo_stage.py', 52, 'python').
project_file('tests/test_smart_commit_shim.py', 24, 'python').
project_file('tests/test_token_validator_patterns.py', 41, 'python').
project_file('tests/test_user_config.py', 105, 'python').
project_file('tests/test_version_sync.py', 263, 'python').
project_file('tests/test_version_validation.py', 254, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('examples/api-usage/01_basic_api.py', 'main', 0, 10, 12).
python_function('examples/api-usage/02_git_operations.py', '_check_git_repository', 0, 2, 2).
python_function('examples/api-usage/02_git_operations.py', '_display_staged_files', 0, 5, 3).
python_function('examples/api-usage/02_git_operations.py', '_display_unstaged_files', 0, 5, 3).
python_function('examples/api-usage/02_git_operations.py', '_display_diff_stats', 0, 5, 6).
python_function('examples/api-usage/02_git_operations.py', '_display_diff_content', 0, 2, 3).
python_function('examples/api-usage/02_git_operations.py', 'main', 0, 2, 6).
python_function('examples/api-usage/03_commit_generation.py', 'main', 0, 9, 7).
python_function('examples/api-usage/04_version_validation.py', 'main', 0, 11, 9).
python_function('examples/api-usage/05_programmatic_workflow.py', 'run_custom_workflow', 0, 1, 1).
python_function('examples/api-usage/05_programmatic_workflow.py', 'create_minimal_workflow', 0, 1, 1).
python_function('examples/custom-hooks/post-commit.py', 'get_commit_info', 0, 1, 4).
python_function('examples/custom-hooks/post-commit.py', 'notify_slack', 1, 3, 6).
python_function('examples/custom-hooks/post-commit.py', 'update_changelog', 1, 4, 6).
python_function('examples/custom-hooks/post-commit.py', 'log_to_file', 1, 1, 5).
python_function('examples/custom-hooks/post-commit.py', 'main', 0, 1, 5).
python_function('examples/custom-hooks/pre-commit.py', 'check_secrets', 0, 8, 9).
python_function('examples/custom-hooks/pre-commit.py', 'check_file_sizes', 1, 5, 7).
python_function('examples/custom-hooks/pre-commit.py', 'run_tests', 0, 2, 1).
python_function('examples/custom-hooks/pre-commit.py', 'main', 0, 5, 7).
python_function('examples/custom-hooks/pre-publish.py', 'test_build', 0, 3, 6).
python_function('examples/custom-hooks/pre-publish.py', 'test_install', 0, 4, 7).
python_function('examples/custom-hooks/pre-publish.py', 'check_version', 0, 6, 5).
python_function('examples/custom-hooks/pre-publish.py', 'run_security_check', 0, 2, 2).
python_function('examples/custom-hooks/pre-publish.py', 'main', 0, 4, 4).
python_function('examples/my-new-project/tests/test_my-new-project.py', 'test_example', 0, 2, 0).
python_function('examples/template-generator/generate.py', 'generate_project', 2, 4, 10).
python_function('examples/template-generator/generate.py', 'main', 0, 2, 7).
python_function('examples/testing/03_advanced_mocking.py', 'test_mocking_external_services', 0, 3, 5).
python_function('examples/testing/03_advanced_mocking.py', 'test_mocking_git_operations', 0, 2, 5).
python_function('examples/testing/03_advanced_mocking.py', 'test_mocking_click_interactions', 0, 2, 7).
python_function('examples/testing/03_advanced_mocking.py', 'test_spies_and_call_counting', 0, 6, 13).
python_function('examples/testing/03_advanced_mocking.py', 'test_mocking_file_system', 0, 1, 2).
python_function('examples/testing/03_advanced_mocking.py', 'test_conditional_mocking', 0, 1, 5).
python_function('examples/testing/03_advanced_mocking.py', 'test_mock_context_manager', 0, 2, 9).
python_function('examples/testing/04_debugging_diagnostics.py', 'test_debug_output_capture', 0, 8, 12).
python_function('examples/testing/04_debugging_diagnostics.py', 'test_stack_trace_analysis', 0, 3, 11).
python_function('examples/testing/04_debugging_diagnostics.py', 'test_performance_timing', 0, 3, 12).
python_function('examples/testing/04_debugging_diagnostics.py', 'test_import_tracing', 0, 5, 5).
python_function('examples/testing/04_debugging_diagnostics.py', 'test_config_diagnostics', 0, 4, 6).
python_function('examples/testing/04_debugging_diagnostics.py', 'create_debug_report', 0, 7, 8).
python_function('examples/validation/run_all_validation.py', 'main', 0, 2, 5).
python_function('examples/validation/test_api_signatures.py', 'main', 0, 2, 8).
python_function('examples/validation/test_imports.py', 'main', 0, 2, 8).
python_function('examples/validation/test_readme_consistency.py', 'main', 0, 3, 7).
python_function('examples/validation/test_syntax_check.py', 'main', 0, 2, 6).
python_function('examples/webhooks/discord-webhook.py', 'send_discord_notification', 2, 5, 8).
python_function('examples/webhooks/discord-webhook.py', 'main', 0, 4, 5).
python_function('examples/webhooks/slack-webhook.py', 'send_slack_notification', 2, 5, 9).
python_function('examples/webhooks/slack-webhook.py', 'main', 0, 4, 5).
python_function('goal/authors/manager.py', 'get_project_authors', 1, 1, 2).
python_function('goal/authors/manager.py', 'add_project_author', 5, 1, 2).
python_function('goal/authors/utils.py', 'format_co_author_trailer', 2, 1, 0).
python_function('goal/authors/utils.py', 'parse_co_authors', 1, 2, 5).
python_function('goal/authors/utils.py', 'add_co_authors_to_message', 2, 5, 2).
python_function('goal/authors/utils.py', 'remove_co_authors_from_message', 1, 5, 7).
python_function('goal/authors/utils.py', 'validate_author_format', 1, 3, 3).
python_function('goal/authors/utils.py', 'deduplicate_co_authors', 1, 4, 5).
python_function('goal/authors/utils.py', 'get_co_authors_from_command_line', 1, 3, 3).
python_function('goal/authors/utils.py', 'format_commit_message_with_co_authors', 3, 3, 1).
python_function('goal/authors/utils.py', 'extract_current_author_from_config', 0, 1, 2).
python_function('goal/bootstrap/configurator.py', 'scaffold_test_file', 2, 14, 11).
python_function('goal/bootstrap/configurator.py', '_find_python_bin', 1, 5, 4).
python_function('goal/bootstrap/configurator.py', '_read_openrouter_api_key', 1, 11, 6).
python_function('goal/bootstrap/configurator.py', '_find_openrouter_api_key', 1, 6, 5).
python_function('goal/bootstrap/configurator.py', '_find_git_root', 1, 3, 2).
python_function('goal/bootstrap/costs_badge.py', '_install_costs_package', 2, 3, 5).
python_function('goal/bootstrap/costs_badge.py', '_load_costs_api', 0, 2, 6).
python_function('goal/bootstrap/costs_badge.py', '_commit_blob_lower', 2, 3, 3).
python_function('goal/bootstrap/costs_badge.py', '_filter_ai_commits', 2, 4, 2).
python_function('goal/bootstrap/costs_badge.py', '_parsed_diff_is_usable', 1, 4, 2).
python_function('goal/bootstrap/costs_badge.py', '_fetch_commit_diff', 4, 3, 5).
python_function('goal/bootstrap/costs_badge.py', '_single_commit_ai_cost', 5, 3, 5).
python_function('goal/bootstrap/costs_badge.py', '_calculate_ai_costs', 1, 4, 6).
python_function('goal/bootstrap/costs_badge.py', '_read_model_from_pyproject', 1, 3, 4).
python_function('goal/bootstrap/costs_badge.py', '_generate_costs_badge', 1, 6, 14).
python_function('goal/bootstrap/detector.py', '_match_marker', 2, 2, 4).
python_function('goal/bootstrap/detector.py', 'detect_project_types_deep', 2, 11, 10).
python_function('goal/bootstrap/detector.py', '_python_package_dir_exists', 2, 5, 4).
python_function('goal/bootstrap/detector.py', '_guess_python_name', 1, 5, 5).
python_function('goal/bootstrap/detector.py', '_python_scaffold_import_name', 2, 5, 3).
python_function('goal/bootstrap/detector.py', '_guess_nodejs_name', 1, 4, 5).
python_function('goal/bootstrap/detector.py', '_guess_rust_name', 1, 4, 4).
python_function('goal/bootstrap/detector.py', '_guess_go_name', 1, 4, 5).
python_function('goal/bootstrap/detector.py', 'guess_package_name', 2, 4, 3).
python_function('goal/bootstrap/installer.py', '_match_marker', 2, 2, 4).
python_function('goal/bootstrap/installer.py', '_should_skip_install', 2, 6, 2).
python_function('goal/bootstrap/installer.py', '_ensure_costs_installed', 2, 3, 4).
python_function('goal/bootstrap/installer.py', '_install_python_deps_legacy', 3, 14, 18).
python_function('goal/bootstrap/installer.py', '_install_python_deps_broker', 2, 2, 5).
python_function('goal/bootstrap/installer.py', '_ensure_python_test_dependency', 3, 5, 5).
python_function('goal/bootstrap/installer.py', '_ensure_python_env', 3, 9, 14).
python_function('goal/bootstrap/installer.py', '_needs_install', 2, 10, 4).
python_function('goal/bootstrap/installer.py', '_run_dep_install', 2, 4, 8).
python_function('goal/bootstrap/installer.py', '_get_matching_dep_command', 2, 4, 3).
python_function('goal/bootstrap/installer.py', '_ensure_generic_env', 4, 6, 8).
python_function('goal/bootstrap/installer.py', 'ensure_project_environment', 3, 3, 4).
python_function('goal/bootstrap/pyproject_costs_setup.py', '_find_dep_list_end', 2, 12, 2).
python_function('goal/bootstrap/pyproject_costs_setup.py', '_try_merge_optional_dev_deps', 1, 6, 7).
python_function('goal/bootstrap/pyproject_costs_setup.py', '_try_merge_hatch_default_deps', 1, 6, 6).
python_function('goal/bootstrap/pyproject_costs_setup.py', '_try_add_deps', 1, 4, 4).
python_function('goal/bootstrap/pyproject_costs_setup.py', '_add_deps_to_section_match', 3, 10, 8).
python_function('goal/bootstrap/pyproject_costs_setup.py', '_ensure_costs_config', 1, 5, 9).
python_function('goal/bootstrap/pyproject_costs_setup.py', '_ensure_env_template', 1, 6, 8).
python_function('goal/changelog.py', '_classify_file_domain', 2, 5, 4).
python_function('goal/changelog.py', '_build_domain_entry', 4, 7, 7).
python_function('goal/changelog.py', '_build_simple_entry', 3, 3, 3).
python_function('goal/changelog.py', '_insert_entry', 2, 5, 3).
python_function('goal/changelog.py', '_find_unreleased_insert_pos', 1, 3, 4).
python_function('goal/changelog.py', 'update_changelog', 5, 5, 10).
python_function('goal/cli/__init__.py', '_has_cli_flag', 3, 8, 2).
python_function('goal/cli/__init__.py', '_goal_update_command', 0, 4, 4).
python_function('goal/cli/__init__.py', '_warn_goal_binary_mismatch', 0, 8, 10).
python_function('goal/cli/__init__.py', '_setup_nfo_logging', 2, 3, 3).
python_function('goal/cli/__init__.py', '_nfo_log_call', 0, 2, 1).
python_function('goal/cli/__init__.py', 'load_command_modules', 0, 3, 1).
python_function('goal/cli/__init__.py', '_auto_update_goal', 2, 3, 3).
python_function('goal/cli/__init__.py', '_show_goal_version_banner', 0, 3, 4).
python_function('goal/cli/__init__.py', '_explicit_ascii_flag', 1, 2, 0).
python_function('goal/cli/__init__.py', '_resolve_output_markdown', 2, 3, 1).
python_function('goal/cli/__init__.py', '_configure_main_context', 15, 3, 5).
python_function('goal/cli/__init__.py', 'main', 17, 4, 7).
python_function('goal/cli/authors_cmd.py', 'display_author_details', 2, 4, 3).
python_function('goal/cli/authors_cmd.py', 'display_current_author', 1, 1, 2).
python_function('goal/cli/authors_cmd.py', 'authors', 0, 1, 1).
python_function('goal/cli/authors_cmd.py', 'authors_list', 0, 1, 3).
python_function('goal/cli/authors_cmd.py', 'authors_add', 4, 1, 5).
python_function('goal/cli/authors_cmd.py', 'authors_remove', 1, 1, 4).
python_function('goal/cli/authors_cmd.py', 'authors_update', 4, 1, 5).
python_function('goal/cli/authors_cmd.py', 'authors_import', 0, 1, 3).
python_function('goal/cli/authors_cmd.py', 'authors_export', 0, 1, 3).
python_function('goal/cli/authors_cmd.py', 'authors_find', 1, 1, 5).
python_function('goal/cli/authors_cmd.py', 'authors_co_author', 2, 1, 4).
python_function('goal/cli/authors_cmd.py', 'authors_current', 0, 1, 4).
python_function('goal/cli/commit_cmd.py', '_output_detailed', 3, 3, 2).
python_function('goal/cli/commit_cmd.py', '_output_simple', 3, 6, 2).
python_function('goal/cli/commit_cmd.py', 'commit', 7, 8, 16).
python_function('goal/cli/commit_cmd.py', 'fix_summary', 4, 12, 15).
python_function('goal/cli/commit_cmd.py', 'validate', 3, 13, 15).
python_function('goal/cli/config_cmd.py', 'config', 0, 1, 1).
python_function('goal/cli/config_cmd.py', 'config_show', 2, 4, 8).
python_function('goal/cli/config_cmd.py', 'config_validate', 3, 3, 7).
python_function('goal/cli/config_cmd.py', 'config_update', 1, 1, 4).
python_function('goal/cli/config_cmd.py', 'config_set', 3, 2, 7).
python_function('goal/cli/config_cmd.py', 'config_get', 2, 2, 5).
python_function('goal/cli/config_cmd.py', 'setup', 2, 3, 6).
python_function('goal/cli/config_validate_cmd.py', 'validate_cmd', 4, 3, 8).
python_function('goal/cli/doctor_cmd.py', 'doctor', 5, 12, 20).
python_function('goal/cli/hooks_cmd.py', 'display_success_message', 1, 1, 2).
python_function('goal/cli/hooks_cmd.py', 'display_failure_message', 1, 1, 2).
python_function('goal/cli/hooks_cmd.py', 'display_install_success', 0, 1, 2).
python_function('goal/cli/hooks_cmd.py', 'hooks', 0, 1, 1).
python_function('goal/cli/hooks_cmd.py', 'hooks_install', 1, 2, 6).
python_function('goal/cli/hooks_cmd.py', 'hooks_uninstall', 0, 2, 5).
python_function('goal/cli/hooks_cmd.py', 'hooks_run', 1, 2, 6).
python_function('goal/cli/hooks_cmd.py', 'hooks_status', 0, 1, 3).
python_function('goal/cli/license_cmd.py', 'license', 0, 1, 1).
python_function('goal/cli/license_cmd.py', 'license_create', 4, 6, 12).
python_function('goal/cli/license_cmd.py', 'license_update', 3, 3, 7).
python_function('goal/cli/license_cmd.py', 'license_validate', 0, 3, 5).
python_function('goal/cli/license_cmd.py', 'license_info', 1, 6, 6).
python_function('goal/cli/license_cmd.py', 'license_check', 2, 2, 5).
python_function('goal/cli/license_cmd.py', 'license_list', 1, 7, 9).
python_function('goal/cli/license_cmd.py', 'license_template', 2, 4, 10).
python_function('goal/cli/postcommit_cmd.py', 'postcommit', 0, 1, 1).
python_function('goal/cli/postcommit_cmd.py', 'postcommit_run', 0, 2, 5).
python_function('goal/cli/postcommit_cmd.py', 'postcommit_list', 0, 1, 3).
python_function('goal/cli/postcommit_cmd.py', 'postcommit_validate', 0, 2, 5).
python_function('goal/cli/postcommit_cmd.py', 'postcommit_info', 0, 6, 5).
python_function('goal/cli/publish.py', 'makefile_has_target', 1, 4, 6).
python_function('goal/cli/publish.py', '_get_project_strategy', 2, 7, 4).
python_function('goal/cli/publish.py', '_get_configured_project_types', 1, 13, 7).
python_function('goal/cli/publish.py', '_get_python_bin', 0, 5, 6).
python_function('goal/cli/publish.py', '_ensure_publish_deps', 1, 5, 5).
python_function('goal/cli/publish.py', '_read_pyproject_package_name', 0, 6, 7).
python_function('goal/cli/publish.py', '_read_setup_py_package_name', 0, 4, 5).
python_function('goal/cli/publish.py', '_read_python_package_name', 0, 2, 2).
python_function('goal/cli/publish.py', '_normalized_name_candidates', 1, 2, 2).
python_function('goal/cli/publish.py', '_python_artifacts_for_version', 2, 8, 9).
python_function('goal/cli/publish.py', '_format_artifact_args', 1, 2, 3).
python_function('goal/cli/publish.py', '_resolve_python_publish_cmd', 2, 6, 11).
python_function('goal/cli/publish.py', '_run_python_build', 2, 5, 4).
python_function('goal/cli/publish.py', '_available_dist_artifacts', 0, 4, 5).
python_function('goal/cli/publish.py', '_ensure_python_artifacts_for_version', 3, 8, 8).
python_function('goal/cli/publish.py', '_prepare_python_publish', 2, 5, 7).
python_function('goal/cli/publish.py', '_read_nodejs_package_name', 0, 3, 4).
python_function('goal/cli/publish.py', '_nodejs_artifacts_for_version', 1, 5, 7).
python_function('goal/cli/publish.py', '_is_rate_limited', 1, 4, 0).
python_function('goal/cli/publish.py', '_run_publish_command', 2, 33, 15).
python_function('goal/cli/publish.py', 'publish_project', 4, 14, 10).
python_function('goal/cli/publish_cmd.py', '_publish_impl', 4, 8, 9).
python_function('goal/cli/publish_cmd.py', 'publish', 4, 2, 3).
python_function('goal/cli/push_cmd.py', 'push', 16, 5, 4).
python_function('goal/cli/recover_cmd.py', 'recover', 6, 6, 12).
python_function('goal/cli/recover_cmd.py', '_get_error_output', 2, 5, 4).
python_function('goal/cli/tests.py', '_get_project_strategy', 2, 7, 4).
python_function('goal/cli/tests.py', '_active_venv_python', 0, 3, 4).
python_function('goal/cli/tests.py', '_resolve_project_python', 2, 4, 6).
python_function('goal/cli/tests.py', '_pytest_importable', 2, 2, 2).
python_function('goal/cli/tests.py', '_prefer_uv_run', 2, 2, 1).
python_function('goal/cli/tests.py', '_rewrite_bash_pytest_for_uv', 3, 5, 4).
python_function('goal/cli/tests.py', '_coerce_python_strategy_to_project_pytest', 2, 8, 3).
python_function('goal/cli/tests.py', '_display_test_error', 3, 9, 6).
python_function('goal/cli/tests.py', '_has_package', 2, 3, 1).
python_function('goal/cli/tests.py', '_run_python_test', 2, 13, 14).
python_function('goal/cli/tests.py', '_run_nodejs_test', 2, 2, 2).
python_function('goal/cli/tests.py', '_run_subdir_test', 3, 3, 4).
python_function('goal/cli/tests.py', '_run_tests_in_subdirs', 2, 5, 8).
python_function('goal/cli/tests.py', '_resolve_root_python', 0, 3, 7).
python_function('goal/cli/tests.py', '_build_python_test_command', 2, 11, 8).
python_function('goal/cli/tests.py', '_ensure_root_pytest_or_mark_failed', 4, 10, 9).
python_function('goal/cli/tests.py', '_run_root_test', 3, 12, 7).
python_function('goal/cli/tests.py', '_run_project_type_tests', 2, 11, 11).
python_function('goal/cli/tests.py', 'run_tests', 2, 4, 1).
python_function('goal/cli/tests.py', 'get_test_execution_details', 0, 6, 12).
python_function('goal/cli/tests_discovery.py', '_has_usable_test_script', 2, 7, 4).
python_function('goal/cli/tests_discovery.py', '_has_project_marker', 2, 2, 3).
python_function('goal/cli/tests_discovery.py', '_find_project_root', 2, 5, 3).
python_function('goal/cli/tests_discovery.py', 'find_python_test_dirs', 0, 9, 9).
python_function('goal/cli/tests_discovery.py', 'find_nodejs_test_dirs', 0, 6, 7).
python_function('goal/cli/tests_pytest_setup.py', 'check_python_venv', 1, 3, 2).
python_function('goal/cli/tests_pytest_setup.py', '_is_uv_project', 1, 1, 1).
python_function('goal/cli/tests_pytest_setup.py', '_try_uv_install', 1, 4, 1).
python_function('goal/cli/tests_pytest_setup.py', 'ensure_pytest_for_project', 2, 9, 5).
python_function('goal/cli/utils_cmd.py', 'status', 2, 10, 11).
python_function('goal/cli/utils_cmd.py', 'init', 2, 4, 11).
python_function('goal/cli/utils_cmd.py', 'info', 0, 2, 7).
python_function('goal/cli/utils_cmd.py', 'version', 1, 2, 11).
python_function('goal/cli/utils_cmd.py', 'package_managers', 2, 8, 8).
python_function('goal/cli/utils_cmd.py', 'check_versions', 1, 2, 9).
python_function('goal/cli/utils_cmd.py', 'clone', 3, 4, 9).
python_function('goal/cli/utils_cmd.py', 'bootstrap', 2, 4, 9).
python_function('goal/cli/validation_cmd.py', 'validation', 0, 1, 1).
python_function('goal/cli/validation_cmd.py', 'validation_run', 0, 2, 5).
python_function('goal/cli/validation_cmd.py', 'validation_list', 0, 1, 3).
python_function('goal/cli/validation_cmd.py', 'validation_validate', 0, 2, 5).
python_function('goal/cli/validation_cmd.py', 'validation_info', 0, 7, 5).
python_function('goal/cli/version_sync.py', '_update_version_file', 2, 1, 3).
python_function('goal/cli/version_sync.py', '_update_json_version_file', 4, 6, 5).
python_function('goal/cli/version_sync.py', '_update_toml_version', 4, 13, 9).
python_function('goal/cli/version_sync.py', '_update_cargo_version', 4, 6, 7).
python_function('goal/cli/version_sync.py', '_update_setup_py_version', 3, 7, 7).
python_function('goal/cli/version_sync.py', '_update_csproj_versions', 2, 3, 7).
python_function('goal/cli/version_sync.py', '_update_pom_xml', 2, 3, 6).
python_function('goal/cli/version_sync.py', '_update_readme_metadata', 3, 7, 5).
python_function('goal/cli/version_sync.py', '_warn_lock_refresh', 1, 1, 2).
python_function('goal/cli/version_sync.py', '_snapshot_paths', 1, 3, 3).
python_function('goal/cli/version_sync.py', '_append_changed_paths', 3, 5, 5).
python_function('goal/cli/version_sync.py', '_sync_dependency_lockfiles', 1, 9, 10).
python_function('goal/cli/version_sync.py', '_sync_uv_lock', 1, 1, 1).
python_function('goal/cli/version_sync.py', '_sync_dependency_locks_after_manifest_updates', 1, 1, 1).
python_function('goal/cli/version_sync.py', '_update_init_py_versions', 2, 7, 8).
python_function('goal/cli/version_sync.py', 'sync_all_versions', 2, 1, 10).
python_function('goal/cli/version_utils.py', 'detect_project_types', 0, 6, 6).
python_function('goal/cli/version_utils.py', 'find_version_files', 0, 6, 6).
python_function('goal/cli/version_utils.py', 'get_version_from_file', 2, 3, 3).
python_function('goal/cli/version_utils.py', 'get_current_version', 0, 5, 7).
python_function('goal/cli/version_utils.py', 'bump_version', 2, 5, 5).
python_function('goal/cli/version_utils.py', 'update_version_in_file', 4, 3, 5).
python_function('goal/cli/version_utils.py', 'update_json_version', 2, 3, 4).
python_function('goal/cli/version_utils.py', '_build_author_block', 3, 5, 5).
python_function('goal/cli/version_utils.py', '_update_tomlkit_license', 2, 2, 0).
python_function('goal/cli/version_utils.py', '_update_tomlkit_authors', 3, 6, 4).
python_function('goal/cli/version_utils.py', '_update_tomlkit_classifier', 2, 5, 1).
python_function('goal/cli/version_utils.py', '_update_pyproject_with_tomlkit', 5, 4, 5).
python_function('goal/cli/version_utils.py', '_update_regex_license', 2, 3, 2).
python_function('goal/cli/version_utils.py', '_update_regex_authors', 3, 3, 4).
python_function('goal/cli/version_utils.py', '_update_regex_classifier', 2, 2, 1).
python_function('goal/cli/version_utils.py', '_update_pyproject_with_regex', 5, 1, 3).
python_function('goal/cli/version_utils.py', '_update_pyproject_metadata', 5, 2, 2).
python_function('goal/cli/version_utils.py', '_update_package_json_metadata', 4, 4, 3).
python_function('goal/cli/version_utils.py', '_update_setup_py_metadata', 4, 1, 1).
python_function('goal/cli/version_utils.py', 'update_project_metadata', 2, 8, 7).
python_function('goal/cli/version_utils.py', '_update_license_section', 2, 5, 6).
python_function('goal/cli/version_utils.py', '_update_author_section', 2, 3, 6).
python_function('goal/cli/version_utils.py', 'update_readme_metadata', 1, 6, 8).
python_function('goal/cli/wizard_cmd.py', 'wizard', 4, 5, 9).
python_function('goal/cli/wizard_cmd.py', '_setup_git_repository', 0, 10, 9).
python_function('goal/cli/wizard_cmd.py', '_find_git_root', 0, 3, 2).
python_function('goal/cli/wizard_cmd.py', '_add_git_remote', 0, 3, 5).
python_function('goal/cli/wizard_cmd.py', '_setup_user_config', 1, 12, 11).
python_function('goal/cli/wizard_cmd.py', '_setup_project_config', 0, 9, 15).
python_function('goal/cli/wizard_cmd.py', '_show_setup_summary', 0, 7, 10).
python_function('goal/cli.py', '_format_import_warning_message', 1, 1, 0).
python_function('goal/cli.py', '_print_import_warning', 2, 1, 2).
python_function('goal/cli_helpers.py', 'strip_ansi', 1, 2, 1).
python_function('goal/cli_helpers.py', 'split_paths_by_type', 1, 14, 6).
python_function('goal/cli_helpers.py', 'stage_paths', 1, 5, 3).
python_function('goal/cli_helpers.py', 'confirm', 2, 6, 5).
python_function('goal/commit_generator.py', 'is_detailed_output_requested', 1, 1, 0).
python_function('goal/commit_generator.py', 'display_commit_message', 1, 1, 2).
python_function('goal/commit_generator.py', 'print_detailed_message', 1, 2, 1).
python_function('goal/commit_generator.py', 'display_detailed_message', 1, 1, 2).
python_function('goal/config/manager.py', 'init_config', 1, 3, 4).
python_function('goal/config/manager.py', 'load_config', 1, 1, 2).
python_function('goal/config/manager.py', 'ensure_config', 1, 5, 6).
python_function('goal/config/validation.py', 'validate_config_file', 2, 11, 8).
python_function('goal/config/validation.py', 'validate_config_interactive', 1, 10, 11).
python_function('goal/config/validation.py', '_auto_fix_config', 2, 9, 1).
python_function('goal/dependency_update.py', '_run_update_command', 2, 4, 5).
python_function('goal/dependency_update.py', '_select_managers_to_update', 1, 21, 13).
python_function('goal/dependency_update.py', '_path_has_skipped_dir', 1, 1, 2).
python_function('goal/dependency_update.py', '_iter_project_marker_files', 1, 6, 3).
python_function('goal/dependency_update.py', 'discover_dependency_project_roots', 1, 7, 12).
python_function('goal/dependency_update.py', '_format_project_label', 1, 2, 4).
python_function('goal/dependency_update.py', '_update_dependencies_in_root', 1, 12, 8).
python_function('goal/dependency_update.py', 'update_project_dependencies', 1, 13, 9).
python_function('goal/doctor/core.py', 'diagnose_project', 3, 2, 4).
python_function('goal/doctor/core.py', 'diagnose_and_report', 3, 8, 11).
python_function('goal/doctor/dotnet.py', 'diagnose_dotnet', 2, 4, 5).
python_function('goal/doctor/go.py', 'diagnose_go', 2, 5, 6).
python_function('goal/doctor/java.py', 'diagnose_java', 2, 6, 4).
python_function('goal/doctor/logging.py', '_log_issue', 1, 3, 5).
python_function('goal/doctor/logging.py', '_log_fix', 1, 1, 2).
python_function('goal/doctor/nodejs.py', 'diagnose_nodejs', 2, 13, 8).
python_function('goal/doctor/php.py', 'diagnose_php', 2, 7, 6).
python_function('goal/doctor/python.py', 'diagnose_python', 2, 6, 7).
python_function('goal/doctor/ruby.py', 'diagnose_ruby', 2, 3, 3).
python_function('goal/doctor/rust.py', 'diagnose_rust', 2, 4, 5).
python_function('goal/doctor/todo.py', '_generate_ticket_id', 1, 1, 2).
python_function('goal/doctor/todo.py', '_read_existing_tickets', 1, 4, 7).
python_function('goal/doctor/todo.py', '_format_todo_entry', 1, 3, 2).
python_function('goal/doctor/todo.py', 'add_issues_to_todo', 3, 9, 16).
python_function('goal/doctor/todo.py', 'diagnose_and_report_with_todo', 4, 6, 2).
python_function('goal/formatter.py', '_build_functional_overview', 9, 12, 5).
python_function('goal/formatter.py', '_build_files_section', 4, 8, 6).
python_function('goal/formatter.py', '_determine_next_steps', 3, 4, 0).
python_function('goal/formatter.py', 'format_push_result', 12, 13, 16).
python_function('goal/formatter.py', 'format_goal_all_summary', 0, 17, 15).
python_function('goal/formatter.py', '_format_complexity_metric', 1, 6, 2).
python_function('goal/formatter.py', '_format_metrics_section', 2, 5, 5).
python_function('goal/formatter.py', '_format_relations_section', 1, 4, 1).
python_function('goal/formatter.py', '_build_capabilities_content', 1, 4, 1).
python_function('goal/formatter.py', '_build_roles_content', 1, 4, 1).
python_function('goal/formatter.py', '_build_details_content', 2, 3, 0).
python_function('goal/formatter.py', '_get_optional_sections', 5, 2, 5).
python_function('goal/formatter.py', '_build_enhanced_summary_section', 5, 9, 4).
python_function('goal/formatter.py', '_add_optional_sections', 6, 3, 2).
python_function('goal/formatter.py', 'format_enhanced_summary', 10, 5, 10).
python_function('goal/formatter.py', 'format_status_output', 4, 4, 7).
python_function('goal/generator/generator.py', 'generate_smart_commit_message', 1, 1, 2).
python_function('goal/git_ops.py', 'run_git', 0, 1, 2).
python_function('goal/git_ops.py', 'run_command', 2, 1, 1).
python_function('goal/git_ops.py', '_echo_cmd', 1, 3, 6).
python_function('goal/git_ops.py', '_run_git_verbose', 0, 11, 8).
python_function('goal/git_ops.py', 'run_git_with_status', 0, 14, 8).
python_function('goal/git_ops.py', 'run_command_tee', 1, 6, 10).
python_function('goal/git_ops.py', 'is_git_repository', 0, 2, 3).
python_function('goal/git_ops.py', 'validate_repo_url', 1, 4, 2).
python_function('goal/git_ops.py', 'get_remote_url', 1, 2, 2).
python_function('goal/git_ops.py', 'list_remotes', 0, 6, 7).
python_function('goal/git_ops.py', '_prompt_remote_url', 0, 3, 5).
python_function('goal/git_ops.py', '_list_remote_branches', 1, 5, 8).
python_function('goal/git_ops.py', 'get_remote_branch', 0, 2, 2).
python_function('goal/git_ops.py', 'clone_repository', 2, 6, 9).
python_function('goal/git_ops.py', '_select_branch', 1, 3, 7).
python_function('goal/git_ops.py', '_handle_merge_strategy', 2, 8, 8).
python_function('goal/git_ops.py', '_handle_init_remote', 1, 5, 7).
python_function('goal/git_ops.py', '_handle_clone', 0, 3, 5).
python_function('goal/git_ops.py', '_handle_local_init', 0, 2, 3).
python_function('goal/git_ops.py', 'ensure_git_repository', 1, 3, 11).
python_function('goal/git_ops.py', 'ensure_remote', 1, 7, 9).
python_function('goal/git_ops.py', 'get_staged_files', 0, 2, 3).
python_function('goal/git_ops.py', 'get_unstaged_files', 0, 3, 3).
python_function('goal/git_ops.py', 'get_working_tree_files', 0, 5, 4).
python_function('goal/git_ops.py', 'get_diff_stats', 1, 7, 6).
python_function('goal/git_ops.py', 'get_diff_content', 2, 5, 4).
python_function('goal/git_ops.py', 'read_ticket', 1, 7, 7).
python_function('goal/git_ops.py', 'apply_ticket_prefix', 2, 6, 4).
python_function('goal/hooks/config.py', 'get_hook_config', 1, 8, 6).
python_function('goal/hooks/config.py', 'create_precommit_config', 2, 3, 4).
python_function('goal/hooks/manager.py', 'install_hooks', 2, 4, 2).
python_function('goal/hooks/manager.py', 'uninstall_hooks', 1, 4, 2).
python_function('goal/hooks/manager.py', 'run_hooks', 2, 4, 2).
python_function('goal/installers/config.py', 'load_installer_config', 1, 3, 7).
python_function('goal/io/stdio.py', 'set_stdio_markdown', 1, 1, 1).
python_function('goal/io/stdio.py', 'use_markdown_stdio', 0, 2, 0).
python_function('goal/io/stdio.py', 'echo_via_markdown', 1, 2, 3).
python_function('goal/io/stdio.py', 'echo_heading', 1, 2, 4).
python_function('goal/io/stdio.py', 'echo_auto', 1, 2, 4).
python_function('goal/io/stdio.py', 'echo_command_block', 1, 2, 4).
python_function('goal/io/stdio.py', 'echo_output_block', 1, 3, 4).
python_function('goal/io/stdio.py', 'echo_info', 1, 2, 3).
python_function('goal/io/stdio.py', 'echo_status_ok', 1, 2, 4).
python_function('goal/io/stdio.py', 'echo_status_warn', 1, 2, 4).
python_function('goal/io/stdio.py', 'echo_status_error', 1, 2, 4).
python_function('goal/license/manager.py', 'create_license_file', 4, 10, 2).
python_function('goal/license/manager.py', 'update_license_file', 3, 7, 2).
python_function('goal/license/spdx.py', '_load_spdx_data', 0, 4, 4).
python_function('goal/license/spdx.py', 'validate_spdx_id', 1, 11, 6).
python_function('goal/license/spdx.py', 'get_license_info', 1, 4, 2).
python_function('goal/license/spdx.py', 'check_compatibility', 2, 14, 4).
python_function('goal/license/spdx.py', 'get_compatible_licenses', 1, 2, 3).
python_function('goal/license/spdx.py', 'is_copyleft', 1, 1, 0).
python_function('goal/license/spdx.py', 'is_permissive', 1, 1, 0).
python_function('goal/package_managers.py', '_path_matches', 2, 2, 4).
python_function('goal/package_managers.py', '_has_any_matching_path', 2, 2, 2).
python_function('goal/package_managers.py', '_detect_package_manager', 2, 2, 1).
python_function('goal/package_managers.py', '_has_language_extension', 2, 2, 3).
python_function('goal/package_managers.py', 'detect_package_managers', 1, 3, 4).
python_function('goal/package_managers.py', 'get_package_manager', 1, 1, 1).
python_function('goal/package_managers.py', 'get_package_managers_by_language', 1, 3, 1).
python_function('goal/package_managers.py', 'is_package_manager_available', 1, 1, 1).
python_function('goal/package_managers.py', 'get_available_package_managers', 1, 3, 2).
python_function('goal/package_managers.py', 'get_preferred_package_manager', 2, 5, 1).
python_function('goal/package_managers.py', '_pip_update_all_command', 1, 6, 2).
python_function('goal/package_managers.py', 'get_update_all_command', 2, 3, 1).
python_function('goal/package_managers.py', 'format_package_manager_command', 2, 3, 3).
python_function('goal/package_managers.py', 'get_package_manager_info', 1, 1, 1).
python_function('goal/package_managers.py', 'list_all_package_managers', 0, 2, 2).
python_function('goal/package_managers.py', 'detect_project_language', 1, 3, 3).
python_function('goal/package_managers.py', 'suggest_package_managers', 1, 5, 7).
python_function('goal/postcommit/manager.py', 'run_post_commit_actions', 1, 1, 2).
python_function('goal/project_bootstrap.py', '_match_marker', 2, 2, 4).
python_function('goal/project_bootstrap.py', 'detect_project_types_deep', 2, 11, 10).
python_function('goal/project_bootstrap.py', '_find_python_bin', 1, 5, 4).
python_function('goal/project_bootstrap.py', '_read_openrouter_api_key', 1, 11, 7).
python_function('goal/project_bootstrap.py', '_find_openrouter_api_key', 1, 6, 5).
python_function('goal/project_bootstrap.py', '_find_git_root', 1, 3, 2).
python_function('goal/project_bootstrap.py', 'refresh_test_dependencies', 1, 10, 13).
python_function('goal/project_bootstrap.py', '_ensure_python_test_dependency', 3, 5, 5).
python_function('goal/project_bootstrap.py', '_ensure_python_env', 3, 6, 13).
python_function('goal/project_bootstrap.py', '_should_skip_install', 2, 6, 2).
python_function('goal/project_bootstrap.py', '_install_python_deps', 3, 12, 17).
python_function('goal/project_bootstrap.py', '_install_python_deps_broker', 2, 2, 5).
python_function('goal/project_bootstrap.py', '_ensure_generic_env', 4, 14, 10).
python_function('goal/project_bootstrap.py', 'ensure_project_environment', 3, 3, 4).
python_function('goal/project_bootstrap.py', 'find_existing_tests', 2, 5, 4).
python_function('goal/project_bootstrap.py', '_resolve_scaffold_test_path', 4, 4, 2).
python_function('goal/project_bootstrap.py', 'scaffold_test', 3, 8, 12).
python_function('goal/project_bootstrap.py', '_new_bootstrap_result', 2, 1, 0).
python_function('goal/project_bootstrap.py', '_pfix_auto_apply', 1, 8, 10).
python_function('goal/project_bootstrap.py', '_coerce_bool', 1, 5, 3).
python_function('goal/project_bootstrap.py', '_goal_yaml_auto_apply', 1, 10, 7).
python_function('goal/project_bootstrap.py', '_auto_fix_enabled', 1, 3, 4).
python_function('goal/project_bootstrap.py', '_run_bootstrap_diagnostics', 3, 4, 4).
python_function('goal/project_bootstrap.py', '_ensure_bootstrap_tests', 3, 3, 2).
python_function('goal/project_bootstrap.py', 'bootstrap_project', 3, 1, 5).
python_function('goal/project_bootstrap.py', 'bootstrap_all_projects', 2, 6, 9).
python_function('goal/project_bootstrap.py', '_ensure_costs_installed', 2, 2, 4).
python_function('goal/project_bootstrap.py', '_ensure_pfix_env', 1, 7, 9).
python_function('goal/project_bootstrap.py', '_validate_pfix_env', 1, 4, 4).
python_function('goal/project_bootstrap.py', '_ensure_pfix_installed', 2, 6, 14).
python_function('goal/project_bootstrap.py', '_ensure_pfix_config', 2, 4, 7).
python_function('goal/project_bootstrap.py', 'scaffold_test_file', 2, 1, 1).
python_function('goal/publish/changes.py', '_normalize_path', 1, 1, 3).
python_function('goal/publish/changes.py', '_basename', 1, 1, 1).
python_function('goal/publish/changes.py', '_suffix', 1, 1, 2).
python_function('goal/publish/changes.py', '_matches_any', 2, 5, 4).
python_function('goal/publish/changes.py', '_is_test_path', 1, 6, 5).
python_function('goal/publish/changes.py', '_is_metadata_file', 1, 7, 4).
python_function('goal/publish/changes.py', '_is_publishable_for_type', 2, 12, 8).
python_function('goal/publish/changes.py', 'analyze_publishable_changes', 2, 8, 5).
python_function('goal/publish/github_fallback.py', '_publishing_section', 1, 10, 3).
python_function('goal/publish/github_fallback.py', 'get_github_release_config', 1, 15, 9).
python_function('goal/publish/github_fallback.py', 'detect_github_owner_repo', 0, 5, 4).
python_function('goal/publish/github_fallback.py', 'resolve_github_repo', 2, 5, 1).
python_function('goal/publish/github_fallback.py', 'is_pypi_blocked', 1, 6, 1).
python_function('goal/publish/github_fallback.py', '_gh_available', 0, 1, 1).
python_function('goal/publish/github_fallback.py', '_env_token_present', 1, 1, 3).
python_function('goal/publish/github_fallback.py', '_token_present', 1, 2, 2).
python_function('goal/publish/github_fallback.py', '_gh_authenticated', 0, 6, 2).
python_function('goal/publish/github_fallback.py', 'github_fallback_actionable', 1, 3, 2).
python_function('goal/publish/github_fallback.py', '_dist_assets', 3, 12, 10).
python_function('goal/publish/github_fallback.py', 'publish_github_release', 1, 15, 14).
python_function('goal/publish/github_fallback.py', 'try_github_fallback', 1, 3, 5).
python_function('goal/push/commands.py', 'push', 15, 4, 4).
python_function('goal/push/core.py', 'run_git_local', 0, 1, 1).
python_function('goal/push/core.py', 'show_workflow_preview', 8, 8, 7).
python_function('goal/push/core.py', 'add_slow_test_tickets_to_planfile', 1, 22, 12).
python_function('goal/push/core.py', 'output_final_summary', 14, 29, 15).
python_function('goal/push/core.py', '_validate_toml_or_exit', 1, 3, 4).
python_function('goal/push/core.py', '_apply_enhanced_quality_gates', 7, 6, 4).
python_function('goal/push/core.py', '_handle_no_files', 5, 3, 1).
python_function('goal/push/core.py', '_abort_if_missing_commit_title', 1, 2, 2).
python_function('goal/push/core.py', '_maybe_show_workflow_preview', 8, 2, 1).
python_function('goal/push/core.py', '_run_test_stage_or_exit', 9, 3, 4).
python_function('goal/push/core.py', 'execute_push_workflow', 18, 20, 34).
python_function('goal/push/core.py', '_build_publish_summary', 3, 4, 0).
python_function('goal/push/core.py', '_initialize_context', 5, 3, 2).
python_function('goal/push/core.py', '_detect_project_types', 0, 2, 4).
python_function('goal/push/core.py', '_bootstrap_projects', 3, 5, 3).
python_function('goal/push/core.py', '_detect_and_bootstrap_projects', 3, 1, 2).
python_function('goal/push/core.py', '_handle_no_changes', 4, 4, 5).
python_function('goal/push/core.py', '_validate_staged_files', 3, 6, 6).
python_function('goal/push/core.py', '_handle_commit_phase', 12, 8, 13).
python_function('goal/push/stages/changelog.py', 'handle_changelog', 5, 2, 4).
python_function('goal/push/stages/changelog.py', 'update_changelog_stage', 4, 1, 1).
python_function('goal/push/stages/commit.py', 'get_commit_message', 6, 11, 7).
python_function('goal/push/stages/commit.py', '_build_validation_summary', 4, 1, 1).
python_function('goal/push/stages/commit.py', '_confirm_suggested_title', 3, 4, 1).
python_function('goal/push/stages/commit.py', '_echo_applied_title_fix', 3, 3, 3).
python_function('goal/push/stages/commit.py', 'enforce_quality_gates', 8, 10, 8).
python_function('goal/push/stages/commit.py', 'handle_single_commit', 5, 7, 4).
python_function('goal/push/stages/commit.py', '_commit_file_group', 5, 5, 9).
python_function('goal/push/stages/commit.py', '_commit_release_metadata', 8, 5, 11).
python_function('goal/push/stages/commit.py', 'handle_split_commits', 8, 14, 14).
python_function('goal/push/stages/costs.py', '_is_cost_tracking_enabled', 0, 4, 5).
python_function('goal/push/stages/costs.py', '_compute_ai_costs', 3, 8, 6).
python_function('goal/push/stages/costs.py', 'update_cost_badges', 4, 11, 17).
python_function('goal/push/stages/dry_run.py', '_build_split_plan_body', 6, 8, 10).
python_function('goal/push/stages/dry_run.py', '_format_markdown_dry_run', 9, 4, 3).
python_function('goal/push/stages/dry_run.py', '_print_plain_dry_run', 6, 4, 6).
python_function('goal/push/stages/dry_run.py', 'handle_dry_run', 16, 5, 5).
python_function('goal/push/stages/publish.py', '_format_skip_message', 1, 9, 4).
python_function('goal/push/stages/publish.py', 'handle_publish', 7, 15, 15).
python_function('goal/push/stages/push_remote.py', '_print_push_header', 2, 4, 6).
python_function('goal/push/stages/push_remote.py', '_push_tag_if_needed', 2, 4, 4).
python_function('goal/push/stages/push_remote.py', '_handle_push_failure', 3, 5, 5).
python_function('goal/push/stages/push_remote.py', 'push_to_remote', 4, 7, 9).
python_function('goal/push/stages/push_remote.py', '_offer_recovery', 1, 2, 6).
python_function('goal/push/stages/push_remote.py', '_is_large_file_error', 1, 2, 2).
python_function('goal/push/stages/push_remote.py', '_handle_large_file_error', 1, 6, 9).
python_function('goal/push/stages/push_remote.py', '_handle_large_files_in_history', 1, 2, 4).
python_function('goal/push/stages/push_remote.py', '_handle_large_files_staged', 1, 2, 4).
python_function('goal/push/stages/push_remote.py', '_execute_recovery', 1, 3, 5).
python_function('goal/push/stages/push_remote.py', '_show_diff_info', 0, 11, 8).
python_function('goal/push/stages/push_remote.py', '_show_recovery_menu', 1, 1, 5).
python_function('goal/push/stages/push_remote.py', '_handle_recovery_choice', 2, 5, 6).
python_function('goal/push/stages/push_remote.py', '_handle_force_push', 0, 4, 6).
python_function('goal/push/stages/push_remote.py', '_handle_pull_merge', 0, 3, 4).
python_function('goal/push/stages/push_remote.py', '_handle_view_diff', 0, 6, 5).
python_function('goal/push/stages/push_remote.py', '_handle_automatic_recovery', 1, 4, 5).
python_function('goal/push/stages/tag.py', 'create_tag', 2, 4, 3).
python_function('goal/push/stages/test.py', 'run_test_stage', 10, 9, 12).
python_function('goal/push/stages/todo.py', 'handle_todo_stage', 3, 14, 10).
python_function('goal/push/stages/version.py', '_get_version_module', 0, 1, 0).
python_function('goal/push/stages/version.py', 'sync_all_versions_wrapper', 2, 1, 2).
python_function('goal/push/stages/version.py', 'handle_version_sync', 4, 3, 7).
python_function('goal/push/stages/version.py', 'get_version_info', 2, 2, 3).
python_function('goal/recovery/large_file.py', '_run_git_chunked', 4, 4, 3).
python_function('goal/smart_commit/generator.py', 'create_smart_generator', 1, 1, 1).
python_function('goal/summary/__init__.py', 'generate_business_summary', 3, 1, 2).
python_function('goal/summary/__init__.py', 'validate_summary', 3, 2, 3).
python_function('goal/summary/__init__.py', 'auto_fix_summary', 3, 2, 3).
python_function('goal/toml_validation.py', 'get_tomllib', 0, 3, 0).
python_function('goal/toml_validation.py', 'validate_toml_file', 1, 9, 15).
python_function('goal/toml_validation.py', 'validate_project_toml_files', 1, 4, 4).
python_function('goal/toml_validation.py', 'check_pyproject_toml', 0, 3, 3).
python_function('goal/user_config.py', 'get_git_user_name', 0, 3, 2).
python_function('goal/user_config.py', 'get_git_user_email', 0, 3, 2).
python_function('goal/user_config.py', 'prompt_for_license', 0, 4, 7).
python_function('goal/user_config.py', 'initialize_user_config', 1, 11, 9).
python_function('goal/user_config.py', 'get_user_config', 0, 2, 3).
python_function('goal/user_config.py', 'show_user_config', 0, 2, 6).
python_function('goal/validation/manager.py', 'run_custom_validations', 1, 1, 2).
python_function('goal/validators/dot_folders.py', '_is_dot_path', 1, 3, 2).
python_function('goal/validators/dot_folders.py', '_is_safe_path', 1, 3, 1).
python_function('goal/validators/dot_folders.py', '_is_whitelisted_path', 2, 4, 3).
python_function('goal/validators/dot_folders.py', '_matches_problematic', 2, 4, 3).
python_function('goal/validators/dot_folders.py', 'check_dot_folders', 2, 9, 12).
python_function('goal/validators/dot_folders.py', 'manage_dot_folders', 3, 9, 13).
python_function('goal/validators/file_validator.py', 'get_file_size_mb', 1, 2, 1).
python_function('goal/validators/file_validator.py', '_is_excluded', 2, 3, 3).
python_function('goal/validators/file_validator.py', '_handle_oversized_file', 5, 3, 3).
python_function('goal/validators/file_validator.py', '_check_file_for_tokens', 2, 3, 4).
python_function('goal/validators/file_validator.py', 'validate_files', 7, 12, 9).
python_function('goal/validators/file_validator.py', 'handle_large_files', 1, 5, 10).
python_function('goal/validators/file_validator.py', '_get_deleted_staged_files', 0, 4, 4).
python_function('goal/validators/file_validator.py', 'validate_staged_files', 1, 14, 6).
python_function('goal/validators/gitignore.py', 'load_gitignore', 1, 6, 6).
python_function('goal/validators/gitignore.py', 'save_gitignore', 2, 8, 9).
python_function('goal/validators/tokens.py', '_calculate_entropy', 1, 5, 4).
python_function('goal/validators/tokens.py', '_is_dummy_value', 1, 8, 4).
python_function('goal/validators/tokens.py', '_get_entropy_threshold', 1, 1, 1).
python_function('goal/validators/tokens.py', '_classify_token', 1, 3, 0).
python_function('goal/validators/tokens.py', '_extract_token_value', 2, 4, 2).
python_function('goal/validators/tokens.py', 'detect_tokens_in_content', 2, 10, 11).
python_function('goal/validators/tokens.py', 'resolve_token_patterns', 1, 7, 3).
python_function('goal/validators/tokens.py', 'migrate_token_patterns', 1, 1, 1).
python_function('goal/validators/tokens.py', 'get_default_token_patterns', 0, 1, 0).
python_function('goal/version_validation.py', 'get_pypi_version', 1, 2, 5).
python_function('goal/version_validation.py', 'get_npm_version', 1, 2, 5).
python_function('goal/version_validation.py', 'get_cargo_version', 1, 2, 5).
python_function('goal/version_validation.py', 'get_rubygems_version', 1, 2, 5).
python_function('goal/version_validation.py', 'get_registry_version', 2, 2, 3).
python_function('goal/version_validation.py', 'extract_badge_versions', 1, 4, 5).
python_function('goal/version_validation.py', 'update_badge_versions', 2, 3, 4).
python_function('goal/version_validation.py', '_detect_python_package', 0, 9, 6).
python_function('goal/version_validation.py', '_detect_nodejs_package', 0, 3, 6).
python_function('goal/version_validation.py', '_detect_rust_package', 0, 4, 6).
python_function('goal/version_validation.py', '_detect_ruby_package', 0, 4, 6).
python_function('goal/version_validation.py', '_validate_single_type', 2, 4, 2).
python_function('goal/version_validation.py', 'validate_project_versions', 2, 2, 1).
python_function('goal/version_validation.py', 'check_readme_badges', 1, 5, 4).
python_function('goal/version_validation.py', 'format_validation_results', 1, 5, 2).
python_function('test_recovery.py', 'test_strategy_detection', 0, 7, 5).
python_function('test_recovery.py', 'test_recovery_manager', 0, 4, 8).
python_function('test_recovery.py', 'main', 0, 4, 2).
python_function('tests/test_changelog.py', 'test_update_changelog_creates_new_file', 0, 5, 7).
python_function('tests/test_changelog.py', 'test_update_changelog_appends_to_existing', 0, 4, 7).
python_function('tests/test_changelog.py', 'test_update_changelog_with_domain_grouping', 0, 3, 7).
python_function('tests/test_changelog.py', 'test_update_changelog_limits_files', 0, 3, 7).
python_function('tests/test_changelog.py', 'test_update_changelog_with_unreleased_section', 0, 4, 7).
python_function('tests/test_cli_options.py', 'run_cli', 0, 1, 1).
python_function('tests/test_cli_options.py', 'test_push_help_includes_markdown_ascii_split_ticket', 0, 5, 1).
python_function('tests/test_cli_options.py', 'test_status_help_includes_markdown_ascii', 0, 3, 1).
python_function('tests/test_cli_options.py', 'test_unknown_command_shows_docs_url', 0, 5, 3).
python_function('tests/test_cli_options.py', 'test_known_commands_work', 0, 3, 1).
python_function('tests/test_cli_options.py', 'test_all_help_does_not_fail_when_push_unavailable', 0, 4, 3).
python_function('tests/test_cli_options.py', 'test_missing_push_command_shows_install_hint', 0, 6, 4).
python_function('tests/test_cli_options.py', 'test_goal_update_command_prefers_active_venv_python', 1, 3, 4).
python_function('tests/test_cli_options.py', 'test_version_banner_includes_ready_to_run_update_command', 2, 4, 4).
python_function('tests/test_cli_options.py', 'test_warn_goal_binary_mismatch_detects_local_venv_without_active_virtual_env', 3, 3, 7).
python_function('tests/test_cli_options.py', 'test_warn_goal_binary_mismatch_prefers_local_goal_binary_hint', 3, 3, 7).
python_function('tests/test_cli_tests_runner.py', 'test_find_python_test_dirs_deduplicates_project_roots_and_prefers_tests_dir', 2, 2, 5).
python_function('tests/test_cli_tests_runner.py', 'test_resolve_project_python_returns_absolute_project_python', 0, 3, 5).
python_function('tests/test_cli_tests_runner.py', 'test_ensure_pytest_for_project_tries_multiple_install_strategies', 0, 7, 4).
python_function('tests/test_cli_tests_runner.py', 'test_active_venv_python_is_preferred_for_root_run', 1, 5, 5).
python_function('tests/test_cli_tests_runner.py', 'test_run_tests_uses_configured_python_strategy_and_skips_subdir_scan', 0, 9, 5).
python_function('tests/test_cli_tests_runner.py', 'test_rewrite_bash_pytest_for_uv_converts_goal_yaml_style_command', 0, 4, 2).
python_function('tests/test_cli_tests_runner.py', 'test_build_python_test_command_prefers_venv_pytest_when_importable', 1, 4, 3).
python_function('tests/test_cli_tests_runner.py', 'test_get_test_execution_details_and_planfile_update', 2, 13, 11).
python_function('tests/test_config_shim.py', 'test_config_shim_exports', 0, 6, 1).
python_function('tests/test_config_shim.py', 'test_all_exports', 0, 6, 0).
python_function('tests/test_dependency_update.py', 'test_get_update_all_command_for_uv', 0, 2, 3).
python_function('tests/test_dependency_update.py', 'test_get_update_all_command_for_pip_with_requirements', 1, 2, 3).
python_function('tests/test_dependency_update.py', 'test_get_update_all_command_for_go', 0, 2, 3).
python_function('tests/test_dependency_update.py', 'test_select_managers_uses_only_highest_priority_python_lockfile', 2, 2, 6).
python_function('tests/test_dependency_update.py', 'test_select_managers_uv_only_without_poetry_lock', 2, 2, 6).
python_function('tests/test_dependency_update.py', 'test_select_managers_prefers_lockfile_manager', 2, 2, 6).
python_function('tests/test_dependency_update.py', 'test_update_project_dependencies_dry_run', 2, 3, 7).
python_function('tests/test_dependency_update.py', 'test_update_project_dependencies_runs_detected_manager', 2, 4, 10).
python_function('tests/test_dependency_update.py', 'test_has_cli_flag_detects_combined_short_options', 0, 14, 1).
python_function('tests/test_dependency_update.py', 'test_discover_dependency_project_roots_finds_subprojects', 2, 2, 6).
python_function('tests/test_dependency_update.py', 'test_discover_dependency_project_roots_respects_recursive_flag', 2, 3, 6).
python_function('tests/test_dependency_update.py', 'test_aur_sets_recursive_and_upgrade_deps_in_context', 0, 6, 5).
python_function('tests/test_dependency_update.py', 'test_interactive_skips_declined_projects', 2, 5, 12).
python_function('tests/test_dependency_update.py', 'test_auto_mode_processes_all_projects_without_prompts', 2, 5, 12).
python_function('tests/test_dependency_update.py', 'test_aiu_sets_interactive_in_context', 0, 5, 5).
python_function('tests/test_dependency_update.py', 'test_ar_sets_recursive_in_context', 0, 4, 5).
python_function('tests/test_dependency_update.py', 'test_upgrade_deps_runs_before_bootstrap', 1, 5, 4).
python_function('tests/test_dependency_update.py', 'test_au_sets_upgrade_deps_in_context', 0, 5, 5).
python_function('tests/test_dependency_update.py', 'test_au_sets_markdown_in_context', 0, 4, 5).
python_function('tests/test_dependency_update.py', 'test_all_with_ascii_keeps_ascii_output', 0, 4, 5).
python_function('tests/test_detect_version_files.py', '_detect_in', 1, 1, 4).
python_function('tests/test_detect_version_files.py', 'test_skips_venv_and_site_packages', 1, 4, 4).
python_function('tests/test_detect_version_files.py', 'test_skips_build_and_node_modules', 1, 4, 5).
python_function('tests/test_detect_version_files.py', 'test_monorepo_detects_nested_manifest', 1, 4, 4).
python_function('tests/test_detect_version_files.py', 'test_skips_example_and_fixture_manifests', 1, 4, 4).
python_function('tests/test_detect_version_files.py', 'test_prefers_shallowest_package', 1, 4, 3).
python_function('tests/test_file_validation.py', 'test_file_size_validation', 0, 4, 5).
python_function('tests/test_file_validation.py', 'test_token_detection', 0, 7, 6).
python_function('tests/test_file_validation.py', 'test_safe_files', 0, 4, 5).
python_function('tests/test_file_validation.py', 'test_false_positive_prevention', 0, 6, 5).
python_function('tests/test_file_validation.py', 'test_symlink_to_directory_is_skipped', 1, 1, 5).
python_function('tests/test_file_validation.py', 'test_config_integration', 0, 4, 7).
python_function('tests/test_file_validation.py', 'main', 0, 2, 8).
python_function('tests/test_formatter.py', 'test_markdown_formatter_basic', 0, 3, 3).
python_function('tests/test_formatter.py', 'test_markdown_formatter_with_metadata', 0, 3, 4).
python_function('tests/test_formatter.py', 'test_markdown_formatter_section', 0, 3, 3).
python_function('tests/test_formatter.py', 'test_markdown_formatter_code_block', 0, 3, 3).
python_function('tests/test_formatter.py', 'test_markdown_formatter_list', 0, 4, 3).
python_function('tests/test_formatter.py', 'test_markdown_formatter_ordered_list', 0, 3, 3).
python_function('tests/test_formatter.py', 'test_markdown_formatter_command_output', 0, 3, 3).
python_function('tests/test_formatter.py', 'test_markdown_formatter_command_failed', 0, 2, 3).
python_function('tests/test_formatter.py', 'test_markdown_formatter_summary', 0, 5, 3).
python_function('tests/test_formatter.py', 'test_build_functional_overview', 0, 5, 1).
python_function('tests/test_formatter.py', 'test_build_functional_overview_single_feature', 0, 2, 1).
python_function('tests/test_formatter.py', 'test_build_functional_overview_no_features', 0, 3, 1).
python_function('tests/test_formatter.py', 'test_determine_next_steps_success', 0, 3, 2).
python_function('tests/test_formatter.py', 'test_determine_next_steps_test_failure', 0, 3, 2).
python_function('tests/test_formatter.py', 'test_determine_next_steps_error', 0, 2, 2).
python_function('tests/test_formatter.py', 'test_format_status_output', 0, 6, 1).
python_function('tests/test_formatter.py', 'test_format_status_output_many_unstaged', 0, 3, 2).
python_function('tests/test_formatter.py', 'test_format_push_result', 0, 5, 1).
python_function('tests/test_formatter.py', 'test_format_push_result_with_error', 0, 3, 1).
python_function('tests/test_formatter.py', 'test_format_goal_all_summary_markdown', 0, 8, 1).
python_function('tests/test_git_ops.py', 'test_validate_repo_url_ssh', 0, 3, 1).
python_function('tests/test_git_ops.py', 'test_validate_repo_url_https', 0, 3, 1).
python_function('tests/test_git_ops.py', 'test_validate_repo_url_invalid', 0, 3, 1).
python_function('tests/test_git_ops.py', 'test_apply_ticket_prefix_with_ticket', 0, 3, 1).
python_function('tests/test_git_ops.py', 'test_apply_ticket_prefix_no_ticket', 0, 2, 1).
python_function('tests/test_git_ops.py', 'test_read_ticket_file_not_exists', 0, 3, 4).
python_function('tests/test_git_ops.py', 'test_read_ticket_file_exists', 0, 2, 6).
python_function('tests/test_git_ops.py', 'test_get_diff_stats_empty', 0, 2, 3).
python_function('tests/test_git_ops.py', 'test_get_diff_stats_with_changes', 0, 3, 3).
python_function('tests/test_git_ops.py', 'test_get_diff_content_small', 0, 2, 3).
python_function('tests/test_git_ops.py', 'test_get_diff_content_large', 0, 3, 3).
python_function('tests/test_git_ops.py', 'test_get_staged_files_empty', 0, 2, 3).
python_function('tests/test_git_ops.py', 'test_get_staged_files_with_files', 0, 3, 3).
python_function('tests/test_git_ops.py', 'test_get_unstaged_files', 0, 3, 3).
python_function('tests/test_git_ops.py', 'test_is_git_repository_true', 0, 2, 6).
python_function('tests/test_git_ops.py', 'test_is_git_repository_false', 0, 2, 6).
python_function('tests/test_project_bootstrap.py', '_write_pyproject', 2, 1, 1).
python_function('tests/test_project_bootstrap.py', 'test_pfix_auto_apply_defaults_true', 1, 4, 2).
python_function('tests/test_project_bootstrap.py', 'test_pfix_auto_apply_false_is_respected', 1, 3, 2).
python_function('tests/test_project_bootstrap.py', 'test_run_bootstrap_diagnostics_gated_by_auto_apply', 2, 4, 3).
python_function('tests/test_project_bootstrap.py', 'test_auto_fix_enabled_reads_goal_yaml', 1, 4, 2).
python_function('tests/test_project_bootstrap.py', 'test_auto_fix_enabled_env_override', 2, 3, 3).
python_function('tests/test_project_bootstrap_costs.py', 'test_calculate_ai_costs_uses_commit_diff_tuple_and_message_filter', 0, 4, 5).
python_function('tests/test_publish_pattern.py', 'test_resolve_python_publish_cmd_uses_pyproject_name', 2, 2, 4).
python_function('tests/test_publish_pattern.py', 'test_resolve_python_publish_cmd_uses_setup_py_name', 2, 2, 4).
python_function('tests/test_publish_pattern.py', 'test_resolve_python_publish_cmd_filters_broad_dist_glob', 2, 2, 4).
python_function('tests/test_publish_pattern.py', 'test_ensure_python_artifacts_resyncs_setup_py_and_rebuilds', 2, 4, 8).
python_function('tests/test_publish_pattern.py', 'test_goal_config_reload_reads_updated_goal_yaml', 2, 3, 7).
python_function('tests/test_push_todo_stage.py', 'test_todo_stage_returns_false_when_prefact_missing', 0, 2, 2).
python_function('tests/test_push_todo_stage.py', 'test_todo_stage_returns_false_on_prefact_nonzero_exit', 0, 2, 3).
python_function('tests/test_push_todo_stage.py', 'test_todo_stage_stages_existing_artifacts', 2, 4, 7).
python_function('tests/test_smart_commit_shim.py', 'test_shim_imports', 0, 4, 1).
python_function('tests/test_smart_commit_shim.py', 'test_all_exports', 0, 4, 0).
python_function('tests/test_token_validator_patterns.py', 'test_urisys_nightly_session_env_is_not_flagged', 0, 3, 3).
python_function('tests/test_token_validator_patterns.py', 'test_legacy_patterns_are_removed_on_resolve', 0, 3, 2).
python_function('tests/test_token_validator_patterns.py', 'test_migrate_token_patterns_reports_changes', 0, 3, 1).
python_function('tests/test_token_validator_patterns.py', 'test_credential_env_assignments_are_still_flagged', 0, 2, 2).
python_function('tests/test_user_config.py', 'test_user_config_load_existing', 0, 4, 7).
python_function('tests/test_user_config.py', 'test_user_config_save', 0, 3, 8).
python_function('tests/test_user_config.py', 'test_user_config_is_initialized', 0, 3, 6).
python_function('tests/test_user_config.py', 'test_get_git_user_name', 0, 2, 2).
python_function('tests/test_user_config.py', 'test_get_git_user_name_failure', 0, 2, 2).
python_function('tests/test_user_config.py', 'test_get_git_user_email', 0, 2, 2).
python_function('tests/test_user_config.py', 'test_available_licenses', 0, 4, 1).
python_function('tests/test_user_config.py', 'test_user_config_get_default', 0, 2, 5).
python_function('tests/test_version_sync.py', 'test_sync_updates_init_py', 1, 8, 8).
python_function('tests/test_version_sync.py', 'test_sync_skips_example_and_fixture_init', 1, 8, 10).
python_function('tests/test_version_sync.py', 'test_python_publish_command_skips_existing', 0, 3, 0).
python_function('tests/test_version_sync.py', 'test_sync_updates_setup_py_version', 2, 4, 5).
python_function('tests/test_version_sync.py', 'test_sync_updates_uv_lock_after_pyproject_version_change', 2, 6, 9).
python_function('tests/test_version_sync.py', 'test_sync_refreshes_detected_dependency_lockfiles', 6, 5, 9).
python_function('tests/test_version_sync.py', 'test_bump_version_pre_release_formats', 3, 2, 2).

% ── Python Classes ───────────────────────────────────────
python_class('examples/api-usage/test_integration.py', 'TestGoalAPIIntegration').
python_method('TestGoalAPIIntegration', 'test_bootstrap_project_detection', 1, 4, 3).
python_method('TestGoalAPIIntegration', 'test_version_validation', 0, 3, 2).
python_method('TestGoalAPIIntegration', 'test_commit_message_generation', 0, 3, 3).
python_method('TestGoalAPIIntegration', 'test_git_operations', 1, 3, 3).
python_class('examples/api-usage/test_integration.py', 'TestCustomValidators').
python_method('TestCustomValidators', 'test_file_size_validator', 1, 1, 0).
python_method('TestCustomValidators', 'test_secret_detection_validator', 0, 1, 0).
python_class('examples/api-usage/test_integration.py', 'TestHookIntegration').
python_method('TestHookIntegration', 'test_pre_commit_hook_execution_placeholder', 1, 1, 0).
python_method('TestHookIntegration', 'test_validator_registration_placeholder', 0, 1, 0).
python_class('examples/api-usage/test_integration.py', 'TestConfiguration').
python_method('TestConfiguration', 'test_config_loading', 1, 2, 3).
python_method('TestConfiguration', 'test_user_config_loading', 0, 3, 6).
python_class('examples/api-usage/test_integration.py', 'TestWorkflowIntegration').
python_method('TestWorkflowIntegration', 'test_full_workflow_dry_run', 1, 2, 4).
python_class('examples/api-usage/test_integration.py', 'ExampleGoalAPITest').
python_method('ExampleGoalAPITest', 'test_my_custom_workflow', 0, 2, 6).
python_class('examples/validation/run_all_validation.py', 'ValidationRunner').
python_method('ValidationRunner', '__init__', 1, 1, 0).
python_method('ValidationRunner', 'run_test', 2, 5, 6).
python_method('ValidationRunner', 'run_all', 0, 3, 3).
python_method('ValidationRunner', 'print_summary', 0, 6, 3).
python_class('examples/validation/test_api_signatures.py', 'APISignatureValidator').
python_method('APISignatureValidator', '__init__', 1, 1, 0).
python_method('APISignatureValidator', 'extract_function_calls', 1, 20, 10).
python_method('APISignatureValidator', 'resolve_function', 1, 8, 5).
python_method('APISignatureValidator', 'validate_call', 3, 20, 10).
python_method('APISignatureValidator', 'validate_file', 1, 3, 2).
python_method('APISignatureValidator', 'validate_all_examples', 0, 6, 9).
python_method('APISignatureValidator', 'print_report', 0, 6, 6).
python_class('examples/validation/test_imports.py', 'ImportValidator').
python_method('ImportValidator', '__init__', 1, 1, 0).
python_method('ImportValidator', 'extract_imports', 1, 9, 6).
python_method('ImportValidator', 'validate_import', 3, 9, 5).
python_method('ImportValidator', 'validate_file', 1, 3, 2).
python_method('ImportValidator', 'validate_all_examples', 0, 5, 9).
python_method('ImportValidator', 'print_report', 0, 7, 6).
python_class('examples/validation/test_readme_consistency.py', 'READMEConsistencyValidator').
python_method('READMEConsistencyValidator', '__init__', 1, 1, 0).
python_method('READMEConsistencyValidator', 'extract_file_references', 1, 6, 4).
python_method('READMEConsistencyValidator', 'extract_markdown_links', 1, 2, 3).
python_method('READMEConsistencyValidator', 'get_actual_structure', 1, 9, 8).
python_method('READMEConsistencyValidator', 'validate_readme', 2, 22, 15).
python_method('READMEConsistencyValidator', 'extract_documented_directories', 1, 3, 5).
python_method('READMEConsistencyValidator', 'extract_documented_files', 1, 2, 4).
python_method('READMEConsistencyValidator', 'validate_all', 0, 4, 8).
python_method('READMEConsistencyValidator', 'print_report', 0, 13, 6).
python_class('examples/validation/test_syntax_check.py', 'SyntaxChecker').
python_method('SyntaxChecker', '__init__', 1, 1, 0).
python_method('SyntaxChecker', 'check_python', 1, 2, 3).
python_method('SyntaxChecker', 'check_shell', 1, 6, 3).
python_method('SyntaxChecker', 'check_json', 1, 3, 4).
python_method('SyntaxChecker', 'check_yaml', 1, 4, 4).
python_method('SyntaxChecker', 'check_file', 1, 7, 8).
python_method('SyntaxChecker', 'check_all_examples', 0, 11, 10).
python_method('SyntaxChecker', 'print_report', 0, 6, 6).
python_class('goal/authors/manager.py', 'AuthorsManager').
python_method('AuthorsManager', '__init__', 1, 2, 2).
python_method('AuthorsManager', 'get_authors', 0, 2, 2).
python_method('AuthorsManager', 'add_author', 4, 5, 9).
python_method('AuthorsManager', 'remove_author', 1, 3, 9).
python_method('AuthorsManager', 'update_author', 4, 6, 7).
python_method('AuthorsManager', 'find_author', 1, 5, 3).
python_method('AuthorsManager', 'list_authors', 0, 7, 6).
python_method('AuthorsManager', 'get_current_author', 0, 1, 2).
python_method('AuthorsManager', 'import_from_git', 0, 6, 9).
python_method('AuthorsManager', 'export_to_contributors', 0, 4, 7).
python_class('goal/bootstrap/templates.py', 'ProjectTemplate').
python_class('goal/cli/__init__.py', 'GoalGroup').
python_method('GoalGroup', 'get_command', 2, 3, 8).
python_method('GoalGroup', 'parse_args', 2, 10, 7).
python_class('goal/config/manager.py', 'GoalConfig').
python_method('GoalConfig', '__init__', 1, 1, 1).
python_method('GoalConfig', '_find_config', 1, 5, 4).
python_method('GoalConfig', '_find_git_root', 0, 3, 2).
python_method('GoalConfig', 'exists', 0, 1, 1).
python_method('GoalConfig', 'load', 0, 5, 6).
python_method('GoalConfig', 'reload', 0, 1, 1).
python_method('GoalConfig', '_get_default_config', 0, 4, 8).
python_method('GoalConfig', '_deep_copy', 1, 5, 3).
python_method('GoalConfig', '_merge_configs', 2, 5, 4).
python_method('GoalConfig', '_detect_project_name', 0, 10, 8).
python_method('GoalConfig', '_detect_project_types', 0, 6, 6).
python_method('GoalConfig', '_detect_description', 0, 7, 7).
python_method('GoalConfig', '_detect_version_files', 0, 17, 12).
python_method('GoalConfig', 'save', 1, 3, 6).
python_method('GoalConfig', 'get', 2, 5, 3).
python_method('GoalConfig', 'set', 2, 4, 2).
python_method('GoalConfig', 'update_from_detection', 0, 6, 7).
python_method('GoalConfig', 'validate', 0, 8, 6).
python_method('GoalConfig', 'get_commit_template', 1, 1, 1).
python_method('GoalConfig', 'get_strategy', 1, 1, 1).
python_method('GoalConfig', 'get_registry', 1, 1, 1).
python_method('GoalConfig', 'get_publish_fallback', 0, 2, 1).
python_method('GoalConfig', 'should_auto_update', 0, 1, 1).
python_method('GoalConfig', 'to_dict', 0, 2, 2).
python_class('goal/config/validation.py', 'ConfigValidationError').
python_method('ConfigValidationError', '__init__', 2, 1, 3).
python_class('goal/config/validation.py', 'ConfigValidator').
python_method('ConfigValidator', '__init__', 1, 1, 0).
python_method('ConfigValidator', 'validate', 1, 3, 9).
python_method('ConfigValidator', '_validate_required_sections', 0, 3, 1).
python_method('ConfigValidator', '_validate_project_section', 0, 11, 7).
python_method('ConfigValidator', '_validate_git_section', 0, 13, 6).
python_method('ConfigValidator', '_validate_versioning_section', 0, 14, 6).
python_method('ConfigValidator', '_validate_publishing_section', 0, 19, 5).
python_method('ConfigValidator', '_check_bool', 3, 4, 3).
python_method('ConfigValidator', '_check_numeric', 6, 9, 3).
python_method('ConfigValidator', '_validate_advanced_section', 0, 4, 3).
python_method('ConfigValidator', '_validate_no_unknown_keys', 0, 7, 3).
python_class('goal/deep_analyzer.py', 'CodeChangeAnalyzer').
python_method('CodeChangeAnalyzer', '__init__', 0, 1, 0).
python_method('CodeChangeAnalyzer', 'analyze_file_diff', 3, 3, 6).
python_method('CodeChangeAnalyzer', '_detect_language', 1, 1, 3).
python_method('CodeChangeAnalyzer', '_analyze_python_diff', 2, 10, 11).
python_method('CodeChangeAnalyzer', '_detect_value_indicators', 1, 6, 6).
python_method('CodeChangeAnalyzer', '_extract_python_entities', 1, 13, 8).
python_method('CodeChangeAnalyzer', '_get_decorator_name', 1, 4, 3).
python_method('CodeChangeAnalyzer', '_calculate_complexity', 1, 4, 3).
python_method('CodeChangeAnalyzer', '_analyze_js_diff', 2, 13, 3).
python_method('CodeChangeAnalyzer', '_analyze_generic_diff', 2, 1, 3).
python_method('CodeChangeAnalyzer', '_detect_functional_areas', 2, 7, 7).
python_class('goal/deep_analyzer_aggregate.py', 'CodeChangeAggregatorMixin').
python_method('CodeChangeAggregatorMixin', 'aggregate_changes', 1, 3, 8).
python_method('CodeChangeAggregatorMixin', '_detect_file_patterns', 1, 6, 2).
python_method('CodeChangeAggregatorMixin', '_check_analyzer_value', 2, 4, 1).
python_method('CodeChangeAggregatorMixin', '_check_cli_value', 2, 8, 4).
python_method('CodeChangeAggregatorMixin', '_check_area_values', 2, 12, 4).
python_method('CodeChangeAggregatorMixin', '_check_complexity_value', 1, 3, 0).
python_method('CodeChangeAggregatorMixin', '_check_architecture_value', 1, 4, 4).
python_method('CodeChangeAggregatorMixin', '_build_entity_fallback', 2, 7, 2).
python_method('CodeChangeAggregatorMixin', 'infer_functional_value', 2, 6, 8).
python_method('CodeChangeAggregatorMixin', 'detect_relations', 1, 6, 6).
python_method('CodeChangeAggregatorMixin', 'generate_functional_summary', 1, 5, 9).
python_method('CodeChangeAggregatorMixin', '_format_entity_names', 2, 2, 0).
python_method('CodeChangeAggregatorMixin', '_format_relations', 1, 2, 1).
python_method('CodeChangeAggregatorMixin', '_format_complexity_change', 1, 2, 0).
python_method('CodeChangeAggregatorMixin', '_format_areas', 1, 1, 1).
python_method('CodeChangeAggregatorMixin', '_build_summary', 3, 13, 7).
python_class('goal/dependency_update.py', 'DependencyUpdateResult').
python_class('goal/doctor/models.py', 'Issue').
python_class('goal/doctor/models.py', 'DoctorReport').
python_method('DoctorReport', 'errors', 0, 3, 0).
python_method('DoctorReport', 'warnings', 0, 3, 0).
python_method('DoctorReport', 'fixed', 0, 3, 0).
python_method('DoctorReport', 'has_problems', 0, 2, 1).
python_class('goal/doctor/python_diag_core.py', 'PythonDiagnosticsCore').
python_method('PythonDiagnosticsCore', '__init__', 3, 1, 0).
python_method('PythonDiagnosticsCore', 'check_py001_missing_config', 4, 5, 3).
python_method('PythonDiagnosticsCore', 'check_py002_build_system', 0, 3, 2).
python_method('PythonDiagnosticsCore', 'check_py003_license_classifiers', 0, 7, 7).
python_method('PythonDiagnosticsCore', 'check_py004_deprecated_backends', 0, 4, 3).
python_method('PythonDiagnosticsCore', 'check_py005_license_table', 0, 5, 5).
python_method('PythonDiagnosticsCore', 'check_py006_duplicate_authors', 0, 8, 13).
python_method('PythonDiagnosticsCore', 'check_py007_requires_python', 0, 4, 3).
python_method('PythonDiagnosticsCore', 'check_py008_empty_classifiers', 0, 2, 3).
python_method('PythonDiagnosticsCore', 'check_py009_string_authors', 0, 5, 7).
python_method('PythonDiagnosticsCore', '_should_skip_string_author_check', 0, 2, 4).
python_method('PythonDiagnosticsCore', '_convert_string_author_block', 1, 6, 10).
python_class('goal/doctor/python_diag_extended.py', 'PythonDiagnostics').
python_method('PythonDiagnostics', '_collect_py010_inconsistencies', 3, 7, 5).
python_method('PythonDiagnostics', '_sync_py010_files', 3, 5, 5).
python_method('PythonDiagnostics', 'check_py010_project_name_consistency', 0, 5, 7).
python_method('PythonDiagnostics', '_collect_py011_inconsistencies', 4, 10, 6).
python_method('PythonDiagnostics', '_sync_py011_files', 4, 5, 4).
python_method('PythonDiagnostics', 'check_py011_version_consistency', 0, 5, 8).
python_method('PythonDiagnostics', 'check_py012_dist_cleanup', 0, 6, 9).
python_method('PythonDiagnostics', '_collect_stale_dist_files', 2, 4, 3).
python_method('PythonDiagnostics', '_remove_stale_dist_files', 2, 3, 2).
python_method('PythonDiagnostics', 'check_py013_goal_publish_pattern', 0, 7, 10).
python_method('PythonDiagnostics', '_extract_goal_publish_pattern', 1, 2, 3).
python_method('PythonDiagnostics', '_goal_publish_pattern_is_acceptable', 3, 3, 0).
python_method('PythonDiagnostics', '_rewrite_goal_publish_pattern', 2, 1, 1).
python_method('PythonDiagnostics', 'check_py014_pypi_token', 0, 4, 6).
python_method('PythonDiagnostics', '_is_publish_enabled', 1, 2, 0).
python_method('PythonDiagnostics', '_has_pypi_credentials', 0, 4, 4).
python_method('PythonDiagnostics', 'run_all_checks', 0, 2, 2).
python_method('PythonDiagnostics', 'write_fixes', 1, 3, 1).
python_class('goal/formatter.py', 'MarkdownFormatter').
python_method('MarkdownFormatter', '__init__', 0, 1, 0).
python_method('MarkdownFormatter', 'add_header', 2, 1, 1).
python_method('MarkdownFormatter', 'add_metadata', 0, 1, 1).
python_method('MarkdownFormatter', 'add_section', 4, 2, 1).
python_method('MarkdownFormatter', 'add_list', 3, 3, 2).
python_method('MarkdownFormatter', 'add_command_output', 3, 2, 1).
python_method('MarkdownFormatter', 'add_summary', 2, 4, 1).
python_method('MarkdownFormatter', 'render', 0, 4, 8).
python_class('goal/generator/analyzer.py', 'ChangeAnalyzer').
python_method('ChangeAnalyzer', 'classify_change_type', 3, 1, 7).
python_method('ChangeAnalyzer', '_detect_signals', 2, 1, 4).
python_method('ChangeAnalyzer', '_has_package_code', 1, 7, 3).
python_method('ChangeAnalyzer', '_is_docs_only', 1, 4, 3).
python_method('ChangeAnalyzer', '_is_ci_only', 1, 4, 3).
python_method('ChangeAnalyzer', '_has_new_goal_python_file', 2, 4, 3).
python_method('ChangeAnalyzer', '_score_by_file_patterns', 2, 5, 3).
python_method('ChangeAnalyzer', '_score_by_diff_content', 2, 3, 4).
python_method('ChangeAnalyzer', '_score_by_statistics', 3, 8, 3).
python_method('ChangeAnalyzer', '_score_by_signals', 4, 1, 4).
python_method('ChangeAnalyzer', '_score_package_signals', 3, 2, 2).
python_method('ChangeAnalyzer', '_score_text_signals', 2, 3, 2).
python_method('ChangeAnalyzer', '_score_file_signals', 2, 4, 0).
python_method('ChangeAnalyzer', '_score_path_signals', 2, 9, 1).
python_method('ChangeAnalyzer', '_score_new_functionality', 3, 5, 2).
python_method('ChangeAnalyzer', '_resolve_change_type', 4, 11, 4).
python_method('ChangeAnalyzer', 'detect_scope', 1, 14, 9).
python_method('ChangeAnalyzer', 'extract_functions_changed', 1, 3, 4).
python_class('goal/generator/analyzer.py', 'ContentAnalyzer').
python_method('ContentAnalyzer', 'short_action_summary', 2, 4, 4).
python_method('ContentAnalyzer', '_detect_tags', 2, 10, 3).
python_method('ContentAnalyzer', '_summary_from_tags', 1, 4, 1).
python_method('ContentAnalyzer', '_summary_from_paths', 2, 12, 6).
python_method('ContentAnalyzer', 'per_file_notes', 2, 3, 7).
python_method('ContentAnalyzer', '_get_added_lines', 2, 6, 6).
python_method('ContentAnalyzer', '_notes_python', 3, 7, 7).
python_method('ContentAnalyzer', '_notes_docs', 4, 10, 9).
python_method('ContentAnalyzer', '_notes_shell', 3, 4, 2).
python_class('goal/generator/generator.py', 'CommitMessageGenerator').
python_method('CommitMessageGenerator', '__init__', 1, 8, 5).
python_method('CommitMessageGenerator', 'get_diff_stats', 1, 2, 1).
python_method('CommitMessageGenerator', 'get_name_status', 2, 2, 1).
python_method('CommitMessageGenerator', 'get_numstat_map', 2, 2, 1).
python_method('CommitMessageGenerator', 'get_changed_files', 2, 2, 1).
python_method('CommitMessageGenerator', 'get_diff_content', 2, 2, 1).
python_method('CommitMessageGenerator', 'classify_change_type', 3, 2, 1).
python_method('CommitMessageGenerator', 'detect_scope', 1, 2, 1).
python_method('CommitMessageGenerator', 'extract_functions_changed', 1, 2, 1).
python_method('CommitMessageGenerator', '_short_action_summary', 2, 2, 1).
python_method('CommitMessageGenerator', '_per_file_notes', 2, 2, 1).
python_method('CommitMessageGenerator', 'generate_commit_message', 3, 7, 9).
python_method('CommitMessageGenerator', 'generate_abstraction_message', 2, 6, 5).
python_method('CommitMessageGenerator', 'generate_changelog_entry', 2, 4, 3).
python_method('CommitMessageGenerator', 'generate_enhanced_summary', 2, 8, 9).
python_method('CommitMessageGenerator', '_try_enhanced_summary', 2, 3, 2).
python_method('CommitMessageGenerator', '_classify_files', 2, 11, 3).
python_method('CommitMessageGenerator', '_build_statistics_section', 1, 1, 0).
python_method('CommitMessageGenerator', '_build_summary_section', 5, 12, 7).
python_method('CommitMessageGenerator', '_build_file_lists', 4, 1, 4).
python_method('CommitMessageGenerator', '_build_per_file_notes', 3, 4, 5).
python_method('CommitMessageGenerator', '_build_implementation_notes', 0, 1, 0).
python_method('CommitMessageGenerator', 'generate_detailed_message', 2, 3, 17).
python_class('goal/generator/git_ops.py', 'GitDiffOperations').
python_method('GitDiffOperations', '__init__', 0, 1, 0).
python_method('GitDiffOperations', 'get_diff_stats', 1, 9, 5).
python_method('GitDiffOperations', 'get_name_status', 2, 9, 8).
python_method('GitDiffOperations', 'get_numstat_map', 2, 11, 9).
python_method('GitDiffOperations', 'get_changed_files', 2, 8, 6).
python_method('GitDiffOperations', 'get_diff_content', 2, 6, 4).
python_method('GitDiffOperations', 'clear_cache', 0, 1, 1).
python_class('goal/hooks/manager.py', 'HooksManager').
python_method('HooksManager', '__init__', 1, 2, 1).
python_method('HooksManager', 'is_precommit_installed', 0, 2, 1).
python_method('HooksManager', 'is_hooks_configured', 0, 2, 1).
python_method('HooksManager', 'install_precommit', 0, 3, 4).
python_method('HooksManager', 'create_hook_script', 0, 1, 3).
python_method('HooksManager', 'create_precommit_config', 1, 3, 6).
python_method('HooksManager', 'install_hooks', 1, 4, 6).
python_method('HooksManager', 'uninstall_hooks', 0, 4, 5).
python_method('HooksManager', 'run_validation', 1, 4, 4).
python_method('HooksManager', 'run_hooks', 1, 4, 4).
python_method('HooksManager', 'status', 0, 3, 6).
python_class('goal/installers/broker.py', 'PackageManagerBroker').
python_method('PackageManagerBroker', '__init__', 1, 1, 0).
python_method('PackageManagerBroker', 'detect_available', 0, 4, 2).
python_method('PackageManagerBroker', 'install', 4, 9, 10).
python_method('PackageManagerBroker', '_select_manager', 2, 5, 1).
python_method('PackageManagerBroker', '_report', 2, 7, 2).
python_method('PackageManagerBroker', 'detect_lockfile', 0, 3, 3).
python_method('PackageManagerBroker', 'install_smart', 2, 2, 3).
python_method('PackageManagerBroker', 'show_available', 0, 6, 4).
python_class('goal/installers/config.py', 'InstallerConfig').
python_method('InstallerConfig', 'from_dict', 2, 1, 2).
python_class('goal/installers/managers/base.py', 'InstallResult').
python_class('goal/installers/managers/base.py', 'AbstractPackageManager').
python_method('AbstractPackageManager', 'is_available', 0, 1, 1).
python_method('AbstractPackageManager', 'install_editable', 1, 1, 0).
python_method('AbstractPackageManager', 'install_requirements', 1, 1, 0).
python_method('AbstractPackageManager', 'install_from_lockfile', 0, 1, 0).
python_method('AbstractPackageManager', '_run', 1, 3, 6).
python_class('goal/installers/managers/pdm.py', 'PdmManager').
python_method('PdmManager', 'install_editable', 1, 2, 2).
python_method('PdmManager', 'install_requirements', 1, 1, 1).
python_method('PdmManager', 'install_from_lockfile', 0, 1, 1).
python_class('goal/installers/managers/pip.py', 'PipManager').
python_method('PipManager', 'is_available', 0, 1, 0).
python_method('PipManager', 'install_editable', 1, 2, 2).
python_method('PipManager', 'install_requirements', 1, 1, 1).
python_class('goal/installers/managers/poetry.py', 'PoetryManager').
python_method('PoetryManager', 'install_editable', 1, 2, 2).
python_method('PoetryManager', 'install_requirements', 1, 1, 1).
python_method('PoetryManager', 'install_from_lockfile', 0, 1, 1).
python_class('goal/installers/managers/uv.py', 'UvManager').
python_method('UvManager', 'install_editable', 1, 2, 2).
python_method('UvManager', 'install_requirements', 1, 1, 1).
python_method('UvManager', 'sync_lockfile', 0, 1, 1).
python_method('UvManager', 'install_self', 0, 1, 1).
python_method('UvManager', 'install_from_lockfile', 0, 1, 1).
python_class('goal/license/manager.py', 'LicenseManager').
python_method('LicenseManager', '__init__', 1, 2, 1).
python_method('LicenseManager', 'get_available_licenses', 0, 4, 6).
python_method('LicenseManager', 'get_license_template', 1, 3, 2).
python_method('LicenseManager', 'add_custom_template', 2, 1, 4).
python_method('LicenseManager', 'create_license_file', 4, 10, 12).
python_method('LicenseManager', 'update_license_file', 3, 7, 11).
python_method('LicenseManager', '_detect_license_type', 2, 4, 1).
python_method('LicenseManager', '_resolve_license_id', 2, 4, 4).
python_method('LicenseManager', '_extract_owner_from_content', 1, 2, 3).
python_method('LicenseManager', 'validate_license_file', 0, 8, 8).
python_class('goal/package_managers.py', 'PackageManager').
python_method('PackageManager', '__post_init__', 0, 2, 0).
python_class('goal/postcommit/actions.py', 'PostCommitAction').
python_method('PostCommitAction', '__init__', 1, 1, 0).
python_method('PostCommitAction', 'execute', 1, 4, 0).
python_method('PostCommitAction', 'get_name', 0, 1, 0).
python_method('PostCommitAction', 'validate_config', 0, 1, 0).
python_class('goal/postcommit/actions.py', 'NotificationAction').
python_method('NotificationAction', 'get_name', 0, 1, 0).
python_method('NotificationAction', 'validate_config', 0, 1, 0).
python_method('NotificationAction', 'execute', 1, 4, 5).
python_class('goal/postcommit/actions.py', 'WebhookAction').
python_method('WebhookAction', 'get_name', 0, 1, 0).
python_method('WebhookAction', 'validate_config', 0, 1, 0).
python_method('WebhookAction', 'execute', 1, 4, 5).
python_class('goal/postcommit/actions.py', 'ScriptAction').
python_method('ScriptAction', 'get_name', 0, 1, 0).
python_method('ScriptAction', 'validate_config', 0, 1, 0).
python_method('ScriptAction', 'execute', 1, 4, 5).
python_class('goal/postcommit/actions.py', 'GitPushAction').
python_method('GitPushAction', 'get_name', 0, 1, 0).
python_method('GitPushAction', 'validate_config', 0, 1, 0).
python_method('GitPushAction', 'execute', 1, 4, 5).
python_class('goal/postcommit/manager.py', 'PostCommitManager').
python_method('PostCommitManager', '__init__', 1, 2, 1).
python_method('PostCommitManager', 'get_config', 0, 5, 3).
python_method('PostCommitManager', 'get_commit_info', 0, 2, 3).
python_method('PostCommitManager', 'run_actions', 0, 6, 8).
python_method('PostCommitManager', 'list_actions', 0, 4, 5).
python_method('PostCommitManager', 'validate_actions', 0, 5, 6).
python_class('goal/publish/changes.py', 'PublishChangeReport').
python_method('PublishChangeReport', 'skip_reason', 0, 3, 0).
python_class('goal/publish/github_fallback.py', 'GitHubReleaseConfig').
python_class('goal/push/core.py', 'PushContext').
python_method('PushContext', '__init__', 1, 1, 0).
python_method('PushContext', 'get', 2, 1, 1).
python_class('goal/recovery/auth.py', 'AuthErrorStrategy').
python_method('AuthErrorStrategy', 'can_handle', 1, 2, 2).
python_method('AuthErrorStrategy', 'recover', 1, 8, 7).
python_class('goal/recovery/base.py', 'RecoveryStrategy').
python_method('RecoveryStrategy', '__init__', 2, 2, 1).
python_method('RecoveryStrategy', 'can_handle', 1, 1, 0).
python_method('RecoveryStrategy', 'recover', 1, 1, 0).
python_method('RecoveryStrategy', 'run_git', 0, 2, 4).
python_method('RecoveryStrategy', 'run_git_with_output', 0, 1, 2).
python_class('goal/recovery/corrupted.py', 'CorruptedObjectStrategy').
python_method('CorruptedObjectStrategy', 'can_handle', 1, 2, 2).
python_method('CorruptedObjectStrategy', 'recover', 1, 4, 4).
python_class('goal/recovery/divergent.py', 'DivergentHistoryStrategy').
python_method('DivergentHistoryStrategy', 'can_handle', 1, 2, 2).
python_method('DivergentHistoryStrategy', 'recover', 1, 9, 10).
python_method('DivergentHistoryStrategy', '_rebase_changes', 1, 2, 3).
python_method('DivergentHistoryStrategy', '_merge_changes', 1, 2, 3).
python_method('DivergentHistoryStrategy', '_pull_changes', 0, 2, 3).
python_method('DivergentHistoryStrategy', '_force_push', 0, 3, 4).
python_class('goal/recovery/exceptions.py', 'RecoveryError').
python_method('RecoveryError', '__init__', 2, 1, 2).
python_class('goal/recovery/exceptions.py', 'AuthError').
python_method('AuthError', '__init__', 2, 1, 2).
python_class('goal/recovery/exceptions.py', 'LargeFileError').
python_method('LargeFileError', '__init__', 2, 1, 3).
python_class('goal/recovery/exceptions.py', 'DivergentHistoryError').
python_method('DivergentHistoryError', '__init__', 2, 1, 2).
python_class('goal/recovery/exceptions.py', 'CorruptedObjectError').
python_method('CorruptedObjectError', '__init__', 2, 1, 2).
python_class('goal/recovery/exceptions.py', 'LFSIssueError').
python_method('LFSIssueError', '__init__', 2, 1, 2).
python_class('goal/recovery/exceptions.py', 'RollbackError').
python_method('RollbackError', '__init__', 2, 1, 2).
python_class('goal/recovery/exceptions.py', 'NetworkError').
python_method('NetworkError', '__init__', 2, 1, 2).
python_class('goal/recovery/exceptions.py', 'QuotaExceededError').
python_method('QuotaExceededError', '__init__', 2, 1, 2).
python_class('goal/recovery/force_push.py', 'ForcePushStrategy').
python_method('ForcePushStrategy', 'can_handle', 1, 2, 2).
python_method('ForcePushStrategy', 'recover', 1, 5, 4).
python_class('goal/recovery/large_file.py', 'LargeFileStrategy').
python_method('LargeFileStrategy', '__init__', 2, 1, 2).
python_method('LargeFileStrategy', 'can_handle', 1, 2, 2).
python_method('LargeFileStrategy', 'recover', 1, 11, 13).
python_method('LargeFileStrategy', '_files_in_history', 1, 5, 2).
python_method('LargeFileStrategy', '_remove_from_history', 1, 7, 8).
python_method('LargeFileStrategy', '_extract_file_paths', 1, 8, 7).
python_method('LargeFileStrategy', '_find_large_files', 1, 5, 5).
python_method('LargeFileStrategy', '_get_file_size_mb', 1, 2, 2).
python_method('LargeFileStrategy', '_remove_large_files', 1, 6, 9).
python_method('LargeFileStrategy', '_move_to_lfs', 1, 4, 5).
python_method('LargeFileStrategy', '_skip_large_files', 1, 2, 3).
python_class('goal/recovery/lfs.py', 'LFSIssueStrategy').
python_method('LFSIssueStrategy', 'can_handle', 1, 2, 2).
python_method('LFSIssueStrategy', 'recover', 1, 6, 5).
python_class('goal/recovery/manager.py', 'RecoveryManager').
python_method('RecoveryManager', '__init__', 2, 2, 8).
python_method('RecoveryManager', '_ensure_recovery_dir', 0, 3, 6).
python_method('RecoveryManager', 'run_git', 0, 2, 4).
python_method('RecoveryManager', 'recover_from_push_failure', 1, 5, 8).
python_method('RecoveryManager', '_identify_strategy', 1, 3, 1).
python_method('RecoveryManager', '_create_backup', 0, 2, 5).
python_method('RecoveryManager', '_cleanup_backup', 1, 3, 2).
python_method('RecoveryManager', '_rollback_to_backup', 1, 3, 3).
python_method('RecoveryManager', '_attempt_push', 0, 2, 1).
python_method('RecoveryManager', 'setup_clean_clone', 0, 4, 7).
python_method('RecoveryManager', 'identify_new_commits', 0, 6, 6).
python_method('RecoveryManager', 'cherry_pick_commits', 1, 4, 7).
python_method('RecoveryManager', 'push_from_clean_clone', 0, 2, 6).
python_method('RecoveryManager', 'full_recovery_workflow', 0, 6, 10).
python_class('goal/smart_commit/abstraction.py', 'CodeAbstraction').
python_method('CodeAbstraction', '__init__', 1, 1, 1).
python_method('CodeAbstraction', 'get_domain', 1, 12, 5).
python_method('CodeAbstraction', 'get_language', 1, 1, 3).
python_method('CodeAbstraction', '_added_lines_from_diff', 1, 4, 3).
python_method('CodeAbstraction', '_dedupe_entities', 1, 3, 3).
python_method('CodeAbstraction', 'extract_entities', 2, 3, 6).
python_method('CodeAbstraction', 'extract_markdown_topics', 1, 9, 8).
python_method('CodeAbstraction', 'infer_benefit', 5, 11, 4).
python_method('CodeAbstraction', 'detect_features', 2, 7, 7).
python_method('CodeAbstraction', 'determine_abstraction_level', 1, 6, 2).
python_method('CodeAbstraction', 'get_action_verb', 1, 1, 1).
python_class('goal/smart_commit/generator.py', 'SmartCommitGenerator').
python_class('goal/smart_commit/generator_core.py', 'SmartCommitGeneratorCore').
python_method('SmartCommitGeneratorCore', '__init__', 1, 1, 1).
python_method('SmartCommitGeneratorCore', 'deep_analyzer', 0, 4, 1).
python_method('SmartCommitGeneratorCore', '_analyze_file_diffs', 2, 10, 13).
python_method('SmartCommitGeneratorCore', '_merge_deep_analysis', 2, 10, 4).
python_method('SmartCommitGeneratorCore', 'analyze_changes', 1, 4, 10).
python_method('SmartCommitGeneratorCore', '_summarize_features', 1, 3, 1).
python_method('SmartCommitGeneratorCore', '_summarize_entities', 1, 6, 3).
python_method('SmartCommitGeneratorCore', '_summarize_documentation', 1, 6, 5).
python_method('SmartCommitGeneratorCore', '_summarize_test_files', 2, 5, 2).
python_method('SmartCommitGeneratorCore', '_fallback_functional_summary', 3, 3, 1).
python_method('SmartCommitGeneratorCore', '_generate_functional_summary', 1, 7, 8).
python_method('SmartCommitGeneratorCore', '_get_staged_files', 0, 4, 3).
python_method('SmartCommitGeneratorCore', '_get_file_diff', 1, 2, 1).
python_method('SmartCommitGeneratorCore', '_infer_commit_type', 1, 11, 3).
python_class('goal/smart_commit/generator_generate.py', 'SmartCommitGeneratorGenerateMixin').
python_method('SmartCommitGeneratorGenerateMixin', 'generate_message', 2, 6, 8).
python_method('SmartCommitGeneratorGenerateMixin', '_is_docs_only_change', 1, 5, 4).
python_method('SmartCommitGeneratorGenerateMixin', '_generate_docs_message', 1, 7, 4).
python_method('SmartCommitGeneratorGenerateMixin', '_generate_high_abstraction_message', 1, 4, 2).
python_method('SmartCommitGeneratorGenerateMixin', '_generate_medium_abstraction_message', 1, 4, 3).
python_method('SmartCommitGeneratorGenerateMixin', '_generate_low_abstraction_message', 1, 7, 5).
python_method('SmartCommitGeneratorGenerateMixin', '_filter_meaningful_entities', 1, 6, 3).
python_method('SmartCommitGeneratorGenerateMixin', '_infer_message_from_files', 1, 12, 5).
python_method('SmartCommitGeneratorGenerateMixin', 'generate_functional_body', 1, 13, 7).
python_method('SmartCommitGeneratorGenerateMixin', 'generate_changelog_entry', 2, 4, 2).
python_method('SmartCommitGeneratorGenerateMixin', 'format_changelog_entry', 1, 4, 2).
python_class('goal/summary/body_formatter.py', 'CommitBodyFormatter').
python_method('CommitBodyFormatter', '__init__', 1, 1, 0).
python_method('CommitBodyFormatter', '_format_entity_list', 3, 3, 2).
python_method('CommitBodyFormatter', '_split_added_entities', 1, 6, 1).
python_method('CommitBodyFormatter', '_append_file_header', 3, 1, 2).
python_method('CommitBodyFormatter', '_append_added_entities', 3, 4, 5).
python_method('CommitBodyFormatter', '_append_entity_change', 3, 2, 2).
python_method('CommitBodyFormatter', '_format_file_change', 5, 7, 6).
python_method('CommitBodyFormatter', 'format_changes_section', 2, 7, 5).
python_method('CommitBodyFormatter', 'format_testing_section', 1, 5, 4).
python_method('CommitBodyFormatter', 'format_dependencies_section', 1, 4, 3).
python_method('CommitBodyFormatter', 'format_stats_section', 2, 7, 5).
python_method('CommitBodyFormatter', 'format_body', 7, 6, 6).
python_class('goal/summary/generator.py', 'EnhancedSummaryGenerator').
python_method('EnhancedSummaryGenerator', '__init__', 1, 2, 3).
python_method('EnhancedSummaryGenerator', 'map_entity_to_role', 1, 13, 4).
python_method('EnhancedSummaryGenerator', '_file_stems', 1, 2, 2).
python_method('EnhancedSummaryGenerator', '_special_title_from_files', 2, 8, 4).
python_method('EnhancedSummaryGenerator', '_title_from_capabilities', 1, 3, 1).
python_method('EnhancedSummaryGenerator', 'detect_capabilities', 2, 5, 6).
python_method('EnhancedSummaryGenerator', 'detect_file_relations', 2, 10, 9).
python_method('EnhancedSummaryGenerator', '_infer_domain', 1, 14, 2).
python_method('EnhancedSummaryGenerator', '_build_relation_chain', 1, 8, 5).
python_method('EnhancedSummaryGenerator', '_render_relations_ascii', 2, 6, 7).
python_method('EnhancedSummaryGenerator', 'calculate_quality_metrics', 2, 6, 8).
python_method('EnhancedSummaryGenerator', 'generate_value_title', 3, 4, 4).
python_method('EnhancedSummaryGenerator', 'generate_enhanced_summary', 4, 11, 19).
python_method('EnhancedSummaryGenerator', 'validate_summary_quality', 2, 8, 7).
python_class('goal/summary/quality_filter.py', 'SummaryQualityFilter').
python_method('SummaryQualityFilter', '__init__', 0, 5, 1).
python_method('SummaryQualityFilter', 'is_noise', 2, 3, 2).
python_method('SummaryQualityFilter', 'filter_entities', 1, 3, 2).
python_method('SummaryQualityFilter', 'has_banned_words', 1, 4, 5).
python_method('SummaryQualityFilter', 'classify_intent', 2, 14, 9).
python_method('SummaryQualityFilter', 'prioritize_capabilities', 1, 1, 2).
python_method('SummaryQualityFilter', 'format_complexity_delta', 2, 6, 1).
python_method('SummaryQualityFilter', 'dedupe_relations', 1, 4, 4).
python_method('SummaryQualityFilter', 'dedupe_files', 1, 3, 4).
python_method('SummaryQualityFilter', 'categorize_files', 1, 11, 8).
python_method('SummaryQualityFilter', 'filter_generic_nodes', 1, 4, 2).
python_method('SummaryQualityFilter', 'format_net_lines', 2, 12, 0).
python_method('SummaryQualityFilter', '_classify_by_churn', 2, 6, 0).
python_method('SummaryQualityFilter', '_classify_by_file_type', 1, 6, 3).
python_method('SummaryQualityFilter', '_score_intent_patterns', 1, 7, 2).
python_method('SummaryQualityFilter', '_resolve_scored_intent', 3, 6, 3).
python_method('SummaryQualityFilter', 'classify_intent_smart', 4, 6, 7).
python_method('SummaryQualityFilter', 'generate_architecture_title', 2, 12, 7).
python_class('goal/summary/validator.py', 'QualityValidator').
python_method('QualityValidator', '__init__', 1, 6, 8).
python_method('QualityValidator', 'validate', 2, 1, 12).
python_method('QualityValidator', '_extract_intent', 2, 5, 3).
python_method('QualityValidator', '_validate_title', 3, 10, 10).
python_method('QualityValidator', '_validate_intent', 7, 9, 4).
python_method('QualityValidator', '_validate_metrics', 3, 3, 3).
python_method('QualityValidator', '_validate_relations', 3, 3, 4).
python_method('QualityValidator', '_validate_files', 3, 3, 3).
python_method('QualityValidator', '_validate_capabilities', 3, 2, 2).
python_method('QualityValidator', '_validate_body', 3, 5, 4).
python_method('QualityValidator', '_validate_value_score', 4, 4, 3).
python_method('QualityValidator', '_calculate_score', 2, 1, 3).
python_method('QualityValidator', '_apply_title_fixes', 7, 4, 5).
python_method('QualityValidator', '_get_entities', 1, 1, 1).
python_method('QualityValidator', '_fix_banned_words_title', 6, 3, 5).
python_method('QualityValidator', '_fix_wrong_intent', 5, 4, 3).
python_method('QualityValidator', '_expand_short_title', 6, 6, 11).
python_method('QualityValidator', '_clean_relations', 1, 4, 3).
python_method('QualityValidator', '_apply_relation_fixes', 2, 2, 2).
python_method('QualityValidator', '_apply_file_dedupe', 2, 2, 3).
python_method('QualityValidator', '_apply_capability_priority', 2, 2, 2).
python_method('QualityValidator', '_apply_net_lines', 4, 3, 2).
python_method('QualityValidator', '_apply_categories', 3, 2, 4).
python_method('QualityValidator', 'auto_fix', 4, 1, 9).
python_class('goal/user_config.py', 'UserConfig').
python_method('UserConfig', '__init__', 0, 1, 2).
python_method('UserConfig', '_load', 0, 3, 3).
python_method('UserConfig', '_save', 0, 2, 5).
python_method('UserConfig', 'get', 2, 1, 1).
python_method('UserConfig', 'set', 2, 1, 1).
python_method('UserConfig', 'is_initialized', 0, 3, 0).
python_class('goal/validation/manager.py', 'ValidationRuleManager').
python_method('ValidationRuleManager', '__init__', 1, 2, 1).
python_method('ValidationRuleManager', 'get_rules', 0, 5, 3).
python_method('ValidationRuleManager', 'get_validation_context', 0, 2, 4).
python_method('ValidationRuleManager', 'validate_all', 0, 7, 8).
python_method('ValidationRuleManager', 'list_rules', 0, 4, 5).
python_method('ValidationRuleManager', 'validate_config', 0, 5, 6).
python_class('goal/validation/rules.py', 'ValidationRule').
python_method('ValidationRule', '__init__', 1, 1, 0).
python_method('ValidationRule', 'validate', 1, 8, 0).
python_method('ValidationRule', 'get_name', 0, 1, 0).
python_method('ValidationRule', 'validate_config', 0, 1, 0).
python_class('goal/validation/rules.py', 'MessagePatternRule').
python_method('MessagePatternRule', 'get_name', 0, 1, 0).
python_method('MessagePatternRule', 'validate_config', 0, 1, 0).
python_method('MessagePatternRule', 'validate', 1, 8, 2).
python_class('goal/validation/rules.py', 'FilePatternRule').
python_method('FilePatternRule', 'get_name', 0, 1, 0).
python_method('FilePatternRule', 'validate_config', 0, 1, 0).
python_method('FilePatternRule', 'validate', 1, 8, 4).
python_class('goal/validation/rules.py', 'ScriptRule').
python_method('ScriptRule', 'get_name', 0, 1, 0).
python_method('ScriptRule', 'validate_config', 0, 1, 0).
python_method('ScriptRule', 'validate', 1, 8, 5).
python_class('goal/validation/rules.py', 'CommitSizeRule').
python_method('CommitSizeRule', 'get_name', 0, 1, 0).
python_method('CommitSizeRule', 'validate_config', 0, 1, 0).
python_method('CommitSizeRule', 'validate', 1, 8, 4).
python_class('goal/validation/rules.py', 'MessageLengthRule').
python_method('MessageLengthRule', 'get_name', 0, 1, 0).
python_method('MessageLengthRule', 'validate_config', 0, 1, 0).
python_method('MessageLengthRule', 'validate', 1, 8, 3).
python_class('goal/validators/exceptions.py', 'ValidationError').
python_class('goal/validators/exceptions.py', 'FileSizeError').
python_method('FileSizeError', '__init__', 3, 1, 2).
python_class('goal/validators/exceptions.py', 'TokenDetectedError').
python_method('TokenDetectedError', '__init__', 3, 1, 2).
python_class('goal/validators/exceptions.py', 'DotFolderError').
python_method('DotFolderError', '__init__', 1, 1, 3).
python_class('tests/test_clone_repo.py', 'TestValidateRepoUrl').
python_method('TestValidateRepoUrl', 'test_valid_http_urls', 1, 2, 2).
python_method('TestValidateRepoUrl', 'test_valid_ssh_urls', 1, 2, 2).
python_method('TestValidateRepoUrl', 'test_invalid_urls', 1, 2, 2).
python_method('TestValidateRepoUrl', 'test_whitespace_is_stripped', 0, 2, 1).
python_class('tests/test_clone_repo.py', 'TestIsGitRepository').
python_method('TestIsGitRepository', 'test_true_inside_git_repo', 1, 2, 4).
python_method('TestIsGitRepository', 'test_false_outside_git_repo', 1, 2, 3).
python_class('tests/test_clone_repo.py', 'TestCloneRepository').
python_method('TestCloneRepository', 'test_invalid_url_returns_failure', 0, 3, 1).
python_method('TestCloneRepository', 'test_clone_success', 1, 4, 8).
python_method('TestCloneRepository', 'test_clone_failure_bad_remote', 1, 3, 4).
python_class('tests/test_clone_repo.py', 'TestEnsureGitRepository').
python_method('TestEnsureGitRepository', 'test_returns_true_when_already_in_repo', 1, 2, 4).
python_method('TestEnsureGitRepository', 'test_exit_option', 1, 2, 4).
python_method('TestEnsureGitRepository', 'test_auto_mode_skips', 1, 2, 3).
python_method('TestEnsureGitRepository', 'test_init_option', 1, 3, 5).
python_method('TestEnsureGitRepository', 'test_clone_option_with_valid_url', 1, 3, 8).
python_method('TestEnsureGitRepository', 'test_clone_option_invalid_url', 1, 2, 4).
python_method('TestEnsureGitRepository', 'test_init_and_add_remote', 1, 4, 10).
python_class('tests/test_clone_repo.py', 'TestCloneCommand').
python_method('TestCloneCommand', 'test_clone_help', 0, 3, 2).
python_method('TestCloneCommand', 'test_clone_invalid_url', 0, 3, 2).
python_method('TestCloneCommand', 'test_clone_valid_local_bare', 1, 4, 7).
python_class('tests/test_config_validation.py', 'TestConfigValidator').
python_method('TestConfigValidator', 'test_valid_default_config', 0, 2, 3).
python_method('TestConfigValidator', 'test_missing_required_section', 0, 3, 3).
python_method('TestConfigValidator', 'test_invalid_project_type', 0, 3, 4).
python_method('TestConfigValidator', 'test_invalid_commit_type', 0, 3, 5).
python_method('TestConfigValidator', 'test_invalid_version_strategy', 0, 3, 5).
python_method('TestConfigValidator', 'test_wrong_type_bool', 0, 3, 5).
python_method('TestConfigValidator', 'test_coverage_threshold_range', 0, 3, 4).
python_method('TestConfigValidator', 'test_strict_mode_treats_warnings_as_errors', 0, 5, 4).
python_method('TestConfigValidator', 'test_unknown_keys_warning', 0, 3, 4).
python_class('tests/test_config_validation.py', 'TestAutoFixConfig').
python_method('TestAutoFixConfig', 'test_fix_branch_prefix', 0, 2, 1).
python_method('TestAutoFixConfig', 'test_fix_tag_format', 0, 2, 1).
python_class('tests/test_config_validation.py', 'TestConfigValidationError').
python_method('TestConfigValidationError', 'test_error_message_formatting', 0, 5, 2).
python_class('tests/test_github_fallback.py', 'TestBlockedDetection').
python_method('TestBlockedDetection', 'test_429_is_blocked', 0, 2, 2).
python_method('TestBlockedDetection', 'test_403_is_blocked', 0, 2, 2).
python_method('TestBlockedDetection', 'test_auth_error_is_blocked', 0, 2, 2).
python_class('tests/test_github_fallback.py', 'TestGitHubConfig').
python_method('TestGitHubConfig', 'test_disabled_when_explicit_off', 0, 2, 1).
python_method('TestGitHubConfig', 'test_repo_map_resolution', 0, 3, 2).
python_method('TestGitHubConfig', 'test_detect_github_remote', 0, 2, 3).
python_class('tests/test_github_fallback.py', 'TestPublishFallbackOnBlock').
python_method('TestPublishFallbackOnBlock', 'test_429_skips_pypi_retries_when_github_actionable', 2, 2, 9).
python_method('TestPublishFallbackOnBlock', 'test_429_retries_when_github_not_actionable', 0, 4, 4).
python_method('TestPublishFallbackOnBlock', 'test_publish_github_release_uploads_assets', 2, 4, 11).
python_method('TestPublishFallbackOnBlock', 'test_try_github_fallback_noop_when_not_blocked', 0, 2, 2).
python_class('tests/test_installers_e2e.py', 'TestPackageManagerBrokerE2E').
python_method('TestPackageManagerBrokerE2E', 'test_broker_detects_available_managers', 0, 4, 3).
python_method('TestPackageManagerBrokerE2E', 'test_broker_detects_lockfile_uv', 1, 2, 4).
python_method('TestPackageManagerBrokerE2E', 'test_broker_detects_lockfile_poetry', 1, 2, 4).
python_method('TestPackageManagerBrokerE2E', 'test_broker_detects_lockfile_pdm', 1, 2, 4).
python_method('TestPackageManagerBrokerE2E', 'test_broker_no_lockfile', 1, 2, 3).
python_method('TestPackageManagerBrokerE2E', 'test_uv_manager_priority', 0, 2, 1).
python_method('TestPackageManagerBrokerE2E', 'test_pdm_manager_priority', 0, 2, 1).
python_method('TestPackageManagerBrokerE2E', 'test_poetry_manager_priority', 0, 2, 1).
python_method('TestPackageManagerBrokerE2E', 'test_pip_manager_priority', 0, 2, 1).
python_method('TestPackageManagerBrokerE2E', 'test_uv_manager_is_available_when_uv_installed', 0, 2, 3).
python_method('TestPackageManagerBrokerE2E', 'test_pip_manager_always_available', 0, 2, 2).
python_method('TestPackageManagerBrokerE2E', 'test_manager_registry_order', 0, 3, 1).
python_class('tests/test_installers_e2e.py', 'TestInstallResult').
python_method('TestInstallResult', 'test_install_result_success', 0, 4, 1).
python_method('TestInstallResult', 'test_install_result_failure', 0, 3, 1).
python_class('tests/test_installers_e2e.py', 'TestBootstrapIntegration').
python_method('TestBootstrapIntegration', 'test_bootstrap_imports_broker', 0, 2, 1).
python_method('TestBootstrapIntegration', 'test_bootstrap_uses_new_installer', 1, 2, 4).
python_method('TestBootstrapIntegration', 'test_legacy_bootstrap_compatibility', 0, 4, 1).
python_class('tests/test_installers_e2e.py', 'TestDoctorIntegration').
python_method('TestDoctorIntegration', 'test_doctor_imports_broker', 0, 2, 1).
python_class('tests/test_installers_e2e.py', 'TestLockfilePriority').
python_method('TestLockfilePriority', 'test_uv_lockfile_triggers_uv_manager', 1, 2, 4).
python_method('TestLockfilePriority', 'test_poetry_lockfile_triggers_poetry_manager', 1, 2, 4).
python_class('tests/test_installers_e2e.py', 'TestUvManagerReal').
python_method('TestUvManagerReal', 'test_uv_manager_detects_uv', 0, 2, 2).
python_method('TestUvManagerReal', 'test_uv_manager_install_editable_mock', 1, 4, 4).
python_class('tests/test_installers_e2e.py', 'TestPoetryManagerReal').
python_method('TestPoetryManagerReal', 'test_poetry_manager_detects_poetry', 0, 2, 2).
python_class('tests/test_installers_e2e.py', 'TestPdmManagerReal').
python_method('TestPdmManagerReal', 'test_pdm_manager_detects_pdm', 0, 2, 2).
python_class('tests/test_project_bootstrap.py', 'TestMatchMarker').
python_method('TestMatchMarker', 'test_exact_file', 1, 3, 2).
python_method('TestMatchMarker', 'test_glob_pattern', 1, 3, 2).
python_class('tests/test_project_bootstrap.py', 'TestDetectProjectTypesDeep').
python_method('TestDetectProjectTypesDeep', 'test_root_python', 1, 3, 3).
python_method('TestDetectProjectTypesDeep', 'test_subfolder_nodejs', 1, 3, 4).
python_method('TestDetectProjectTypesDeep', 'test_ignores_hidden_dirs', 1, 2, 3).
python_method('TestDetectProjectTypesDeep', 'test_multiple_types', 1, 3, 3).
python_method('TestDetectProjectTypesDeep', 'test_empty_dir', 1, 2, 1).
python_method('TestDetectProjectTypesDeep', 'test_rust_in_subfolder', 1, 2, 3).
python_method('TestDetectProjectTypesDeep', 'test_java_gradle', 1, 2, 2).
python_method('TestDetectProjectTypesDeep', 'test_dotnet_csproj', 1, 2, 2).
python_class('tests/test_project_bootstrap.py', 'TestGuessPackageName').
python_method('TestGuessPackageName', 'test_python_from_pyproject', 1, 2, 2).
python_method('TestGuessPackageName', 'test_nodejs_from_package_json', 1, 2, 2).
python_method('TestGuessPackageName', 'test_rust_from_cargo', 1, 2, 2).
python_method('TestGuessPackageName', 'test_go_from_gomod', 1, 2, 2).
python_method('TestGuessPackageName', 'test_fallback_to_dirname', 1, 2, 2).
python_method('TestGuessPackageName', 'test_test_harness_uses_directory_name', 1, 2, 3).
python_class('tests/test_project_bootstrap.py', 'TestFindExistingTests').
python_method('TestFindExistingTests', 'test_finds_python_tests', 1, 3, 4).
python_method('TestFindExistingTests', 'test_finds_nodejs_tests', 1, 2, 4).
python_method('TestFindExistingTests', 'test_no_tests_returns_empty', 1, 2, 1).
python_method('TestFindExistingTests', 'test_finds_go_tests', 1, 2, 3).
python_method('TestFindExistingTests', 'test_finds_ruby_specs', 1, 2, 4).
python_class('tests/test_project_bootstrap.py', 'TestScaffoldTest').
python_method('TestScaffoldTest', 'test_creates_python_test', 1, 5, 4).
python_method('TestScaffoldTest', 'test_creates_nodejs_test', 1, 4, 3).
python_method('TestScaffoldTest', 'test_creates_rust_test', 1, 3, 2).
python_method('TestScaffoldTest', 'test_creates_go_test', 1, 3, 2).
python_method('TestScaffoldTest', 'test_creates_ruby_spec', 1, 3, 3).
python_method('TestScaffoldTest', 'test_creates_php_test', 1, 3, 2).
python_method('TestScaffoldTest', 'test_creates_dotnet_test', 1, 3, 2).
python_method('TestScaffoldTest', 'test_creates_java_test', 1, 3, 2).
python_method('TestScaffoldTest', 'test_skips_when_tests_exist', 1, 2, 3).
python_method('TestScaffoldTest', 'test_scaffold_in_tests_project_avoids_nested_dir', 1, 4, 4).
python_method('TestScaffoldTest', 'test_skips_unknown_type', 1, 2, 1).
python_method('TestScaffoldTest', 'test_interactive_decline', 1, 3, 3).
python_class('tests/test_project_bootstrap.py', 'TestEnsureProjectEnvironmentPython').
python_method('TestEnsureProjectEnvironmentPython', 'test_creates_venv_and_installs', 1, 6, 6).
python_method('TestEnsureProjectEnvironmentPython', 'test_skips_if_venv_exists', 1, 8, 7).
python_method('TestEnsureProjectEnvironmentPython', 'test_interactive_decline', 1, 3, 4).
python_class('tests/test_project_bootstrap.py', 'TestEnsureProjectEnvironmentGeneric').
python_method('TestEnsureProjectEnvironmentGeneric', 'test_unknown_type_returns_true', 1, 2, 1).
python_method('TestEnsureProjectEnvironmentGeneric', 'test_nodejs_with_missing_npm', 1, 2, 3).
python_class('tests/test_project_bootstrap.py', 'TestOpenRouterEnvDiscovery').
python_method('TestOpenRouterEnvDiscovery', 'test_finds_parent_env_over_blank_local_env', 1, 4, 5).
python_method('TestOpenRouterEnvDiscovery', 'test_does_not_create_local_env_when_parent_key_exists', 1, 3, 5).
python_method('TestOpenRouterEnvDiscovery', 'test_creates_llm_model_template_when_no_api_key_exists', 1, 6, 3).
python_class('tests/test_project_bootstrap.py', 'TestPythonTestDependency').
python_method('TestPythonTestDependency', 'test_installs_missing_pytest', 1, 4, 3).
python_class('tests/test_project_bootstrap.py', 'TestPfixInstallSource').
python_method('TestPfixInstallSource', 'test_installs_pfix_from_pypi_by_default', 1, 3, 4).
python_method('TestPfixInstallSource', 'test_installs_pfix_from_local_path_when_configured', 1, 3, 7).
python_class('tests/test_project_bootstrap.py', 'TestCostsBadgeGeneration').
python_method('TestCostsBadgeGeneration', 'test_uses_git_root_for_subproject_analysis', 1, 7, 12).
python_class('tests/test_project_bootstrap.py', 'TestBootstrapProject').
python_method('TestBootstrapProject', 'test_full_bootstrap_python', 1, 6, 6).
python_method('TestBootstrapProject', 'test_bootstrap_with_existing_tests', 1, 3, 6).
python_class('tests/test_project_bootstrap.py', 'TestBootstrapAllProjects').
python_method('TestBootstrapAllProjects', 'test_detects_and_bootstraps', 1, 4, 8).
python_method('TestBootstrapAllProjects', 'test_empty_dir', 1, 2, 3).
python_class('tests/test_project_bootstrap.py', 'TestBootstrapCommand').
python_method('TestBootstrapCommand', 'test_bootstrap_help', 0, 3, 2).
python_method('TestBootstrapCommand', 'test_bootstrap_empty_dir', 1, 3, 3).
python_method('TestBootstrapCommand', 'test_bootstrap_python_project', 1, 4, 6).
python_class('tests/test_project_bootstrap.py', 'TestProjectBootstrapConfig').
python_method('TestProjectBootstrapConfig', 'test_required_keys', 1, 9, 4).
python_class('tests/test_project_doctor.py', 'TestDoctorReport').
python_method('TestDoctorReport', 'test_properties', 0, 5, 4).
python_method('TestDoctorReport', 'test_no_problems', 0, 2, 3).
python_class('tests/test_project_doctor.py', 'TestDiagnosePython').
python_method('TestDiagnosePython', 'test_no_pyproject', 1, 2, 1).
python_method('TestDiagnosePython', 'test_only_requirements_txt', 1, 2, 3).
python_method('TestDiagnosePython', 'test_missing_build_system', 1, 7, 4).
python_method('TestDiagnosePython', 'test_missing_build_system_no_fix', 1, 6, 4).
python_method('TestDiagnosePython', 'test_deprecated_license_classifier', 1, 7, 4).
python_method('TestDiagnosePython', 'test_broken_backend', 1, 7, 4).
python_method('TestDiagnosePython', 'test_license_table_format', 1, 6, 4).
python_method('TestDiagnosePython', 'test_duplicate_authors', 1, 6, 5).
python_method('TestDiagnosePython', 'test_missing_requires_python', 1, 6, 4).
python_method('TestDiagnosePython', 'test_healthy_project', 1, 2, 3).
python_method('TestDiagnosePython', 'test_string_format_authors', 1, 7, 4).
python_class('tests/test_project_doctor.py', 'TestDiagnoseNodejs').
python_method('TestDiagnoseNodejs', 'test_no_package_json', 1, 2, 1).
python_method('TestDiagnoseNodejs', 'test_invalid_json', 1, 2, 3).
python_method('TestDiagnoseNodejs', 'test_missing_version', 1, 6, 5).
python_method('TestDiagnoseNodejs', 'test_missing_test_script', 1, 2, 3).
python_method('TestDiagnoseNodejs', 'test_no_test_specified', 1, 2, 3).
python_method('TestDiagnoseNodejs', 'test_healthy_nodejs', 1, 2, 3).
python_class('tests/test_project_doctor.py', 'TestDiagnoseRust').
python_method('TestDiagnoseRust', 'test_no_cargo', 1, 2, 1).
python_method('TestDiagnoseRust', 'test_missing_package', 1, 2, 3).
python_method('TestDiagnoseRust', 'test_missing_edition', 1, 2, 3).
python_class('tests/test_project_doctor.py', 'TestDiagnoseGo').
python_method('TestDiagnoseGo', 'test_no_gomod', 1, 2, 1).
python_method('TestDiagnoseGo', 'test_invalid_gomod', 1, 2, 3).
python_method('TestDiagnoseGo', 'test_missing_gosum', 1, 2, 3).
python_class('tests/test_project_doctor.py', 'TestDiagnoseRuby').
python_method('TestDiagnoseRuby', 'test_no_gemfile', 1, 2, 1).
python_method('TestDiagnoseRuby', 'test_missing_lock', 1, 2, 3).
python_class('tests/test_project_doctor.py', 'TestDiagnosePhp').
python_method('TestDiagnosePhp', 'test_no_composer', 1, 2, 1).
python_method('TestDiagnosePhp', 'test_invalid_json', 1, 2, 3).
python_method('TestDiagnosePhp', 'test_missing_autoload', 1, 2, 3).
python_class('tests/test_project_doctor.py', 'TestDiagnoseDotnet').
python_method('TestDiagnoseDotnet', 'test_no_csproj', 1, 2, 1).
python_method('TestDiagnoseDotnet', 'test_missing_target_framework', 1, 2, 3).
python_class('tests/test_project_doctor.py', 'TestDiagnoseJava').
python_method('TestDiagnoseJava', 'test_no_build_file', 1, 2, 2).
python_method('TestDiagnoseJava', 'test_missing_model_version', 1, 2, 3).
python_class('tests/test_project_doctor.py', 'TestDiagnoseProject').
python_method('TestDiagnoseProject', 'test_unknown_type', 1, 2, 1).
python_method('TestDiagnoseProject', 'test_python_dispatch', 1, 2, 3).
python_class('tests/test_project_doctor.py', 'TestDiagnoseAndReport').
python_method('TestDiagnoseAndReport', 'test_prints_report', 1, 2, 2).
python_method('TestDiagnoseAndReport', 'test_healthy_project', 1, 2, 2).
python_class('tests/test_project_doctor.py', 'TestDoctorCommand').
python_method('TestDoctorCommand', 'test_doctor_help', 0, 3, 2).
python_method('TestDoctorCommand', 'test_doctor_empty_dir', 1, 3, 3).
python_method('TestDoctorCommand', 'test_doctor_finds_python_issues', 1, 3, 4).
python_method('TestDoctorCommand', 'test_doctor_no_fix', 1, 3, 5).
python_method('TestDoctorCommand', 'test_doctor_with_fix', 1, 4, 5).
python_class('tests/test_publish_changes.py', 'TestAnalyzePublishableChanges').
python_method('TestAnalyzePublishableChanges', 'test_detects_python_source_changes', 0, 3, 1).
python_method('TestAnalyzePublishableChanges', 'test_skips_metadata_only_python_changes', 0, 3, 1).
python_method('TestAnalyzePublishableChanges', 'test_skips_docs_and_tests', 0, 2, 1).
python_method('TestAnalyzePublishableChanges', 'test_detects_node_source_changes', 0, 3, 1).
python_method('TestAnalyzePublishableChanges', 'test_no_registry_types', 0, 3, 1).
python_method('TestAnalyzePublishableChanges', 'test_detects_nested_subproject_source', 0, 3, 1).
python_method('TestAnalyzePublishableChanges', 'test_lockfile_only_changes_are_not_publishable', 0, 2, 1).
python_class('tests/test_push_e2e.py', 'TestPublishRetry').
python_method('TestPublishRetry', 'test_retries_on_429_then_succeeds', 0, 4, 3).
python_method('TestPublishRetry', 'test_gives_up_after_max_retries_on_429', 0, 3, 4).
python_method('TestPublishRetry', 'test_no_retry_on_non_429_failure', 0, 2, 4).
python_method('TestPublishRetry', 'test_is_rate_limited_detection', 0, 3, 2).
python_class('tests/test_push_e2e.py', 'TestWorkflowOrder').
python_method('TestWorkflowOrder', 'test_publish_runs_before_tag_and_push', 0, 2, 4).
python_method('TestWorkflowOrder', 'test_metadata_only_changes_skip_publish_but_still_tag_and_push', 0, 1, 4).
python_method('TestWorkflowOrder', 'test_auto_publish_failure_aborts_before_tag_and_push', 0, 3, 4).
python_class('tests/test_push_e2e.py', 'TestPushWorkflowImports').
python_method('TestPushWorkflowImports', 'test_push_stages_commit_imports', 0, 3, 1).
python_method('TestPushWorkflowImports', 'test_push_stages_version_imports', 0, 3, 1).
python_method('TestPushWorkflowImports', 'test_push_stages_changelog_imports', 0, 2, 1).
python_method('TestPushWorkflowImports', 'test_push_stages_test_imports', 0, 2, 1).
python_method('TestPushWorkflowImports', 'test_push_stages_tag_imports', 0, 2, 1).
python_method('TestPushWorkflowImports', 'test_push_stages_push_remote_imports', 0, 2, 1).
python_method('TestPushWorkflowImports', 'test_push_stages_publish_imports', 0, 2, 1).
python_method('TestPushWorkflowImports', 'test_push_stages_dry_run_imports', 0, 2, 1).
python_method('TestPushWorkflowImports', 'test_push_core_imports', 0, 3, 2).
python_method('TestPushWorkflowImports', 'test_push_commands_import', 0, 2, 1).
python_method('TestPushWorkflowImports', 'test_push_package_import', 0, 2, 2).
python_method('TestPushWorkflowImports', 'test_push_cmd_shim', 0, 3, 2).
python_class('tests/test_push_e2e.py', 'TestPushWorkflowIntegration').
python_method('TestPushWorkflowIntegration', 'test_version_info_returns_tuple', 0, 3, 1).
python_method('TestPushWorkflowIntegration', 'test_format_changes_section', 0, 4, 3).
python_method('TestPushWorkflowIntegration', 'test_build_functional_overview_with_features', 0, 5, 1).
python_method('TestPushWorkflowIntegration', 'test_build_functional_overview_fallback', 0, 3, 1).
python_class('tests/test_push_e2e.py', 'TestPushWorkflowE2E').
python_method('TestPushWorkflowE2E', 'test_push_workflow_dry_run', 1, 3, 6).
python_method('TestPushWorkflowE2E', 'test_push_stages_handle_empty_inputs', 0, 2, 0).
python_method('TestPushWorkflowE2E', 'test_push_command_forwards_no_publish_flag', 0, 3, 4).
python_method('TestPushWorkflowE2E', 'test_push_workflow_aborts_on_auto_test_failure', 0, 2, 4).
python_method('TestPushWorkflowE2E', 'test_commit_phase_refreshes_costs_before_single_commit', 0, 1, 3).
python_method('TestPushWorkflowE2E', 'test_publish_project_skips_nodejs_publish_when_not_configured', 0, 2, 3).
python_method('TestPushWorkflowE2E', 'test_publish_project_runs_nodejs_publish_when_configured', 0, 2, 4).
python_method('TestPushWorkflowE2E', 'test_publish_command_falls_back_when_make_publish_fails', 0, 1, 5).
python_method('TestPushWorkflowE2E', 'test_run_tests_ignores_top_level_tests_dir_as_subdir', 0, 3, 6).
python_method('TestPushWorkflowE2E', 'test_publish_command_imports_all_required_modules', 0, 4, 5).
python_class('tests/test_version_validation.py', 'TestVersionValidation').
python_method('TestVersionValidation', 'setUp', 0, 1, 0).
python_method('TestVersionValidation', 'test_extract_badge_versions', 0, 7, 11).
python_method('TestVersionValidation', 'test_update_badge_versions', 0, 1, 7).
python_method('TestVersionValidation', 'test_check_readme_badges', 0, 2, 7).
python_method('TestVersionValidation', 'test_check_readme_badges_up_to_date', 0, 1, 1).
python_method('TestVersionValidation', 'test_check_readme_no_file', 0, 1, 3).
python_method('TestVersionValidation', 'test_get_pypi_version_success', 1, 1, 5).
python_method('TestVersionValidation', 'test_get_pypi_version_failure', 1, 2, 4).
python_method('TestVersionValidation', 'test_get_npm_version_success', 1, 1, 5).
python_method('TestVersionValidation', 'test_get_cargo_version_success', 1, 1, 5).
python_method('TestVersionValidation', 'test_get_rubygems_version_success', 1, 1, 5).
python_method('TestVersionValidation', 'test_validate_python_project', 2, 1, 5).
python_method('TestVersionValidation', 'test_validate_nodejs_project', 3, 1, 6).
python_method('TestVersionValidation', 'test_format_validation_results', 0, 1, 4).

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────
makefile_target('SHELL', '').
makefile_target('GREEN', 'Define colors for better output').
makefile_target('YELLOW', '').
makefile_target('WHITE', '').
makefile_target('RESET', '').
makefile_target('help', '').
makefile_target('install', '').
makefile_target('dev', '').
makefile_target('test', '').
makefile_target('build', '').
makefile_target('publish', '').
makefile_target('clean', '').
makefile_target('push', '').
makefile_target('docker-matrix', '').
makefile_target('bump-version', 'Bump version (e.g., make bump-version PART=patch)').

% ── Taskfile Tasks ───────────────────────────────────────
taskfile_task('', 'Install Python dependencies (editable)').
taskfile_task('', 'Run pytest suite').
taskfile_task('', 'Run strict Koru quality gates (fails on regix hard violations)').
taskfile_task('', 'Build wheel + sdist').
taskfile_task('', 'Remove build artefacts').
taskfile_task('', '[imported from Makefile] help').
taskfile_task('', '[imported from Makefile] dev').
taskfile_task('', '[imported from Makefile] publish').
taskfile_task('', '[imported from Makefile] push').
taskfile_task('', '[imported from Makefile] docker-matrix').
taskfile_task('', '[imported from Makefile] bump-version').
taskfile_task('', '[from doql] workflow: health').
taskfile_task('', '[from doql] workflow: import-makefile-hint').
taskfile_task('', 'Run install, lint, test').
taskfile_task('', 'Generate SUMD (Structured Unified Markdown Descriptor) for AI-aware project description').
taskfile_task('', 'Generate SUMR (Summary Report) with project metrics and health status').

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', 'sk-or-v1-...', 'OpenRouter API Key (required for real cost calculation)').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Default AI model for cost analysis').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').
testql_scenario('generated-from-pytests.testql.toon.yaml', 'cli').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-cli-tests.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('Taskfile.yml', 'taskfile').
sumd_declared_file('pyqual.yaml', 'pyqual').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('cli', 'click').
sumd_interface('cli', '').
sumd_interface('web', '').
sumd_workflow('install', 'manual').
sumd_workflow_step('install', 1, 'pip install .').
sumd_workflow('dev', 'manual').
sumd_workflow_step('dev', 1, 'pip install -e ".[dev]"').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, 'python -m pytest -q').
sumd_workflow('build', 'manual').
sumd_workflow_step('build', 1, 'python -m pip install --upgrade build twine').
sumd_workflow_step('build', 2, 'python -m build --sdist --wheel').
sumd_workflow('publish', 'manual').
sumd_workflow_step('publish', 1, 'python -m twine upload dist/*').
sumd_workflow('clean', 'manual').
sumd_workflow_step('clean', 1, 'rm -rf dist build *.egg-info .pytest_cache __pycache__ goal/__pycache__').
sumd_workflow('push', 'manual').
sumd_workflow_step('push', 1, 'if command -v goal &> /dev/null').
sumd_workflow_step('push', 2, 'goal push').
sumd_workflow_step('push', 3, 'else \').
sumd_workflow_step('push', 4, 'echo "Goal not installed. Run \'make install\' first."').
sumd_workflow_step('push', 5, 'fi').
sumd_workflow('docker-matrix', 'manual').
sumd_workflow_step('docker-matrix', 1, 'bash integration/run_docker_matrix.sh').
sumd_workflow('bump-version', 'manual').
sumd_workflow_step('bump-version', 1, 'if [ -z "$(PART)" ]').
sumd_workflow('koru-gate', 'manual').
sumd_workflow_step('koru-gate', 1, './scripts/koru_verify_ci.sh').
sumd_workflow('help', 'manual').
sumd_workflow_step('help', 1, 'echo "Targets:"').
sumd_workflow_step('help', 2, 'echo "  make install  - install goal locally"').
sumd_workflow_step('help', 3, 'echo "  make dev      - install in development mode"').
sumd_workflow_step('help', 4, 'echo "  make test     - run tests"').
sumd_workflow_step('help', 5, 'echo "  make build    - build package for PyPI"').
sumd_workflow_step('help', 6, 'echo "  make publish  - build and upload to PyPI"').
sumd_workflow_step('help', 7, 'echo "  make clean    - remove build artifacts"').
sumd_workflow_step('help', 8, 'echo "  make push     - use goal to push changes"').
sumd_workflow('health', 'manual').
sumd_workflow_step('health', 1, 'docker compose ps').
sumd_workflow_step('health', 2, 'docker compose exec app echo "Health check passed"').
sumd_workflow('import-makefile-hint', 'manual').
sumd_workflow_step('import-makefile-hint', 1, 'echo \'Run: taskfile import Makefile to import existing targets.\'').
sumd_workflow('all', 'manual').
sumd_workflow_step('all', 1, 'taskfile run install').
sumd_workflow_step('all', 2, 'taskfile run lint').
sumd_workflow_step('all', 3, 'taskfile run test').
sumd_workflow('sumd', 'manual').
sumd_workflow('sumr', 'manual').
```

## Source Map

*Top 5 modules by symbol density — signatures for LLM orientation.*

### `goal.project_bootstrap` (`goal/project_bootstrap.py`)

```python
def _match_marker(base, pattern)  # CC=2, fan=4
def detect_project_types_deep(root, max_depth)  # CC=11, fan=10 ⚠
def _find_python_bin(project_dir)  # CC=5, fan=4
def _read_openrouter_api_key(env_file)  # CC=11, fan=7 ⚠
def _find_openrouter_api_key(project_dir)  # CC=6, fan=5
def _find_git_root(project_dir)  # CC=3, fan=2
def refresh_test_dependencies(project_types)  # CC=10, fan=13 ⚠
def _ensure_python_test_dependency(project_dir, python_bin, test_dep)  # CC=5, fan=5
def _ensure_python_env(project_dir, cfg, yes)  # CC=6, fan=13
def _should_skip_install(project_dir, markers)  # CC=6, fan=2
def _install_python_deps(project_dir, cfg, python_bin)  # CC=12, fan=17 ⚠
def _install_python_deps_broker(project_dir, extras)  # CC=2, fan=5
def _ensure_generic_env(project_dir, project_type, cfg, yes)  # CC=14, fan=10 ⚠
def ensure_project_environment(project_dir, project_type, yes)  # CC=3, fan=4
def find_existing_tests(project_dir, project_type)  # CC=5, fan=4
def _resolve_scaffold_test_path(project_dir, project_type, cfg, package_name)  # CC=4, fan=2
def scaffold_test(project_dir, project_type, yes)  # CC=8, fan=12
def _new_bootstrap_result(project_dir, project_type)  # CC=1, fan=0
def _pfix_auto_apply(project_dir)  # CC=8, fan=10
def _coerce_bool(value)  # CC=5, fan=3
def _goal_yaml_auto_apply(project_dir)  # CC=10, fan=7 ⚠
def _auto_fix_enabled(project_dir)  # CC=3, fan=4
def _run_bootstrap_diagnostics(project_dir, project_type, yes)  # CC=4, fan=4
def _ensure_bootstrap_tests(project_dir, project_type, yes)  # CC=3, fan=2
def bootstrap_project(project_dir, project_type, yes)  # CC=1, fan=5
def bootstrap_all_projects(root, yes)  # CC=6, fan=9
def _ensure_costs_installed(project_dir, python_bin)  # CC=2, fan=4
def _ensure_pfix_env(project_dir)  # CC=7, fan=9
def _validate_pfix_env(project_dir)  # CC=4, fan=4
def _ensure_pfix_installed(project_dir, yes)  # CC=6, fan=14
def _ensure_pfix_config(project_dir, yes)  # CC=4, fan=7
def scaffold_test_file(project_dir, project_type)  # CC=1, fan=1
```

### `goal.git_ops` (`goal/git_ops.py`)

```python
def run_git()  # CC=1, fan=2
def run_command(command, capture)  # CC=1, fan=1
def _echo_cmd(args)  # CC=3, fan=6
def _run_git_verbose()  # CC=11, fan=8 ⚠
def run_git_with_status()  # CC=14, fan=8 ⚠
def run_command_tee(command)  # CC=6, fan=10
def is_git_repository()  # CC=2, fan=3
def validate_repo_url(url)  # CC=4, fan=2
def get_remote_url(remote)  # CC=2, fan=2
def list_remotes()  # CC=6, fan=7
def _prompt_remote_url()  # CC=3, fan=5
def _list_remote_branches(remote)  # CC=5, fan=8
def get_remote_branch()  # CC=2, fan=2
def clone_repository(url, target_dir)  # CC=6, fan=9
def _select_branch(branches)  # CC=3, fan=7
def _handle_merge_strategy(branches, has_files)  # CC=8, fan=8
def _handle_init_remote(has_files)  # CC=5, fan=7
def _handle_clone()  # CC=3, fan=5
def _handle_local_init()  # CC=2, fan=3
def ensure_git_repository(auto)  # CC=3, fan=11
def ensure_remote(auto)  # CC=7, fan=9
def get_staged_files()  # CC=2, fan=3
def get_unstaged_files()  # CC=3, fan=3
def get_working_tree_files()  # CC=5, fan=4
def get_diff_stats(cached)  # CC=7, fan=6
def get_diff_content(cached, max_lines)  # CC=5, fan=4
def read_ticket(path)  # CC=7, fan=7
def apply_ticket_prefix(title, ticket)  # CC=6, fan=4
```

### `goal.formatter` (`goal/formatter.py`)

```python
def _build_functional_overview(features, summary, entities, files, stats, current_version, new_version, commit_msg, project_types)  # CC=12, fan=5 ⚠
def _build_files_section(formatter, files, stats, analysis)  # CC=8, fan=6
def _determine_next_steps(error, test_exit_code, new_version)  # CC=4, fan=0
def format_push_result(project_types, files, stats, current_version, new_version, commit_msg, commit_body, test_result, test_exit_code, actions, error, analysis)  # CC=13, fan=16 ⚠
def format_goal_all_summary()  # CC=17, fan=15 ⚠
def _format_complexity_metric(metrics)  # CC=6, fan=2
def _format_metrics_section(metrics, relations)  # CC=5, fan=5
def _format_relations_section(relations)  # CC=4, fan=1
def _build_capabilities_content(capabilities)  # CC=4, fan=1
def _build_roles_content(roles)  # CC=4, fan=1
def _build_details_content(commit_body, capabilities)  # CC=3, fan=0
def _get_optional_sections(capabilities, roles, metrics, relations, commit_body)  # CC=2, fan=5
def _build_enhanced_summary_section(commit_title, files, stats, current_version, new_version)  # CC=9, fan=4
def _add_optional_sections(formatter, capabilities, roles, metrics, relations, commit_body)  # CC=3, fan=2
def format_enhanced_summary(commit_title, commit_body, capabilities, roles, relations, metrics, files, stats, current_version, new_version)  # CC=5, fan=10
def format_status_output(version, branch, staged_files, unstaged_files)  # CC=4, fan=7
class MarkdownFormatter:  # Formats Goal output as structured markdown for LLM consumpti
    def __init__()  # CC=1
    def add_header(title, level)  # CC=1
    def add_metadata()  # CC=1
    def add_section(title, content, code_block, language)  # CC=2
    def add_list(title, items, ordered)  # CC=3
    def add_command_output(command, output, exit_code)  # CC=2
    def add_summary(actions_taken, next_steps)  # CC=4
    def render()  # CC=4
```

### `goal.package_managers` (`goal/package_managers.py`)

```python
def _path_matches(project_root, pattern)  # CC=2, fan=4
def _has_any_matching_path(project_root, patterns)  # CC=2, fan=2
def _detect_package_manager(project_root, pm)  # CC=2, fan=1
def _has_language_extension(project_root, extensions)  # CC=2, fan=3
def detect_package_managers(project_path)  # CC=3, fan=4
def get_package_manager(name)  # CC=1, fan=1
def get_package_managers_by_language(language)  # CC=3, fan=1
def is_package_manager_available(pm)  # CC=1, fan=1
def get_available_package_managers(project_path)  # CC=3, fan=2
def get_preferred_package_manager(project_path, language)  # CC=5, fan=1
def _pip_update_all_command(project_root)  # CC=6, fan=2
def get_update_all_command(pm, project_root)  # CC=3, fan=1
def format_package_manager_command(pm, command_type)  # CC=3, fan=3
def get_package_manager_info(pm)  # CC=1, fan=1
def list_all_package_managers()  # CC=2, fan=2
def detect_project_language(project_path)  # CC=3, fan=3
def suggest_package_managers(project_path)  # CC=5, fan=7
class PackageManager:  # Package manager configuration and capabilities.
    def __post_init__()  # CC=2
```

### `goal.deep_analyzer_aggregate` (`goal/deep_analyzer_aggregate.py`)

```python
class CodeChangeAggregatorMixin:
    def aggregate_changes(file_analyses)  # CC=3
    def _detect_file_patterns(files)  # CC=6
    def _check_analyzer_value(file_patterns, added)  # CC=4
    def _check_cli_value(areas, added)  # CC=8
    def _check_area_values(areas, added)  # CC=12 ⚠
    def _check_complexity_value(complexity)  # CC=3
    def _check_architecture_value(added)  # CC=4
    def _build_entity_fallback(added, modified)  # CC=7
    def infer_functional_value(aggregated, files)  # CC=6
    def detect_relations(file_analyses)  # CC=6
    def generate_functional_summary(files)  # CC=5
    def _format_entity_names(items, limit)  # CC=2
    def _format_relations(relations)  # CC=2
    def _format_complexity_change(complexity)  # CC=2
    def _format_areas(areas)  # CC=1
    def _build_summary(aggregated, value, relations)  # CC=13 ⚠
```

## Call Graph

*412 nodes · 500 edges · 82 modules · CC̄=4.5*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in integration.run_matrix)* | 0 | 255 | 0 | **255** |
| `_setup_project_config` *(in goal.cli.wizard_cmd)* | 9 | 1 | 55 | **56** |
| `initialize_user_config` *(in goal.user_config)* | 11 ⚠ | 4 | 52 | **56** |
| `execute_push_workflow` *(in goal.push.core)* | 20 ⚠ | 2 | 52 | **54** |
| `set` *(in goal.user_config.UserConfig)* | 1 | 49 | 1 | **50** |
| `run_git` *(in goal.git_ops)* | 1 | 46 | 2 | **48** |
| `validate` *(in goal.cli.commit_cmd)* | 13 ⚠ | 0 | 45 | **45** |
| `output_final_summary` *(in goal.push.core)* | 29 ⚠ | 2 | 40 | **42** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/goal
# generated in 0.20s
# nodes: 412 | edges: 500 | modules: 82
# CC̄=4.5

HUBS[20]:
  integration.run_matrix.print
    CC=0  in:255  out:0  total:255
  goal.cli.wizard_cmd._setup_project_config
    CC=9  in:1  out:55  total:56
  goal.user_config.initialize_user_config
    CC=11  in:4  out:52  total:56
  goal.push.core.execute_push_workflow
    CC=20  in:2  out:52  total:54
  goal.user_config.UserConfig.set
    CC=1  in:49  out:1  total:50
  goal.git_ops.run_git
    CC=1  in:46  out:2  total:48
  goal.cli.commit_cmd.validate
    CC=13  in:0  out:45  total:45
  goal.push.core.output_final_summary
    CC=29  in:2  out:40  total:42
  goal.cli.wizard_cmd._setup_user_config
    CC=12  in:1  out:39  total:40
  goal.cli.doctor_cmd.doctor
    CC=12  in:0  out:40  total:40
  goal.cli.wizard_cmd._show_setup_summary
    CC=7  in:1  out:39  total:40
  goal.cli.commit_cmd.fix_summary
    CC=12  in:0  out:38  total:38
  goal.formatter.format_goal_all_summary
    CC=17  in:1  out:35  total:36
  examples.api-usage.01_basic_api.main
    CC=10  in:0  out:34  total:34
  goal.cli.wizard_cmd._setup_git_repository
    CC=10  in:1  out:33  total:34
  goal.push.stages.todo.handle_todo_stage
    CC=14  in:1  out:32  total:33
  goal.bootstrap.installer._install_python_deps_legacy
    CC=14  in:1  out:32  total:33
  goal.user_config.show_user_config
    CC=2  in:1  out:31  total:32
  examples.api-usage.04_version_validation.main
    CC=11  in:0  out:30  total:30
  goal.deep_analyzer.CodeChangeAnalyzer._analyze_python_diff
    CC=10  in:0  out:29  total:29

MODULES:
  examples.api-usage.01_basic_api  [1 funcs]
    main  CC=10  out:34
  examples.api-usage.02_git_operations  [6 funcs]
    _check_git_repository  CC=2  out:4
    _display_diff_content  CC=2  out:5
    _display_diff_stats  CC=5  out:11
    _display_staged_files  CC=5  out:7
    _display_unstaged_files  CC=5  out:7
    main  CC=2  out:9
  examples.api-usage.03_commit_generation  [1 funcs]
    main  CC=9  out:23
  examples.api-usage.04_version_validation  [1 funcs]
    main  CC=11  out:30
  examples.api-usage.05_programmatic_workflow  [2 funcs]
    create_minimal_workflow  CC=1  out:4
    run_custom_workflow  CC=1  out:18
  examples.custom-hooks.post-commit  [5 funcs]
    get_commit_info  CC=1  out:10
    log_to_file  CC=1  out:5
    main  CC=1  out:11
    notify_slack  CC=3  out:7
    update_changelog  CC=4  out:8
  examples.custom-hooks.pre-commit  [4 funcs]
    check_file_sizes  CC=5  out:8
    check_secrets  CC=8  out:9
    main  CC=5  out:23
    run_tests  CC=2  out:1
  examples.custom-hooks.pre-publish  [5 funcs]
    check_version  CC=6  out:12
    main  CC=4  out:8
    run_security_check  CC=2  out:5
    test_build  CC=3  out:11
    test_install  CC=4  out:17
  examples.dotnet-project.Calculator  [2 funcs]
    Add  CC=1  out:0
    Main  CC=1  out:3
  examples.template-generator.generate  [2 funcs]
    generate_project  CC=4  out:23
    main  CC=2  out:12
  examples.testing.03_advanced_mocking  [5 funcs]
    test_conditional_mocking  CC=1  out:8
    test_mocking_click_interactions  CC=2  out:14
    test_mocking_external_services  CC=3  out:10
    test_mocking_git_operations  CC=2  out:7
    test_spies_and_call_counting  CC=6  out:23
  examples.testing.04_debugging_diagnostics  [6 funcs]
    create_debug_report  CC=7  out:22
    test_config_diagnostics  CC=4  out:12
    test_debug_output_capture  CC=8  out:21
    test_import_tracing  CC=5  out:12
    test_performance_timing  CC=3  out:26
    test_stack_trace_analysis  CC=3  out:16
  examples.validation.run_all_validation  [3 funcs]
    print_summary  CC=6  out:14
    run_all  CC=3  out:7
    run_test  CC=5  out:15
  examples.webhooks.discord-webhook  [2 funcs]
    main  CC=4  out:9
    send_discord_notification  CC=5  out:15
  examples.webhooks.slack-webhook  [2 funcs]
    main  CC=4  out:9
    send_slack_notification  CC=5  out:16
  goal.authors.utils  [1 funcs]
    format_co_author_trailer  CC=1  out:0
  goal.bootstrap.configurator  [5 funcs]
    _find_git_root  CC=3  out:2
    _find_openrouter_api_key  CC=6  out:5
    _find_python_bin  CC=5  out:6
    _read_openrouter_api_key  CC=11  out:12
    scaffold_test_file  CC=14  out:12
  goal.bootstrap.costs_badge  [9 funcs]
    _calculate_ai_costs  CC=4  out:8
    _commit_blob_lower  CC=3  out:3
    _fetch_commit_diff  CC=3  out:7
    _filter_ai_commits  CC=4  out:2
    _generate_costs_badge  CC=6  out:23
    _load_costs_api  CC=2  out:9
    _parsed_diff_is_usable  CC=4  out:2
    _read_model_from_pyproject  CC=3  out:4
    _single_commit_ai_cost  CC=3  out:5
  goal.bootstrap.detector  [5 funcs]
    _match_marker  CC=2  out:4
    _python_package_dir_exists  CC=5  out:4
    _python_scaffold_import_name  CC=5  out:4
    detect_project_types_deep  CC=11  out:11
    guess_package_name  CC=4  out:3
  goal.bootstrap.installer  [12 funcs]
    _ensure_costs_installed  CC=3  out:8
    _ensure_generic_env  CC=6  out:9
    _ensure_python_env  CC=9  out:25
    _ensure_python_test_dependency  CC=5  out:15
    _get_matching_dep_command  CC=4  out:3
    _install_python_deps_broker  CC=2  out:5
    _install_python_deps_legacy  CC=14  out:32
    _match_marker  CC=2  out:4
    _needs_install  CC=10  out:9
    _run_dep_install  CC=4  out:14
  goal.bootstrap.pyproject_costs_setup  [6 funcs]
    _add_deps_to_section_match  CC=10  out:9
    _ensure_costs_config  CC=5  out:13
    _find_dep_list_end  CC=12  out:2
    _try_add_deps  CC=4  out:4
    _try_merge_hatch_default_deps  CC=6  out:6
    _try_merge_optional_dev_deps  CC=6  out:7
  goal.changelog  [6 funcs]
    _build_domain_entry  CC=7  out:12
    _build_simple_entry  CC=3  out:4
    _classify_file_domain  CC=5  out:4
    _find_unreleased_insert_pos  CC=3  out:6
    _insert_entry  CC=5  out:3
    update_changelog  CC=5  out:12
  goal.cli  [2 funcs]
    _format_import_warning_message  CC=1  out:0
    _print_import_warning  CC=1  out:2
  goal.cli.authors_cmd  [5 funcs]
    authors_co_author  CC=1  out:5
    authors_current  CC=1  out:4
    authors_find  CC=1  out:5
    display_author_details  CC=4  out:15
    display_current_author  CC=1  out:5
  goal.cli.commit_cmd  [3 funcs]
    commit  CC=8  out:27
    fix_summary  CC=12  out:38
    validate  CC=13  out:45
  goal.cli.config_cmd  [6 funcs]
    config_get  CC=2  out:6
    config_set  CC=2  out:8
    config_show  CC=4  out:11
    config_update  CC=1  out:4
    config_validate  CC=3  out:8
    setup  CC=3  out:10
  goal.cli.config_validate_cmd  [1 funcs]
    validate_cmd  CC=3  out:11
  goal.cli.doctor_cmd  [1 funcs]
    doctor  CC=12  out:40
  goal.cli.hooks_cmd  [6 funcs]
    display_failure_message  CC=1  out:3
    display_install_success  CC=1  out:8
    display_success_message  CC=1  out:3
    hooks_install  CC=2  out:6
    hooks_run  CC=2  out:6
    hooks_uninstall  CC=2  out:5
  goal.cli.license_cmd  [5 funcs]
    license_check  CC=2  out:10
    license_create  CC=6  out:21
    license_info  CC=6  out:19
    license_list  CC=7  out:20
    license_update  CC=3  out:13
  goal.cli.publish  [2 funcs]
    makefile_has_target  CC=4  out:6
    publish_project  CC=14  out:22
  goal.cli.publish_cmd  [2 funcs]
    _publish_impl  CC=8  out:16
    publish  CC=2  out:5
  goal.cli.recover_cmd  [2 funcs]
    _get_error_output  CC=5  out:4
    recover  CC=6  out:23
  goal.cli.tests  [20 funcs]
    _active_venv_python  CC=3  out:4
    _build_python_test_command  CC=11  out:10
    _coerce_python_strategy_to_project_pytest  CC=8  out:3
    _display_test_error  CC=9  out:18
    _ensure_root_pytest_or_mark_failed  CC=10  out:14
    _get_project_strategy  CC=7  out:5
    _has_package  CC=3  out:1
    _prefer_uv_run  CC=2  out:1
    _pytest_importable  CC=2  out:2
    _resolve_project_python  CC=4  out:6
  goal.cli.tests_discovery  [5 funcs]
    _find_project_root  CC=5  out:4
    _has_project_marker  CC=2  out:3
    _has_usable_test_script  CC=7  out:4
    find_nodejs_test_dirs  CC=6  out:8
    find_python_test_dirs  CC=9  out:16
  goal.cli.tests_pytest_setup  [3 funcs]
    _is_uv_project  CC=1  out:1
    _try_uv_install  CC=4  out:2
    ensure_pytest_for_project  CC=9  out:13
  goal.cli.utils_cmd  [8 funcs]
    bootstrap  CC=4  out:11
    check_versions  CC=2  out:12
    clone  CC=4  out:15
    info  CC=2  out:13
    init  CC=4  out:12
    package_managers  CC=8  out:16
    status  CC=10  out:21
    version  CC=2  out:14
  goal.cli.version_sync  [1 funcs]
    sync_all_versions  CC=1  out:11
  goal.cli.version_utils  [21 funcs]
    _build_author_block  CC=5  out:6
    _update_author_section  CC=3  out:8
    _update_license_section  CC=5  out:8
    _update_package_json_metadata  CC=4  out:3
    _update_pyproject_metadata  CC=2  out:2
    _update_pyproject_with_regex  CC=1  out:3
    _update_pyproject_with_tomlkit  CC=4  out:5
    _update_regex_authors  CC=3  out:5
    _update_regex_classifier  CC=2  out:1
    _update_regex_license  CC=3  out:6
  goal.cli.wizard_cmd  [5 funcs]
    _find_git_root  CC=3  out:2
    _setup_git_repository  CC=10  out:33
    _setup_project_config  CC=9  out:55
    _setup_user_config  CC=12  out:39
    _show_setup_summary  CC=7  out:39
  goal.cli_helpers  [3 funcs]
    confirm  CC=6  out:6
    split_paths_by_type  CC=14  out:17
    stage_paths  CC=5  out:4
  goal.commit_generator  [3 funcs]
    display_commit_message  CC=1  out:2
    display_detailed_message  CC=1  out:2
    print_detailed_message  CC=2  out:3
  goal.config.manager  [2 funcs]
    ensure_config  CC=5  out:8
    init_config  CC=3  out:4
  goal.config.validation  [2 funcs]
    validate_config_file  CC=11  out:25
    validate_config_interactive  CC=10  out:22
  goal.deep_analyzer  [4 funcs]
    _analyze_generic_diff  CC=1  out:6
    _analyze_js_diff  CC=13  out:12
    _analyze_python_diff  CC=10  out:29
    _detect_functional_areas  CC=7  out:12
  goal.deep_analyzer_aggregate  [2 funcs]
    aggregate_changes  CC=3  out:16
    detect_relations  CC=6  out:8
  goal.dependency_update  [7 funcs]
    _iter_project_marker_files  CC=6  out:3
    _path_has_skipped_dir  CC=1  out:2
    _run_update_command  CC=4  out:8
    _select_managers_to_update  CC=21  out:22
    _update_dependencies_in_root  CC=12  out:23
    discover_dependency_project_roots  CC=7  out:19
    update_project_dependencies  CC=13  out:20
  goal.formatter  [16 funcs]
    _add_optional_sections  CC=3  out:2
    _build_capabilities_content  CC=4  out:1
    _build_details_content  CC=3  out:0
    _build_enhanced_summary_section  CC=9  out:6
    _build_files_section  CC=8  out:12
    _build_functional_overview  CC=12  out:13
    _build_roles_content  CC=4  out:1
    _determine_next_steps  CC=4  out:0
    _format_complexity_metric  CC=6  out:3
    _format_metrics_section  CC=5  out:9
  goal.generator.analyzer  [1 funcs]
    extract_functions_changed  CC=3  out:10
  goal.generator.generator  [2 funcs]
    _classify_files  CC=11  out:7
    generate_smart_commit_message  CC=1  out:2
  goal.git_ops  [28 funcs]
    _echo_cmd  CC=3  out:6
    _handle_clone  CC=3  out:7
    _handle_init_remote  CC=5  out:25
    _handle_local_init  CC=2  out:5
    _handle_merge_strategy  CC=8  out:25
    _list_remote_branches  CC=5  out:9
    _prompt_remote_url  CC=3  out:12
    _run_git_verbose  CC=11  out:16
    _select_branch  CC=3  out:9
    apply_ticket_prefix  CC=6  out:5
  goal.hooks.manager  [1 funcs]
    run_validation  CC=4  out:4
  goal.io.stdio  [9 funcs]
    echo_auto  CC=2  out:4
    echo_command_block  CC=2  out:4
    echo_heading  CC=2  out:4
    echo_info  CC=2  out:3
    echo_output_block  CC=3  out:5
    echo_status_warn  CC=2  out:4
    echo_via_markdown  CC=2  out:3
    set_stdio_markdown  CC=1  out:1
    use_markdown_stdio  CC=2  out:0
  goal.license.manager  [2 funcs]
    create_license_file  CC=10  out:21
    update_license_file  CC=7  out:13
  goal.license.spdx  [3 funcs]
    check_compatibility  CC=14  out:8
    get_license_info  CC=4  out:4
    validate_spdx_id  CC=11  out:13
  goal.package_managers  [15 funcs]
    _detect_package_manager  CC=2  out:2
    _has_any_matching_path  CC=2  out:2
    _has_language_extension  CC=2  out:3
    _path_matches  CC=2  out:4
    _pip_update_all_command  CC=6  out:3
    detect_package_managers  CC=3  out:4
    detect_project_language  CC=3  out:3
    get_available_package_managers  CC=3  out:2
    get_package_manager_info  CC=1  out:1
    get_package_managers_by_language  CC=3  out:1
  goal.project_bootstrap  [1 funcs]
    bootstrap_project  CC=1  out:5
  goal.publish.changes  [8 funcs]
    _basename  CC=1  out:1
    _is_metadata_file  CC=7  out:6
    _is_publishable_for_type  CC=12  out:12
    _is_test_path  CC=6  out:7
    _matches_any  CC=5  out:4
    _normalize_path  CC=1  out:3
    _suffix  CC=1  out:2
    analyze_publishable_changes  CC=8  out:8
  goal.publish.github_fallback  [2 funcs]
    _publishing_section  CC=10  out:6
    get_github_release_config  CC=15  out:23
  goal.push.core  [17 funcs]
    _apply_enhanced_quality_gates  CC=6  out:6
    _bootstrap_projects  CC=5  out:3
    _detect_and_bootstrap_projects  CC=1  out:2
    _detect_project_types  CC=2  out:4
    _handle_commit_phase  CC=8  out:19
    _handle_no_changes  CC=4  out:6
    _handle_no_files  CC=3  out:1
    _initialize_context  CC=3  out:3
    _maybe_show_workflow_preview  CC=2  out:1
    _run_test_stage_or_exit  CC=3  out:4
  goal.push.stages.changelog  [1 funcs]
    handle_changelog  CC=2  out:4
  goal.push.stages.commit  [8 funcs]
    _build_validation_summary  CC=1  out:1
    _commit_file_group  CC=5  out:14
    _commit_release_metadata  CC=5  out:16
    _confirm_suggested_title  CC=4  out:1
    enforce_quality_gates  CC=10  out:14
    get_commit_message  CC=11  out:21
    handle_single_commit  CC=7  out:7
    handle_split_commits  CC=14  out:22
  goal.push.stages.costs  [3 funcs]
    _compute_ai_costs  CC=8  out:10
    _is_cost_tracking_enabled  CC=4  out:8
    update_cost_badges  CC=11  out:25
  goal.push.stages.dry_run  [4 funcs]
    _build_split_plan_body  CC=8  out:13
    _format_markdown_dry_run  CC=4  out:7
    _print_plain_dry_run  CC=4  out:13
    handle_dry_run  CC=5  out:6
  goal.push.stages.publish  [2 funcs]
    _format_skip_message  CC=9  out:19
    handle_publish  CC=15  out:24
  goal.push.stages.push_remote  [17 funcs]
    _execute_recovery  CC=3  out:11
    _handle_automatic_recovery  CC=4  out:13
    _handle_force_push  CC=4  out:19
    _handle_large_file_error  CC=6  out:16
    _handle_large_files_in_history  CC=2  out:18
    _handle_large_files_staged  CC=2  out:5
    _handle_pull_merge  CC=3  out:12
    _handle_push_failure  CC=5  out:16
    _handle_recovery_choice  CC=5  out:8
    _handle_view_diff  CC=6  out:18
  goal.push.stages.tag  [1 funcs]
    create_tag  CC=4  out:8
  goal.push.stages.test  [1 funcs]
    run_test_stage  CC=9  out:23
  goal.push.stages.todo  [1 funcs]
    handle_todo_stage  CC=14  out:32
  goal.push.stages.version  [4 funcs]
    _get_version_module  CC=1  out:0
    get_version_info  CC=2  out:3
    handle_version_sync  CC=3  out:10
    sync_all_versions_wrapper  CC=1  out:2
  goal.recovery.large_file  [5 funcs]
    _extract_file_paths  CC=8  out:9
    _move_to_lfs  CC=4  out:13
    _remove_large_files  CC=6  out:17
    _skip_large_files  CC=2  out:5
    _run_git_chunked  CC=4  out:4
  goal.summary.generator  [1 funcs]
    detect_capabilities  CC=5  out:7
  goal.summary.quality_filter  [3 funcs]
    dedupe_files  CC=3  out:4
    dedupe_relations  CC=4  out:5
    has_banned_words  CC=4  out:5
  goal.summary.validator  [1 funcs]
    _validate_title  CC=10  out:21
  goal.toml_validation  [4 funcs]
    check_pyproject_toml  CC=3  out:3
    get_tomllib  CC=3  out:0
    validate_project_toml_files  CC=4  out:4
    validate_toml_file  CC=9  out:19
  goal.user_config  [7 funcs]
    set  CC=1  out:1
    get_git_user_email  CC=3  out:2
    get_git_user_name  CC=3  out:2
    get_user_config  CC=2  out:3
    initialize_user_config  CC=11  out:52
    prompt_for_license  CC=4  out:25
    show_user_config  CC=2  out:31
  goal.validators.dot_folders  [6 funcs]
    _is_dot_path  CC=3  out:3
    _is_safe_path  CC=3  out:1
    _is_whitelisted_path  CC=4  out:5
    _matches_problematic  CC=4  out:4
    check_dot_folders  CC=9  out:12
    manage_dot_folders  CC=9  out:18
  goal.validators.file_validator  [8 funcs]
    _check_file_for_tokens  CC=3  out:4
    _get_deleted_staged_files  CC=4  out:6
    _handle_oversized_file  CC=3  out:3
    _is_excluded  CC=3  out:3
    get_file_size_mb  CC=2  out:1
    handle_large_files  CC=5  out:14
    validate_files  CC=12  out:9
    validate_staged_files  CC=14  out:13
  goal.validators.gitignore  [2 funcs]
    load_gitignore  CC=6  out:9
    save_gitignore  CC=8  out:11
  goal.validators.tokens  [9 funcs]
    _calculate_entropy  CC=5  out:4
    _classify_token  CC=3  out:0
    _extract_token_value  CC=4  out:3
    _get_entropy_threshold  CC=1  out:1
    _is_dummy_value  CC=8  out:7
    detect_tokens_in_content  CC=10  out:13
    get_default_token_patterns  CC=1  out:0
    migrate_token_patterns  CC=1  out:1
    resolve_token_patterns  CC=7  out:3
  goal.version_validation  [6 funcs]
    _validate_single_type  CC=4  out:3
    check_readme_badges  CC=5  out:4
    extract_badge_versions  CC=4  out:10
    format_validation_results  CC=5  out:5
    get_pypi_version  CC=2  out:6
    validate_project_versions  CC=2  out:1
  integration.run_matrix  [1 funcs]
    print  CC=0  out:0

EDGES:
  examples.dotnet-project.Calculator.Program.Main → examples.dotnet-project.Calculator.Calculator.Add
  examples.webhooks.slack-webhook.send_slack_notification → integration.run_matrix.print
  examples.webhooks.slack-webhook.main → examples.webhooks.slack-webhook.send_slack_notification
  examples.webhooks.slack-webhook.main → integration.run_matrix.print
  examples.webhooks.discord-webhook.send_discord_notification → integration.run_matrix.print
  examples.webhooks.discord-webhook.main → examples.webhooks.discord-webhook.send_discord_notification
  examples.webhooks.discord-webhook.main → integration.run_matrix.print
  examples.custom-hooks.post-commit.notify_slack → integration.run_matrix.print
  examples.custom-hooks.post-commit.update_changelog → integration.run_matrix.print
  examples.custom-hooks.post-commit.log_to_file → integration.run_matrix.print
  examples.custom-hooks.post-commit.main → integration.run_matrix.print
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.get_commit_info
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.notify_slack
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.update_changelog
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.log_to_file
  examples.custom-hooks.pre-publish.test_build → integration.run_matrix.print
  examples.custom-hooks.pre-publish.test_install → integration.run_matrix.print
  examples.custom-hooks.pre-publish.check_version → integration.run_matrix.print
  examples.custom-hooks.pre-publish.run_security_check → integration.run_matrix.print
  examples.custom-hooks.pre-publish.main → integration.run_matrix.print
  examples.custom-hooks.pre-commit.main → integration.run_matrix.print
  examples.custom-hooks.pre-commit.main → examples.custom-hooks.pre-commit.check_secrets
  examples.custom-hooks.pre-commit.main → examples.custom-hooks.pre-commit.check_file_sizes
  examples.custom-hooks.pre-commit.main → examples.custom-hooks.pre-commit.run_tests
  examples.api-usage.04_version_validation.main → integration.run_matrix.print
  examples.api-usage.04_version_validation.main → goal.cli.version_utils.get_current_version
  examples.api-usage.04_version_validation.main → goal.version_validation.get_pypi_version
  examples.api-usage.04_version_validation.main → goal.cli.version_utils.detect_project_types
  examples.api-usage.05_programmatic_workflow.run_custom_workflow → integration.run_matrix.print
  examples.api-usage.05_programmatic_workflow.create_minimal_workflow → integration.run_matrix.print
  examples.api-usage.01_basic_api.main → integration.run_matrix.print
  examples.api-usage.01_basic_api.main → goal.cli.version_utils.detect_project_types
  examples.api-usage.01_basic_api.main → goal.cli.version_utils.get_current_version
  examples.api-usage.03_commit_generation.main → integration.run_matrix.print
  examples.api-usage.03_commit_generation.main → goal.git_ops.get_staged_files
  examples.api-usage.03_commit_generation.main → goal.git_ops.get_diff_content
  examples.api-usage.02_git_operations._check_git_repository → integration.run_matrix.print
  examples.api-usage.02_git_operations._check_git_repository → goal.git_ops.is_git_repository
  examples.api-usage.02_git_operations._display_staged_files → integration.run_matrix.print
  examples.api-usage.02_git_operations._display_staged_files → goal.git_ops.get_staged_files
  examples.api-usage.02_git_operations._display_unstaged_files → integration.run_matrix.print
  examples.api-usage.02_git_operations._display_unstaged_files → goal.git_ops.get_unstaged_files
  examples.api-usage.02_git_operations._display_diff_stats → integration.run_matrix.print
  examples.api-usage.02_git_operations._display_diff_stats → goal.git_ops.get_diff_stats
  examples.api-usage.02_git_operations._display_diff_content → integration.run_matrix.print
  examples.api-usage.02_git_operations._display_diff_content → goal.git_ops.get_diff_content
  examples.api-usage.02_git_operations.main → integration.run_matrix.print
  examples.api-usage.02_git_operations.main → examples.api-usage.02_git_operations._display_staged_files
  examples.api-usage.02_git_operations.main → examples.api-usage.02_git_operations._display_unstaged_files
  examples.api-usage.02_git_operations.main → examples.api-usage.02_git_operations._display_diff_stats
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (2)

**`CLI Command Tests`**

**`Functional probes derived from pytest coverage areas`**

## Intent

Goal - Automated git push with enterprise-grade commit intelligence, smart conventional commit generation based on deep code analysis, and interactive release workflow management.

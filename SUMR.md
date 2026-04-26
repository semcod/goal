# Goal

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `goal`
- **version**: `2.1.197`
- **python_requires**: `>=3.8`
- **license**: Apache-2.0
- **ai_model**: `openrouter/x-ai/grok-code-fast-1`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, testql(2), app.doql.less, pyqual.yaml, goal.yaml, .env.example, src(15 mod), project/(6 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: goal;
  version: 2.1.197;
}

dependencies {
  runtime: "click>=8.0.0, PyYAML>=6.0, clickmd>=0.1.0, costs>=0.1.21";
  dev: "pytest>=7.0.0, build, twine, pfix>=0.1.60, tox>=4.0.0";
}

interface[type="cli"] {
  framework: click;
}
interface[type="cli"] page[name="goal"] {

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
  step-9: run cmd=case "$(PART)" in \;
  step-10: run cmd=major) major=$$((major + 1)); minor=0; patch=0 ;; \;
  step-11: run cmd=minor) minor=$$((minor + 1)); patch=0 ;; \;
  step-12: run cmd=patch) patch=$$((patch + 1)) ;; \;
  step-13: run cmd=*) echo "${YELLOW}Error: PART must be major, minor, or patch${RESET}"; exit 1 ;; \;
  step-14: run cmd=esac; \;
  step-15: run cmd=new_version="$${major}.$${minor}.$${patch}"; \;
  step-16: run cmd=sed -i "s/^version = \"$$current_version\"/version = \"$$new_version\"/" pyproject.toml; \;
  step-17: run cmd=echo "${GREEN}Version bumped to $$new_version${RESET}"; \;
  step-18: run cmd=git add pyproject.toml; \;
  step-19: run cmd=git commit -m "Bump version to $$new_version"; \;
  step-20: run cmd=if git rev-parse "v$$new_version" >/dev/null 2>&1; then \;
  step-21: run cmd=echo "${YELLOW}Error: tag 'v$$new_version' already exists${RESET}"; \;
  step-22: run cmd=exit 1; \;
  step-23: run cmd=fi; \;
  step-24: run cmd=git tag -a "v$$new_version" -m "Version $$new_version"; \;
  step-25: run cmd=echo "${GREEN}Created tag v$$new_version${RESET}";
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

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  python_version: >=3.8;
}
```

### Source Modules

- `goal.changelog`
- `goal.cli`
- `goal.commit_generator`
- `goal.config`
- `goal.deep_analyzer`
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

## Workflows

### Taskfile Tasks (`Taskfile.yml`)

```yaml markpact:taskfile path=Taskfile.yml
version: '1'
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

## Dependencies

### Runtime

```text markpact:deps python
click>=8.0.0
PyYAML>=6.0
clickmd>=0.1.0
costs>=0.1.21
```

### Development

```text markpact:deps python scope=dev
pytest>=7.0.0
build
twine
pfix>=0.1.60
tox>=4.0.0
```

## Source Map

*Top 5 modules by symbol density — signatures for LLM orientation.*

### `goal.project_bootstrap` (`goal/project_bootstrap.py`)

```python
def _match_marker(base, pattern)  # CC=2, fan=4
def detect_project_types_deep(root, max_depth)  # CC=11, fan=10 ⚠
def _guess_python_name(project_dir)  # CC=5, fan=5
def _guess_nodejs_name(project_dir)  # CC=4, fan=5
def _guess_rust_name(project_dir)  # CC=4, fan=4
def _guess_go_name(project_dir)  # CC=4, fan=6
def guess_package_name(project_dir, project_type)  # CC=3, fan=4
def _find_python_bin(project_dir)  # CC=5, fan=4
def _read_openrouter_api_key(env_file)  # CC=11, fan=6 ⚠
def _find_openrouter_api_key(project_dir)  # CC=6, fan=5
def _find_git_root(project_dir)  # CC=3, fan=2
def _ensure_python_test_dependency(project_dir, python_bin, test_dep)  # CC=5, fan=5
def _ensure_python_env(project_dir, cfg, yes)  # CC=5, fan=12
def _should_skip_install(project_dir, markers)  # CC=6, fan=2
def _install_python_deps(project_dir, cfg, python_bin)  # CC=12, fan=17 ⚠
def _install_python_deps_broker(project_dir, extras)  # CC=2, fan=5
def _ensure_generic_env(project_dir, project_type, cfg, yes)  # CC=14, fan=10 ⚠
def ensure_project_environment(project_dir, project_type, yes)  # CC=3, fan=4
def find_existing_tests(project_dir, project_type)  # CC=5, fan=4
def _resolve_scaffold_test_path(project_dir, project_type, cfg, package_name)  # CC=3, fan=2
def scaffold_test(project_dir, project_type, yes)  # CC=8, fan=12
def _new_bootstrap_result(project_dir, project_type)  # CC=1, fan=0
def _run_bootstrap_diagnostics(project_dir, project_type, yes)  # CC=1, fan=3
def _ensure_bootstrap_tests(project_dir, project_type, yes)  # CC=3, fan=2
def bootstrap_project(project_dir, project_type, yes)  # CC=1, fan=5
def bootstrap_all_projects(root, yes)  # CC=6, fan=9
def _install_costs_package(project_dir, python_bin)  # CC=3, fan=5
def _load_costs_api()  # CC=2, fan=6
def _calculate_ai_costs(repo_root)  # CC=9, fan=8
def _read_model_from_pyproject(project_dir)  # CC=3, fan=4
def _generate_costs_badge(project_dir)  # CC=6, fan=13
def _ensure_costs_installed(project_dir, python_bin)  # CC=2, fan=4
def _add_deps_to_section(match, required_deps)  # CC=10, fan=9 ⚠
def _try_add_deps(content)  # CC=11, fan=4 ⚠
def _ensure_costs_config(project_dir)  # CC=5, fan=8
def _ensure_env_template(project_dir)  # CC=6, fan=7
def _ensure_pfix_env(project_dir)  # CC=7, fan=8
def _validate_pfix_env(project_dir)  # CC=4, fan=4
def _ensure_pfix_installed(project_dir, yes)  # CC=4, fan=9
def _ensure_pfix_config(project_dir, yes)  # CC=4, fan=6
```

### `goal.git_ops` (`goal/git_ops.py`)

```python
def run_git()  # CC=1, fan=2
def run_command(command, capture)  # CC=1, fan=1
def _echo_cmd(args)  # CC=2, fan=4
def _run_git_verbose()  # CC=8, fan=7
def run_git_with_status()  # CC=11, fan=6 ⚠
def run_command_tee(command)  # CC=3, fan=7
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

### `goal.deep_analyzer` (`goal/deep_analyzer.py`)

```python
class CodeChangeAnalyzer:  # Analyzes code changes to extract functional meaning.
    def __init__()  # CC=1
    def analyze_file_diff(filepath, old_content, new_content)  # CC=3
    def _detect_language(filepath)  # CC=1
    def _analyze_python_diff(old_content, new_content)  # CC=10 ⚠
    def _detect_value_indicators(added_entities)  # CC=6
    def _extract_python_entities(tree)  # CC=13 ⚠
    def _get_decorator_name(decorator)  # CC=4
    def _calculate_complexity(node)  # CC=4
    def _analyze_js_diff(old_content, new_content)  # CC=13 ⚠
    def _analyze_generic_diff(old_content, new_content)  # CC=1
    def _detect_functional_areas(entities, content)  # CC=7
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

### `goal.formatter` (`goal/formatter.py`)

```python
def _build_functional_overview(features, summary, entities, files, stats, current_version, new_version, commit_msg, project_types)  # CC=12, fan=5 ⚠
def _build_files_section(formatter, files, stats, analysis)  # CC=8, fan=6
def _determine_next_steps(error, test_exit_code, new_version)  # CC=4, fan=0
def format_push_result(project_types, files, stats, current_version, new_version, commit_msg, commit_body, test_result, test_exit_code, actions, error, analysis)  # CC=13, fan=16 ⚠
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
def format_package_manager_command(pm, command_type)  # CC=3, fan=3
def get_package_manager_info(pm)  # CC=1, fan=1
def list_all_package_managers()  # CC=2, fan=2
def detect_project_language(project_path)  # CC=3, fan=3
def suggest_package_managers(project_path)  # CC=5, fan=7
class PackageManager:  # Package manager configuration and capabilities.
    def __post_init__()  # CC=2
```

## Call Graph

*380 nodes · 500 edges · 78 modules · CC̄=0.2*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in Taskfile)* | 0 | 255 | 0 | **255** |
| `any` *(in testql-scenarios.generated-from-pytests.testql.toon)* | 0 | 65 | 0 | **65** |
| `_setup_project_config` *(in goal.cli.wizard_cmd)* | 9 | 1 | 55 | **56** |
| `initialize_user_config` *(in goal.user_config)* | 11 ⚠ | 4 | 52 | **56** |
| `run_git` *(in goal.git_ops)* | 1 | 47 | 2 | **49** |
| `validate` *(in goal.cli.commit_cmd)* | 13 ⚠ | 0 | 45 | **45** |
| `sum` *(in project.map.toon)* | 0 | 44 | 0 | **44** |
| `_show_setup_summary` *(in goal.cli.wizard_cmd)* | 7 | 1 | 39 | **40** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/goal
# nodes: 380 | edges: 500 | modules: 78
# CC̄=0.2

HUBS[20]:
  Taskfile.print
    CC=0  in:255  out:0  total:255
  testql-scenarios.generated-from-pytests.testql.toon.any
    CC=0  in:65  out:0  total:65
  goal.cli.wizard_cmd._setup_project_config
    CC=9  in:1  out:55  total:56
  goal.user_config.initialize_user_config
    CC=11  in:4  out:52  total:56
  goal.git_ops.run_git
    CC=1  in:47  out:2  total:49
  goal.cli.commit_cmd.validate
    CC=13  in:0  out:45  total:45
  project.map.toon.sum
    CC=0  in:44  out:0  total:44
  goal.cli.wizard_cmd._show_setup_summary
    CC=7  in:1  out:39  total:40
  goal.cli.wizard_cmd._setup_user_config
    CC=12  in:1  out:39  total:40
  goal.user_config.UserConfig.set
    CC=1  in:38  out:1  total:39
  goal.cli.commit_cmd.fix_summary
    CC=12  in:0  out:38  total:38
  examples.api-usage.02_git_operations.main
    CC=15  in:0  out:38  total:38
  goal.cli.doctor_cmd.doctor
    CC=12  in:0  out:36  total:36
  examples.api-usage.01_basic_api.main
    CC=10  in:0  out:34  total:34
  project.map.toon.list
    CC=0  in:34  out:0  total:34
  goal.cli.wizard_cmd._setup_git_repository
    CC=10  in:1  out:33  total:34
  goal.user_config.show_user_config
    CC=2  in:1  out:31  total:32
  goal.push.core.execute_push_workflow
    CC=6  in:2  out:29  total:31
  examples.api-usage.04_version_validation.main
    CC=11  in:0  out:30  total:30
  goal.deep_analyzer.CodeChangeAnalyzer._analyze_python_diff
    CC=10  in:0  out:29  total:29

MODULES:
  Taskfile  [1 funcs]
    print  CC=0  out:0
  examples.api-usage.01_basic_api  [1 funcs]
    main  CC=10  out:34
  examples.api-usage.02_git_operations  [1 funcs]
    main  CC=15  out:38
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
  examples.testing.03_advanced_mocking  [7 funcs]
    test_conditional_mocking  CC=1  out:8
    test_mock_context_manager  CC=2  out:13
    test_mocking_click_interactions  CC=2  out:14
    test_mocking_external_services  CC=3  out:10
    test_mocking_file_system  CC=1  out:3
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
  goal.changelog  [6 funcs]
    _build_domain_entry  CC=7  out:12
    _build_simple_entry  CC=3  out:4
    _classify_file_domain  CC=5  out:4
    _find_unreleased_insert_pos  CC=3  out:6
    _insert_entry  CC=5  out:3
    update_changelog  CC=5  out:12
  goal.cli  [9 funcs]
    parse_args  CC=6  out:4
    _auto_update_goal  CC=3  out:9
    _configure_main_context  CC=3  out:4
    _format_import_warning_message  CC=1  out:0
    _print_import_warning  CC=1  out:2
    _show_goal_version_banner  CC=8  out:14
    confirm  CC=6  out:6
    split_paths_by_type  CC=14  out:17
    stage_paths  CC=5  out:4
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
    doctor  CC=12  out:36
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
  goal.cli.publish  [8 funcs]
    _ensure_publish_deps  CC=5  out:20
    _get_configured_project_types  CC=13  out:13
    _get_project_strategy  CC=7  out:5
    _get_python_bin  CC=3  out:4
    _prepare_python_publish  CC=7  out:15
    _run_publish_command  CC=8  out:14
    makefile_has_target  CC=4  out:6
    publish_project  CC=13  out:21
  goal.cli.publish_cmd  [2 funcs]
    _publish_impl  CC=8  out:16
    publish  CC=2  out:5
  goal.cli.recover_cmd  [2 funcs]
    _get_error_output  CC=5  out:4
    recover  CC=6  out:23
  goal.cli.tests  [8 funcs]
    _find_nodejs_test_dirs  CC=6  out:8
    _find_project_root  CC=5  out:4
    _find_python_test_dirs  CC=11  out:9
    _has_project_marker  CC=2  out:3
    _has_usable_test_script  CC=7  out:4
    _run_subdir_test  CC=13  out:24
    _run_tests_in_subdirs  CC=5  out:8
    run_tests  CC=10  out:10
  goal.cli.utils_cmd  [8 funcs]
    bootstrap  CC=4  out:11
    check_versions  CC=2  out:12
    clone  CC=4  out:15
    info  CC=2  out:13
    init  CC=4  out:12
    package_managers  CC=8  out:16
    status  CC=10  out:21
    version  CC=2  out:14
  goal.cli.version_sync  [9 funcs]
    _update_cargo_version  CC=6  out:8
    _update_csproj_versions  CC=3  out:7
    _update_init_py_versions  CC=7  out:9
    _update_json_version_file  CC=6  out:6
    _update_pom_xml  CC=3  out:6
    _update_readme_metadata  CC=7  out:6
    _update_toml_version  CC=6  out:8
    _update_version_file  CC=1  out:3
    sync_all_versions  CC=1  out:9
  goal.cli.version_utils  [12 funcs]
    _build_author_block  CC=5  out:6
    _update_package_json_metadata  CC=4  out:3
    _update_pyproject_metadata  CC=4  out:8
    _update_setup_py_metadata  CC=1  out:3
    bump_version  CC=5  out:9
    detect_project_types  CC=6  out:8
    find_version_files  CC=6  out:9
    get_current_version  CC=5  out:7
    get_version_from_file  CC=3  out:3
    update_json_version  CC=3  out:4
  goal.cli.wizard_cmd  [5 funcs]
    _find_git_root  CC=3  out:2
    _setup_git_repository  CC=10  out:33
    _setup_project_config  CC=9  out:55
    _setup_user_config  CC=12  out:39
    _show_setup_summary  CC=7  out:39
  goal.commit_generator  [3 funcs]
    display_commit_message  CC=1  out:2
    display_detailed_message  CC=1  out:2
    print_detailed_message  CC=2  out:3
  goal.config.manager  [8 funcs]
    _detect_project_types  CC=6  out:8
    load  CC=5  out:7
    save  CC=3  out:6
    set  CC=4  out:2
    update_from_detection  CC=4  out:11
    ensure_config  CC=5  out:8
    init_config  CC=3  out:4
    load_config  CC=1  out:2
  goal.config.validation  [2 funcs]
    validate_config_file  CC=11  out:25
    validate_config_interactive  CC=10  out:22
  goal.deep_analyzer  [12 funcs]
    _analyze_generic_diff  CC=1  out:6
    _analyze_js_diff  CC=13  out:12
    _analyze_python_diff  CC=10  out:29
    _check_architecture_value  CC=4  out:4
    _check_cli_value  CC=8  out:4
    _detect_file_patterns  CC=6  out:10
    _detect_functional_areas  CC=7  out:12
    _detect_value_indicators  CC=6  out:8
    _extract_python_entities  CC=13  out:17
    aggregate_changes  CC=3  out:16
  goal.formatter  [15 funcs]
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
  goal.generator.analyzer  [17 funcs]
    _has_new_goal_python_file  CC=4  out:3
    _has_package_code  CC=7  out:7
    _is_ci_only  CC=4  out:4
    _is_docs_only  CC=4  out:3
    _resolve_change_type  CC=11  out:10
    _score_by_statistics  CC=8  out:3
    _score_package_signals  CC=2  out:2
    _score_path_signals  CC=9  out:2
    _score_text_signals  CC=3  out:2
    detect_scope  CC=14  out:12
  goal.generator.generator  [3 funcs]
    _classify_files  CC=11  out:7
    generate_enhanced_summary  CC=8  out:14
    generate_smart_commit_message  CC=1  out:2
  goal.git_ops  [28 funcs]
    _echo_cmd  CC=2  out:5
    _handle_clone  CC=3  out:7
    _handle_init_remote  CC=5  out:25
    _handle_local_init  CC=2  out:5
    _handle_merge_strategy  CC=8  out:25
    _list_remote_branches  CC=5  out:9
    _prompt_remote_url  CC=3  out:12
    _run_git_verbose  CC=8  out:13
    _select_branch  CC=3  out:9
    apply_ticket_prefix  CC=6  out:5
  goal.hooks.config  [1 funcs]
    get_hook_config  CC=8  out:7
  goal.hooks.manager  [2 funcs]
    create_precommit_config  CC=3  out:9
    run_validation  CC=4  out:4
  goal.license.manager  [2 funcs]
    create_license_file  CC=10  out:21
    update_license_file  CC=7  out:13
  goal.license.spdx  [3 funcs]
    check_compatibility  CC=14  out:8
    get_license_info  CC=4  out:4
    validate_spdx_id  CC=11  out:13
  goal.package_managers  [13 funcs]
    _detect_package_manager  CC=2  out:2
    _has_any_matching_path  CC=2  out:2
    _has_language_extension  CC=2  out:3
    _path_matches  CC=2  out:4
    detect_package_managers  CC=3  out:4
    detect_project_language  CC=3  out:3
    get_available_package_managers  CC=3  out:2
    get_package_manager_info  CC=1  out:1
    get_package_managers_by_language  CC=3  out:1
    get_preferred_package_manager  CC=5  out:1
  goal.postcommit.manager  [1 funcs]
    get_config  CC=5  out:3
  goal.project_bootstrap  [3 funcs]
    _find_python_bin  CC=5  out:6
    bootstrap_project  CC=1  out:5
    detect_project_types_deep  CC=11  out:11
  goal.push.core  [14 funcs]
    _apply_enhanced_quality_gates  CC=6  out:6
    _detect_and_bootstrap_projects  CC=7  out:7
    _handle_commit_phase  CC=8  out:19
    _handle_no_changes  CC=4  out:6
    _handle_no_files  CC=3  out:1
    _initialize_context  CC=3  out:2
    _maybe_show_workflow_preview  CC=2  out:1
    _run_test_stage_or_exit  CC=3  out:4
    _validate_staged_files  CC=6  out:18
    _validate_toml_or_exit  CC=3  out:6
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
  goal.push.stages.publish  [1 funcs]
    handle_publish  CC=6  out:15
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
    run_test_stage  CC=9  out:24
  goal.push.stages.todo  [1 funcs]
    handle_todo_stage  CC=10  out:22
  goal.push.stages.version  [4 funcs]
    _get_version_module  CC=1  out:0
    get_version_info  CC=2  out:3
    handle_version_sync  CC=3  out:10
    sync_all_versions_wrapper  CC=1  out:2
  goal.recovery.auth  [1 funcs]
    can_handle  CC=2  out:2
  goal.recovery.base  [1 funcs]
    run_git  CC=2  out:5
  goal.recovery.corrupted  [1 funcs]
    can_handle  CC=2  out:2
  goal.recovery.divergent  [1 funcs]
    can_handle  CC=2  out:2
  goal.recovery.force_push  [1 funcs]
    can_handle  CC=2  out:2
  goal.recovery.large_file  [6 funcs]
    _extract_file_paths  CC=8  out:9
    _move_to_lfs  CC=4  out:13
    _remove_large_files  CC=6  out:17
    _skip_large_files  CC=2  out:5
    can_handle  CC=2  out:2
    _run_git_chunked  CC=4  out:4
  goal.recovery.lfs  [1 funcs]
    can_handle  CC=2  out:2
  goal.recovery.manager  [2 funcs]
    _ensure_recovery_dir  CC=3  out:8
    run_git  CC=2  out:5
  goal.summary.validator  [1 funcs]
    _validate_title  CC=10  out:21
  goal.toml_validation  [4 funcs]
    check_pyproject_toml  CC=3  out:3
    get_tomllib  CC=3  out:0
    validate_project_toml_files  CC=4  out:4
    validate_toml_file  CC=9  out:19
  goal.user_config  [9 funcs]
    _load  CC=3  out:3
    _save  CC=2  out:5
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
  goal.validators.file_validator  [7 funcs]
    _check_file_for_tokens  CC=3  out:4
    _handle_oversized_file  CC=3  out:3
    _is_excluded  CC=3  out:3
    get_file_size_mb  CC=2  out:1
    handle_large_files  CC=5  out:14
    validate_files  CC=12  out:8
    validate_staged_files  CC=10  out:11
  goal.validators.gitignore  [2 funcs]
    load_gitignore  CC=6  out:9
    save_gitignore  CC=8  out:11
  goal.validators.tokens  [7 funcs]
    _calculate_entropy  CC=5  out:4
    _classify_token  CC=3  out:0
    _extract_token_value  CC=4  out:3
    _get_entropy_threshold  CC=1  out:1
    _is_dummy_value  CC=8  out:7
    detect_tokens_in_content  CC=10  out:13
    get_default_token_patterns  CC=1  out:0
  goal.version_validation  [7 funcs]
    _validate_single_type  CC=4  out:3
    check_readme_badges  CC=5  out:4
    extract_badge_versions  CC=4  out:10
    format_validation_results  CC=5  out:5
    get_pypi_version  CC=2  out:6
    update_badge_versions  CC=3  out:5
    validate_project_versions  CC=2  out:1
  project.map.toon  [11 funcs]
    ai_cost  CC=0  out:0
    finder  CC=0  out:0
    get_commit_diff  CC=0  out:0
    get_repo_stats  CC=0  out:0
    list  CC=0  out:0
    max  CC=0  out:0
    open  CC=0  out:0
    parse_commits  CC=0  out:0
    patch  CC=0  out:0
    sum  CC=0  out:0
  testql-scenarios.generated-from-pytests.testql.toon  [2 funcs]
    all  CC=0  out:0
    any  CC=0  out:0

EDGES:
  examples.dotnet-project.Calculator.Program.Main → examples.dotnet-project.Calculator.Calculator.Add
  examples.webhooks.slack-webhook.send_slack_notification → Taskfile.print
  examples.webhooks.slack-webhook.main → examples.webhooks.slack-webhook.send_slack_notification
  examples.webhooks.slack-webhook.main → Taskfile.print
  examples.webhooks.discord-webhook.send_discord_notification → Taskfile.print
  examples.webhooks.discord-webhook.main → examples.webhooks.discord-webhook.send_discord_notification
  examples.webhooks.discord-webhook.main → Taskfile.print
  examples.custom-hooks.post-commit.notify_slack → Taskfile.print
  examples.custom-hooks.post-commit.update_changelog → project.map.toon.open
  examples.custom-hooks.post-commit.update_changelog → Taskfile.print
  examples.custom-hooks.post-commit.log_to_file → Taskfile.print
  examples.custom-hooks.post-commit.log_to_file → project.map.toon.open
  examples.custom-hooks.post-commit.main → Taskfile.print
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.get_commit_info
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.notify_slack
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.update_changelog
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.log_to_file
  examples.custom-hooks.pre-publish.test_build → Taskfile.print
  examples.custom-hooks.pre-publish.test_build → project.map.toon.list
  examples.custom-hooks.pre-publish.test_install → Taskfile.print
  examples.custom-hooks.pre-publish.test_install → project.map.toon.list
  examples.custom-hooks.pre-publish.check_version → Taskfile.print
  examples.custom-hooks.pre-publish.check_version → project.map.toon.open
  examples.custom-hooks.pre-publish.run_security_check → Taskfile.print
  examples.custom-hooks.pre-publish.main → Taskfile.print
  examples.custom-hooks.pre-publish.main → testql-scenarios.generated-from-pytests.testql.toon.all
  examples.custom-hooks.pre-commit.main → Taskfile.print
  examples.custom-hooks.pre-commit.main → examples.custom-hooks.pre-commit.check_secrets
  examples.custom-hooks.pre-commit.main → examples.custom-hooks.pre-commit.check_file_sizes
  examples.custom-hooks.pre-commit.main → examples.custom-hooks.pre-commit.run_tests
  examples.api-usage.04_version_validation.main → Taskfile.print
  examples.api-usage.04_version_validation.main → goal.cli.version_utils.get_current_version
  examples.api-usage.04_version_validation.main → goal.version_validation.get_pypi_version
  examples.api-usage.04_version_validation.main → goal.cli.version_utils.detect_project_types
  examples.api-usage.05_programmatic_workflow.run_custom_workflow → Taskfile.print
  examples.api-usage.05_programmatic_workflow.create_minimal_workflow → Taskfile.print
  examples.api-usage.01_basic_api.main → Taskfile.print
  examples.api-usage.01_basic_api.main → goal.cli.version_utils.detect_project_types
  examples.api-usage.01_basic_api.main → goal.cli.version_utils.get_current_version
  examples.api-usage.03_commit_generation.main → Taskfile.print
  examples.api-usage.03_commit_generation.main → goal.git_ops.get_staged_files
  examples.api-usage.03_commit_generation.main → goal.git_ops.get_diff_content
  examples.api-usage.02_git_operations.main → Taskfile.print
  examples.api-usage.02_git_operations.main → goal.git_ops.get_staged_files
  examples.api-usage.02_git_operations.main → goal.git_ops.get_unstaged_files
  examples.validation.run_all_validation.ValidationRunner.run_test → Taskfile.print
  examples.validation.run_all_validation.ValidationRunner.run_all → Taskfile.print
  examples.validation.run_all_validation.ValidationRunner.print_summary → Taskfile.print
  examples.validation.run_all_validation.ValidationRunner.print_summary → project.map.toon.sum
  examples.template-generator.generate.generate_project → Taskfile.print
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**
- assert `repo_dir == "cloned"`
- assert `repo_dir == "cloned"`
- assert `current == '1.0.0'`

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/goal
# nodes: 380 | edges: 500 | modules: 78
# CC̄=0.2

HUBS[20]:
  Taskfile.print
    CC=0  in:255  out:0  total:255
  testql-scenarios.generated-from-pytests.testql.toon.any
    CC=0  in:65  out:0  total:65
  goal.cli.wizard_cmd._setup_project_config
    CC=9  in:1  out:55  total:56
  goal.user_config.initialize_user_config
    CC=11  in:4  out:52  total:56
  goal.git_ops.run_git
    CC=1  in:47  out:2  total:49
  goal.cli.commit_cmd.validate
    CC=13  in:0  out:45  total:45
  project.map.toon.sum
    CC=0  in:44  out:0  total:44
  goal.cli.wizard_cmd._show_setup_summary
    CC=7  in:1  out:39  total:40
  goal.cli.wizard_cmd._setup_user_config
    CC=12  in:1  out:39  total:40
  goal.user_config.UserConfig.set
    CC=1  in:38  out:1  total:39
  goal.cli.commit_cmd.fix_summary
    CC=12  in:0  out:38  total:38
  examples.api-usage.02_git_operations.main
    CC=15  in:0  out:38  total:38
  goal.cli.doctor_cmd.doctor
    CC=12  in:0  out:36  total:36
  examples.api-usage.01_basic_api.main
    CC=10  in:0  out:34  total:34
  project.map.toon.list
    CC=0  in:34  out:0  total:34
  goal.cli.wizard_cmd._setup_git_repository
    CC=10  in:1  out:33  total:34
  goal.user_config.show_user_config
    CC=2  in:1  out:31  total:32
  goal.push.core.execute_push_workflow
    CC=6  in:2  out:29  total:31
  examples.api-usage.04_version_validation.main
    CC=11  in:0  out:30  total:30
  goal.deep_analyzer.CodeChangeAnalyzer._analyze_python_diff
    CC=10  in:0  out:29  total:29

MODULES:
  Taskfile  [1 funcs]
    print  CC=0  out:0
  examples.api-usage.01_basic_api  [1 funcs]
    main  CC=10  out:34
  examples.api-usage.02_git_operations  [1 funcs]
    main  CC=15  out:38
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
  examples.testing.03_advanced_mocking  [7 funcs]
    test_conditional_mocking  CC=1  out:8
    test_mock_context_manager  CC=2  out:13
    test_mocking_click_interactions  CC=2  out:14
    test_mocking_external_services  CC=3  out:10
    test_mocking_file_system  CC=1  out:3
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
  goal.changelog  [6 funcs]
    _build_domain_entry  CC=7  out:12
    _build_simple_entry  CC=3  out:4
    _classify_file_domain  CC=5  out:4
    _find_unreleased_insert_pos  CC=3  out:6
    _insert_entry  CC=5  out:3
    update_changelog  CC=5  out:12
  goal.cli  [9 funcs]
    parse_args  CC=6  out:4
    _auto_update_goal  CC=3  out:9
    _configure_main_context  CC=3  out:4
    _format_import_warning_message  CC=1  out:0
    _print_import_warning  CC=1  out:2
    _show_goal_version_banner  CC=8  out:14
    confirm  CC=6  out:6
    split_paths_by_type  CC=14  out:17
    stage_paths  CC=5  out:4
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
    doctor  CC=12  out:36
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
  goal.cli.publish  [8 funcs]
    _ensure_publish_deps  CC=5  out:20
    _get_configured_project_types  CC=13  out:13
    _get_project_strategy  CC=7  out:5
    _get_python_bin  CC=3  out:4
    _prepare_python_publish  CC=7  out:15
    _run_publish_command  CC=8  out:14
    makefile_has_target  CC=4  out:6
    publish_project  CC=13  out:21
  goal.cli.publish_cmd  [2 funcs]
    _publish_impl  CC=8  out:16
    publish  CC=2  out:5
  goal.cli.recover_cmd  [2 funcs]
    _get_error_output  CC=5  out:4
    recover  CC=6  out:23
  goal.cli.tests  [8 funcs]
    _find_nodejs_test_dirs  CC=6  out:8
    _find_project_root  CC=5  out:4
    _find_python_test_dirs  CC=11  out:9
    _has_project_marker  CC=2  out:3
    _has_usable_test_script  CC=7  out:4
    _run_subdir_test  CC=13  out:24
    _run_tests_in_subdirs  CC=5  out:8
    run_tests  CC=10  out:10
  goal.cli.utils_cmd  [8 funcs]
    bootstrap  CC=4  out:11
    check_versions  CC=2  out:12
    clone  CC=4  out:15
    info  CC=2  out:13
    init  CC=4  out:12
    package_managers  CC=8  out:16
    status  CC=10  out:21
    version  CC=2  out:14
  goal.cli.version_sync  [9 funcs]
    _update_cargo_version  CC=6  out:8
    _update_csproj_versions  CC=3  out:7
    _update_init_py_versions  CC=7  out:9
    _update_json_version_file  CC=6  out:6
    _update_pom_xml  CC=3  out:6
    _update_readme_metadata  CC=7  out:6
    _update_toml_version  CC=6  out:8
    _update_version_file  CC=1  out:3
    sync_all_versions  CC=1  out:9
  goal.cli.version_utils  [12 funcs]
    _build_author_block  CC=5  out:6
    _update_package_json_metadata  CC=4  out:3
    _update_pyproject_metadata  CC=4  out:8
    _update_setup_py_metadata  CC=1  out:3
    bump_version  CC=5  out:9
    detect_project_types  CC=6  out:8
    find_version_files  CC=6  out:9
    get_current_version  CC=5  out:7
    get_version_from_file  CC=3  out:3
    update_json_version  CC=3  out:4
  goal.cli.wizard_cmd  [5 funcs]
    _find_git_root  CC=3  out:2
    _setup_git_repository  CC=10  out:33
    _setup_project_config  CC=9  out:55
    _setup_user_config  CC=12  out:39
    _show_setup_summary  CC=7  out:39
  goal.commit_generator  [3 funcs]
    display_commit_message  CC=1  out:2
    display_detailed_message  CC=1  out:2
    print_detailed_message  CC=2  out:3
  goal.config.manager  [8 funcs]
    _detect_project_types  CC=6  out:8
    load  CC=5  out:7
    save  CC=3  out:6
    set  CC=4  out:2
    update_from_detection  CC=4  out:11
    ensure_config  CC=5  out:8
    init_config  CC=3  out:4
    load_config  CC=1  out:2
  goal.config.validation  [2 funcs]
    validate_config_file  CC=11  out:25
    validate_config_interactive  CC=10  out:22
  goal.deep_analyzer  [12 funcs]
    _analyze_generic_diff  CC=1  out:6
    _analyze_js_diff  CC=13  out:12
    _analyze_python_diff  CC=10  out:29
    _check_architecture_value  CC=4  out:4
    _check_cli_value  CC=8  out:4
    _detect_file_patterns  CC=6  out:10
    _detect_functional_areas  CC=7  out:12
    _detect_value_indicators  CC=6  out:8
    _extract_python_entities  CC=13  out:17
    aggregate_changes  CC=3  out:16
  goal.formatter  [15 funcs]
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
  goal.generator.analyzer  [17 funcs]
    _has_new_goal_python_file  CC=4  out:3
    _has_package_code  CC=7  out:7
    _is_ci_only  CC=4  out:4
    _is_docs_only  CC=4  out:3
    _resolve_change_type  CC=11  out:10
    _score_by_statistics  CC=8  out:3
    _score_package_signals  CC=2  out:2
    _score_path_signals  CC=9  out:2
    _score_text_signals  CC=3  out:2
    detect_scope  CC=14  out:12
  goal.generator.generator  [3 funcs]
    _classify_files  CC=11  out:7
    generate_enhanced_summary  CC=8  out:14
    generate_smart_commit_message  CC=1  out:2
  goal.git_ops  [28 funcs]
    _echo_cmd  CC=2  out:5
    _handle_clone  CC=3  out:7
    _handle_init_remote  CC=5  out:25
    _handle_local_init  CC=2  out:5
    _handle_merge_strategy  CC=8  out:25
    _list_remote_branches  CC=5  out:9
    _prompt_remote_url  CC=3  out:12
    _run_git_verbose  CC=8  out:13
    _select_branch  CC=3  out:9
    apply_ticket_prefix  CC=6  out:5
  goal.hooks.config  [1 funcs]
    get_hook_config  CC=8  out:7
  goal.hooks.manager  [2 funcs]
    create_precommit_config  CC=3  out:9
    run_validation  CC=4  out:4
  goal.license.manager  [2 funcs]
    create_license_file  CC=10  out:21
    update_license_file  CC=7  out:13
  goal.license.spdx  [3 funcs]
    check_compatibility  CC=14  out:8
    get_license_info  CC=4  out:4
    validate_spdx_id  CC=11  out:13
  goal.package_managers  [13 funcs]
    _detect_package_manager  CC=2  out:2
    _has_any_matching_path  CC=2  out:2
    _has_language_extension  CC=2  out:3
    _path_matches  CC=2  out:4
    detect_package_managers  CC=3  out:4
    detect_project_language  CC=3  out:3
    get_available_package_managers  CC=3  out:2
    get_package_manager_info  CC=1  out:1
    get_package_managers_by_language  CC=3  out:1
    get_preferred_package_manager  CC=5  out:1
  goal.postcommit.manager  [1 funcs]
    get_config  CC=5  out:3
  goal.project_bootstrap  [3 funcs]
    _find_python_bin  CC=5  out:6
    bootstrap_project  CC=1  out:5
    detect_project_types_deep  CC=11  out:11
  goal.push.core  [14 funcs]
    _apply_enhanced_quality_gates  CC=6  out:6
    _detect_and_bootstrap_projects  CC=7  out:7
    _handle_commit_phase  CC=8  out:19
    _handle_no_changes  CC=4  out:6
    _handle_no_files  CC=3  out:1
    _initialize_context  CC=3  out:2
    _maybe_show_workflow_preview  CC=2  out:1
    _run_test_stage_or_exit  CC=3  out:4
    _validate_staged_files  CC=6  out:18
    _validate_toml_or_exit  CC=3  out:6
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
  goal.push.stages.publish  [1 funcs]
    handle_publish  CC=6  out:15
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
    run_test_stage  CC=9  out:24
  goal.push.stages.todo  [1 funcs]
    handle_todo_stage  CC=10  out:22
  goal.push.stages.version  [4 funcs]
    _get_version_module  CC=1  out:0
    get_version_info  CC=2  out:3
    handle_version_sync  CC=3  out:10
    sync_all_versions_wrapper  CC=1  out:2
  goal.recovery.auth  [1 funcs]
    can_handle  CC=2  out:2
  goal.recovery.base  [1 funcs]
    run_git  CC=2  out:5
  goal.recovery.corrupted  [1 funcs]
    can_handle  CC=2  out:2
  goal.recovery.divergent  [1 funcs]
    can_handle  CC=2  out:2
  goal.recovery.force_push  [1 funcs]
    can_handle  CC=2  out:2
  goal.recovery.large_file  [6 funcs]
    _extract_file_paths  CC=8  out:9
    _move_to_lfs  CC=4  out:13
    _remove_large_files  CC=6  out:17
    _skip_large_files  CC=2  out:5
    can_handle  CC=2  out:2
    _run_git_chunked  CC=4  out:4
  goal.recovery.lfs  [1 funcs]
    can_handle  CC=2  out:2
  goal.recovery.manager  [2 funcs]
    _ensure_recovery_dir  CC=3  out:8
    run_git  CC=2  out:5
  goal.summary.validator  [1 funcs]
    _validate_title  CC=10  out:21
  goal.toml_validation  [4 funcs]
    check_pyproject_toml  CC=3  out:3
    get_tomllib  CC=3  out:0
    validate_project_toml_files  CC=4  out:4
    validate_toml_file  CC=9  out:19
  goal.user_config  [9 funcs]
    _load  CC=3  out:3
    _save  CC=2  out:5
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
  goal.validators.file_validator  [7 funcs]
    _check_file_for_tokens  CC=3  out:4
    _handle_oversized_file  CC=3  out:3
    _is_excluded  CC=3  out:3
    get_file_size_mb  CC=2  out:1
    handle_large_files  CC=5  out:14
    validate_files  CC=12  out:8
    validate_staged_files  CC=10  out:11
  goal.validators.gitignore  [2 funcs]
    load_gitignore  CC=6  out:9
    save_gitignore  CC=8  out:11
  goal.validators.tokens  [7 funcs]
    _calculate_entropy  CC=5  out:4
    _classify_token  CC=3  out:0
    _extract_token_value  CC=4  out:3
    _get_entropy_threshold  CC=1  out:1
    _is_dummy_value  CC=8  out:7
    detect_tokens_in_content  CC=10  out:13
    get_default_token_patterns  CC=1  out:0
  goal.version_validation  [7 funcs]
    _validate_single_type  CC=4  out:3
    check_readme_badges  CC=5  out:4
    extract_badge_versions  CC=4  out:10
    format_validation_results  CC=5  out:5
    get_pypi_version  CC=2  out:6
    update_badge_versions  CC=3  out:5
    validate_project_versions  CC=2  out:1
  project.map.toon  [11 funcs]
    ai_cost  CC=0  out:0
    finder  CC=0  out:0
    get_commit_diff  CC=0  out:0
    get_repo_stats  CC=0  out:0
    list  CC=0  out:0
    max  CC=0  out:0
    open  CC=0  out:0
    parse_commits  CC=0  out:0
    patch  CC=0  out:0
    sum  CC=0  out:0
  testql-scenarios.generated-from-pytests.testql.toon  [2 funcs]
    all  CC=0  out:0
    any  CC=0  out:0

EDGES:
  examples.dotnet-project.Calculator.Program.Main → examples.dotnet-project.Calculator.Calculator.Add
  examples.webhooks.slack-webhook.send_slack_notification → Taskfile.print
  examples.webhooks.slack-webhook.main → examples.webhooks.slack-webhook.send_slack_notification
  examples.webhooks.slack-webhook.main → Taskfile.print
  examples.webhooks.discord-webhook.send_discord_notification → Taskfile.print
  examples.webhooks.discord-webhook.main → examples.webhooks.discord-webhook.send_discord_notification
  examples.webhooks.discord-webhook.main → Taskfile.print
  examples.custom-hooks.post-commit.notify_slack → Taskfile.print
  examples.custom-hooks.post-commit.update_changelog → project.map.toon.open
  examples.custom-hooks.post-commit.update_changelog → Taskfile.print
  examples.custom-hooks.post-commit.log_to_file → Taskfile.print
  examples.custom-hooks.post-commit.log_to_file → project.map.toon.open
  examples.custom-hooks.post-commit.main → Taskfile.print
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.get_commit_info
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.notify_slack
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.update_changelog
  examples.custom-hooks.post-commit.main → examples.custom-hooks.post-commit.log_to_file
  examples.custom-hooks.pre-publish.test_build → Taskfile.print
  examples.custom-hooks.pre-publish.test_build → project.map.toon.list
  examples.custom-hooks.pre-publish.test_install → Taskfile.print
  examples.custom-hooks.pre-publish.test_install → project.map.toon.list
  examples.custom-hooks.pre-publish.check_version → Taskfile.print
  examples.custom-hooks.pre-publish.check_version → project.map.toon.open
  examples.custom-hooks.pre-publish.run_security_check → Taskfile.print
  examples.custom-hooks.pre-publish.main → Taskfile.print
  examples.custom-hooks.pre-publish.main → testql-scenarios.generated-from-pytests.testql.toon.all
  examples.custom-hooks.pre-commit.main → Taskfile.print
  examples.custom-hooks.pre-commit.main → examples.custom-hooks.pre-commit.check_secrets
  examples.custom-hooks.pre-commit.main → examples.custom-hooks.pre-commit.check_file_sizes
  examples.custom-hooks.pre-commit.main → examples.custom-hooks.pre-commit.run_tests
  examples.api-usage.04_version_validation.main → Taskfile.print
  examples.api-usage.04_version_validation.main → goal.cli.version_utils.get_current_version
  examples.api-usage.04_version_validation.main → goal.version_validation.get_pypi_version
  examples.api-usage.04_version_validation.main → goal.cli.version_utils.detect_project_types
  examples.api-usage.05_programmatic_workflow.run_custom_workflow → Taskfile.print
  examples.api-usage.05_programmatic_workflow.create_minimal_workflow → Taskfile.print
  examples.api-usage.01_basic_api.main → Taskfile.print
  examples.api-usage.01_basic_api.main → goal.cli.version_utils.detect_project_types
  examples.api-usage.01_basic_api.main → goal.cli.version_utils.get_current_version
  examples.api-usage.03_commit_generation.main → Taskfile.print
  examples.api-usage.03_commit_generation.main → goal.git_ops.get_staged_files
  examples.api-usage.03_commit_generation.main → goal.git_ops.get_diff_content
  examples.api-usage.02_git_operations.main → Taskfile.print
  examples.api-usage.02_git_operations.main → goal.git_ops.get_staged_files
  examples.api-usage.02_git_operations.main → goal.git_ops.get_unstaged_files
  examples.validation.run_all_validation.ValidationRunner.run_test → Taskfile.print
  examples.validation.run_all_validation.ValidationRunner.run_all → Taskfile.print
  examples.validation.run_all_validation.ValidationRunner.print_summary → Taskfile.print
  examples.validation.run_all_validation.ValidationRunner.print_summary → project.map.toon.sum
  examples.template-generator.generate.generate_project → Taskfile.print
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 184f 144117L | python:134,yaml:20,json:8,shell:5,toml:4,txt:2,csharp:2,yml:1,go:1,xml:1,java:1,php:1 | 2026-04-26
# CC̄=0.2 | critical:1/20179 | dups:0 | cycles:0

HEALTH[1]:
  🟡 CC    main CC=15 (limit:15)

REFACTOR[1]:
  1. split 1 high-CC methods  (CC>15)

PIPELINES[539]:
  [1] Src [Add_ReturnsSum]: Add_ReturnsSum
      PURITY: 100% pure
  [2] Src [Subtract_ReturnsDifference]: Subtract_ReturnsDifference
      PURITY: 100% pure
  [3] Src [Multiply_ReturnsProduct]: Multiply_ReturnsProduct
      PURITY: 100% pure
  [4] Src [Divide_ReturnsQuotient]: Divide_ReturnsQuotient
      PURITY: 100% pure
  [5] Src [Main]: Main → Add
      PURITY: 100% pure

LAYERS:
  goal/                           CC̄=4.3    ←in:157  →out:59  !! split
  │ !! project_bootstrap         1288L  0C   40m  CC=14     ←6
  │ !! python                     625L  1C   31m  CC=10     ←0
  │ !! package_managers           616L  1C   16m  CC=5      ←1
  │ !! deep_analyzer              584L  1C   27m  CC=13     ←0
  │ !! git_ops                    574L  0C   28m  CC=11     ←19
  │ !! manager                    570L  1C   12m  CC=10     ←1
  │ !! generator                  534L  1C   14m  CC=14     ←0
  │ !! generator                  527L  1C   25m  CC=13     ←0
  │ validation                 475L  2C   15m  CC=14     ←2
  │ manager                    457L  1C   25m  CC=10     ←7
  │ analyzer                   442L  2C   27m  CC=14     ←0
  │ constants                  435L  0C    0m  CC=0.0    ←0
  │ core                       416L  1C   17m  CC=10     ←3
  │ push_remote                382L  0C   17m  CC=11     ←1
  │ generator                  381L  1C   24m  CC=12     ←2
  │ validator                  364L  1C   24m  CC=10     ←0
  │ quality_filter             344L  1C   18m  CC=14     ←0
  │ wizard_cmd                 340L  0C    7m  CC=12     ←0
  │ version_utils              335L  0C   13m  CC=12     ←7
  │ large_file                 334L  1C   12m  CC=11     ←0
  │ manager                    315L  1C   12m  CC=7      ←0
  │ manager                    311L  1C   14m  CC=6      ←0
  │ manager                    302L  1C   14m  CC=4      ←1
  │ version_validation         299L  0C   15m  CC=9      ←5
  │ __init__                   294L  1C   13m  CC=14     ←7
  │ abstraction                260L  1C   11m  CC=12     ←0
  │ formatter                  257L  1C   23m  CC=13     ←4
  │ user_config                250L  1C   12m  CC=11     ←24
  │ file_validator             247L  0C    7m  CC=12     ←2
  │ commit                     244L  0C    9m  CC=14     ←2
  │ publish                    232L  0C    8m  CC=13     ←2
  │ tokens                     224L  0C    7m  CC=10     ←1
  │ spdx                       222L  0C    7m  CC=14     ←2
  │ actions                    221L  5C   16m  CC=7      ←0
  │ rules                      220L  6C   19m  CC=11     ←0
  │ utils                      212L  0C    9m  CC=5      ←2
  │ utils_cmd                  207L  0C    8m  CC=10     ←0
  │ commit_cmd                 204L  0C    5m  CC=13     ←0
  │ license_cmd                198L  0C    8m  CC=7      ←0
  │ body_formatter             193L  1C   12m  CC=7      ←0
  │ manager                    192L  1C    7m  CC=6      ←0
  │ manager                    190L  1C    7m  CC=7      ←0
  │ tests                      184L  0C    8m  CC=13     ←0
  │ git_ops                    171L  1C    7m  CC=11     ←0
  │ broker                     156L  1C    8m  CC=8      ←0
  │ version_sync               151L  0C    9m  CC=7      ←2
  │ dry_run                    139L  0C    4m  CC=8      ←1
  │ dot_folders                133L  0C    6m  CC=9      ←1
  │ config_cmd                 129L  0C    7m  CC=4      ←0
  │ todo                       128L  0C    5m  CC=9      ←1
  │ authors_cmd                127L  0C   12m  CC=4      ←0
  │ recover_cmd                125L  0C    2m  CC=6      ←0
  │ costs                      120L  0C    3m  CC=11     ←0
  │ divergent                  119L  1C    6m  CC=9      ←0
  │ changelog                  115L  0C    6m  CC=7      ←0
  │ push_cmd                   114L  0C    1m  CC=2      ←0
  │ version_types              113L  0C    0m  CC=0.0    ←0
  │ toml_validation            112L  0C    4m  CC=9      ←2
  │ config                     105L  0C    2m  CC=8      ←0
  │ doctor_cmd                 100L  0C    1m  CC=12     ←0
  │ core                        87L  0C    2m  CC=8      ←3
  │ validation_cmd              85L  0C    5m  CC=7      ←0
  │ hooks_cmd                   83L  0C    8m  CC=2      ←0
  │ postcommit_cmd              82L  0C    5m  CC=6      ←0
  │ nodejs                      77L  0C    1m  CC=13     ←0
  │ auth                        75L  1C    2m  CC=8      ←0
  │ test                        72L  0C    1m  CC=9      ←1
  │ base                        68L  2C    5m  CC=3      ←0
  │ exceptions                  58L  9C    9m  CC=3      ←0
  │ lfs                         57L  1C    2m  CC=6      ←0
  │ __init__                    56L  0C    0m  CC=0.0    ←0
  │ __init__                    55L  0C    0m  CC=0.0    ←0
  │ publish_cmd                 54L  0C    2m  CC=8      ←0
  │ corrupted                   53L  1C    2m  CC=4      ←0
  │ version                     52L  0C    4m  CC=3      ←2
  │ todo                        52L  0C    1m  CC=10     ←1
  │ config_validate_cmd         50L  0C    1m  CC=3      ←0
  │ __init__                    50L  0C    0m  CC=0.0    ←0
  │ base                        48L  1C    5m  CC=2      ←0
  │ __init__                    48L  0C    0m  CC=0.0    ←0
  │ gitignore                   46L  0C    2m  CC=8      ←2
  │ force_push                  45L  1C    2m  CC=5      ←0
  │ php                         45L  0C    1m  CC=7      ←0
  │ commands                    43L  0C    1m  CC=2      ←0
  │ __init__                    42L  0C    3m  CC=2      ←0
  │ config                      42L  1C    2m  CC=3      ←0
  │ models                      41L  2C    0m  CC=0.0    ←0
  │ exceptions                  39L  4C    3m  CC=2      ←0
  │ publish                     37L  0C    1m  CC=6      ←1
  │ uv                          37L  1C    5m  CC=2      ←0
  │ __init__                    36L  0C    0m  CC=0.0    ←0
  │ rust                        35L  0C    1m  CC=4      ←0
  │ go                          35L  0C    1m  CC=5      ←0
  │ version                     35L  0C    0m  CC=0.0    ←0
  │ java                        33L  0C    1m  CC=6      ←0
  │ commit_generator            32L  0C    4m  CC=2      ←0
  │ poetry                      32L  1C    3m  CC=2      ←0
  │ project_doctor              32L  0C    0m  CC=0.0    ←0
  │ __init__                    31L  0C    0m  CC=0.0    ←0
  │ changelog                   30L  0C    2m  CC=2      ←1
  │ pdm                         29L  1C    3m  CC=2      ←0
  │ tag                         28L  0C    1m  CC=4      ←1
  │ pip                         28L  1C    3m  CC=2      ←0
  │ __init__                    27L  0C    0m  CC=0.0    ←0
  │ __init__                    27L  0C    0m  CC=0.0    ←0
  │ dotnet                      26L  0C    1m  CC=4      ←0
  │ ruby                        25L  0C    1m  CC=3      ←0
  │ logging                     25L  0C    2m  CC=3      ←1
  │ enhanced_summary            23L  0C    0m  CC=0.0    ←0
  │ strategies                  23L  0C    0m  CC=0.0    ←0
  │ __init__                    20L  0C    0m  CC=0.0    ←0
  │ __init__                    19L  0C    0m  CC=0.0    ←0
  │ __init__                    19L  0C    0m  CC=0.0    ←0
  │ __main__                    18L  0C    0m  CC=0.0    ←0
  │ __init__                    16L  0C    0m  CC=0.0    ←0
  │ __init__                    14L  0C    0m  CC=0.0    ←0
  │ __init__                    14L  0C    0m  CC=0.0    ←0
  │ cli                         11L  0C    2m  CC=1      ←0
  │ __init__                     9L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=3.5    ←in:0  →out:0
  │ 04_debugging_diagnostics   284L  0C    6m  CC=8      ←0
  │ generate                   267L  0C    2m  CC=4      ←0
  │ 03_advanced_mocking        265L  0C    7m  CC=6      ←0
  │ config-example.yaml        183L  0C    0m  CC=0.0    ←0
  │ pre-publish                171L  0C    5m  CC=6      ←0
  │ post-commit                151L  0C    5m  CC=4      ←1
  │ pre-commit                 128L  0C    4m  CC=8      ←1
  │ slack-webhook              123L  0C    2m  CC=5      ←0
  │ 05_programmatic_workflow   123L  0C    2m  CC=1      ←0
  │ run_all_validation         120L  1C    5m  CC=6      ←0
  │ discord-webhook            111L  0C    2m  CC=5      ←0
  │ 04_version_validation       78L  0C    1m  CC=11     ←0
  │ !! 02_git_operations           78L  0C    1m  CC=15     ←0
  │ 01_basic_api                73L  0C    1m  CC=10     ←0
  │ 03_commit_generation        72L  0C    1m  CC=9      ←0
  │ markdown-demo.sh            70L  0C    0m  CC=0.0    ←0
  │ package.json                64L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              57L  0C    0m  CC=0.0    ←0
  │ Cargo.toml                  49L  0C    0m  CC=0.0    ←0
  │ pom.xml                     40L  0C    0m  CC=0.0    ←0
  │ CalculatorTests.cs          32L  1C    4m  CC=1      ←0
  │ install.sh                  31L  0C    0m  CC=0.0    ←0
  │ Calculator.cs               21L  2C    5m  CC=1      ←0
  │ goal.yaml                   17L  0C    0m  CC=0.0    ←0
  │ Main.java                   15L  1C    2m  CC=1      ←0
  │ pyproject.toml              15L  0C    0m  CC=0.0    ←0
  │ composer.json               15L  0C    0m  CC=0.0    ←0
  │ Example.php                 11L  1C    1m  CC=1      ←0
  │ main.go                     10L  0C    1m  CC=1      ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             2108L  0C    0m  CC=0.0    ←0
  │ tree.txt                   379L  0C    0m  CC=0.0    ←0
  │ Taskfile.yml               240L  0C    1m  CC=0.0    ←16
  │ pyqual.yaml                161L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             135L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                82L  0C    0m  CC=0.0    ←0
  │ redsl.yaml                  78L  0C    0m  CC=0.0    ←0
  │ project.toon-schema.json    66L  0C    0m  CC=0.0    ←0
  │ project.sh                  48L  0C    0m  CC=0.0    ←0
  │ .pre-commit-config.yaml     38L  0C    0m  CC=0.0    ←0
  │ redsl_refactor_report.toon.yaml    33L  0C    0m  CC=0.0    ←0
  │ redsl_refactor_plan.toon.yaml    26L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │
  integration/                    CC̄=0.0    ←in:0  →out:0
  │ run_matrix.sh              216L  1C    4m  CC=0.0    ←0
  │ run_docker_matrix.sh         5L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    63L  0C    2m  CC=0.0    ←26
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! map.toon.yaml            53852L  0C  19289m  CC=0.0    ←45
  │ !! calls.yaml                5563L  0C    0m  CC=0.0    ←0
  │ !! project.yaml              1323L  0C    0m  CC=0.0    ←0
  │ !! validation.toon.yaml       554L  0C    0m  CC=0.0    ←0
  │ calls.toon.yaml            491L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         251L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml      172L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           55L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         54L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  47L  0C    0m  CC=0.0    ←0
  │
  .taskill/                       CC̄=0.0    ←in:0  →out:0
  │ state.json                  11L  0C    0m  CC=0.0    ←0
  │
  .aider/                         CC̄=0.0    ←in:0  →out:0
  │ !! model_prices_and_context_window.json 37479L  0C    0m  CC=0.0    ←0
  │ !! openrouter_models.json   17810L  0C    0m  CC=0.0    ←0
  │ analytics.json               5L  0C    0m  CC=0.0    ←0
  │ installs.json                3L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     Makefile                                  0L
     examples/makefile/Makefile                0L
     integration/Dockerfile                    0L

COUPLING:
                                                                          Taskfile                                     goal                              project.map                       examples.api-usage                         examples.testing                                 goal.cli                                goal.push  testql-scenarios.generated-from-pytests                    examples.custom-hooks                             goal.summary                           goal.generator                          goal.validators                      examples.validation                              goal.config                            goal.recovery
                                 Taskfile                                       ──                                       ←5                                                                              ←102                                      ←59                                                                                                                                                                 ←50                                                                                                                                                                 ←20                                                                                    hub
                                     goal                                        5                                       ──                                       31                                      ←11                                      ←13                                      ←44                                      ←55                                       18                                                                                ←6                                        1                                      ←13                                                                                 3                                       ←1  hub
                              project.map                                                                               ←31                                       ──                                       ←3                                      ←30                                      ←12                                      ←14                                                                                ←6                                      ←31                                       ←8                                       ←7                                       ←1                                       ←3                                       ←6  hub
                       examples.api-usage                                      102                                       11                                        3                                       ──                                                                                 4                                                                                                                                                                                                            1                                                                                                                          1                                           !! fan-out
                         examples.testing                                       59                                       13                                       30                                                                                ──                                                                                 1                                                                                                                                                                                                                                                                                                                                          !! fan-out
                                 goal.cli                                                                                44                                       12                                       ←4                                                                                ──                                        1                                        7                                                                                                                                                                                                                                                    11                                           hub
                                goal.push                                                                                55                                       14                                                                                ←1                                        7                                       ──                                        1                                        3                                                                                                                          1                                                                                                                             !! fan-out
  testql-scenarios.generated-from-pytests                                                                               ←18                                                                                                                                                                  ←7                                       ←1                                       ──                                       ←1                                       ←9                                      ←19                                       ←7                                                                                                                         ←6  hub
                    examples.custom-hooks                                       50                                                                                 6                                                                                                                                                                  ←3                                        1                                       ──                                                                                                                                                                                                                                                        !! fan-out
                             goal.summary                                                                                 6                                       31                                                                                                                                                                                                            9                                                                                ──                                                                                                                                                                                                               !! fan-out
                           goal.generator                                                                                 4                                        8                                       ←1                                                                                                                                                                  19                                                                                                                         ──                                                                                                                                                                      !! fan-out
                          goal.validators                                                                                13                                        7                                                                                                                                                                  ←1                                        7                                                                                                                                                                  ──                                                                                                                             !! fan-out
                      examples.validation                                       20                                                                                 1                                                                                                                                                                                                                                                                                                                                                                                                                        ──                                                                                    !! fan-out
                              goal.config                                                                                 1                                        3                                       ←1                                                                               ←11                                                                                                                                                                                                                                                                                                                                      ──                                           hub
                            goal.recovery                                                                                 1                                        6                                                                                                                                                                                                            6                                                                                                                                                                                                                                                                                             ──  !! fan-out
  CYCLES: none
  HUB: testql-scenarios.generated-from-pytests/ (fan-in=79)
  HUB: goal.license/ (fan-in=7)
  HUB: Taskfile/ (fan-in=255)
  HUB: goal.config/ (fan-in=16)
  HUB: project.map/ (fan-in=169)
  HUB: goal/ (fan-in=157)
  HUB: goal.cli/ (fan-in=11)
  SMELL: goal.summary/ fan-out=46 → split needed
  SMELL: goal.validators/ fan-out=27 → split needed
  SMELL: examples.testing/ fan-out=103 → split needed
  SMELL: examples.validation/ fan-out=21 → split needed
  SMELL: goal.push/ fan-out=81 → split needed
  SMELL: goal.generator/ fan-out=31 → split needed
  SMELL: examples.webhooks/ fan-out=10 → split needed
  SMELL: goal/ fan-out=59 → split needed
  SMELL: goal.recovery/ fan-out=13 → split needed
  SMELL: examples.custom-hooks/ fan-out=57 → split needed
  SMELL: goal.cli/ fan-out=89 → split needed
  SMELL: examples.api-usage/ fan-out=123 → split needed
  SMELL: goal.smart_commit/ fan-out=11 → split needed
  SMELL: examples.template-generator/ fan-out=10 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 19 groups | 132f 20738L | 2026-04-26

SUMMARY:
  files_scanned: 132
  total_lines:   20738
  dup_groups:    19
  dup_fragments: 48
  saved_lines:   203
  scan_ms:       5651

HOTSPOTS[7] (files with most duplication):
  goal/cli/version_sync.py  dup=36L  groups=1  frags=2  (0.2%)
  goal/hooks/manager.py  dup=35L  groups=2  frags=3  (0.2%)
  goal/user_config.py  dup=28L  groups=1  frags=2  (0.1%)
  goal/cli/postcommit_cmd.py  dup=27L  groups=4  frags=4  (0.1%)
  goal/cli/validation_cmd.py  dup=27L  groups=4  frags=4  (0.1%)
  goal/cli/authors_cmd.py  dup=23L  groups=3  frags=6  (0.1%)
  goal/license/spdx.py  dup=20L  groups=1  frags=2  (0.1%)

DUPLICATES[19] (ranked by impact):
  [92a676278db9e76e]   STRU  uninstall_hooks  L=11 N=3 saved=22 sim=1.00
      goal/hooks/manager.py:278-288  (uninstall_hooks)
      goal/postcommit/manager.py:182-192  (run_post_commit_actions)
      goal/validation/manager.py:180-190  (run_custom_validations)
  [0269aa7743a3214a]   STRU  authors_list  L=4 N=6 saved=20 sim=1.00
      goal/cli/authors_cmd.py:40-43  (authors_list)
      goal/cli/authors_cmd.py:77-80  (authors_import)
      goal/cli/authors_cmd.py:84-87  (authors_export)
      goal/cli/hooks_cmd.py:71-74  (hooks_status)
      goal/cli/postcommit_cmd.py:28-31  (postcommit_list)
      goal/cli/validation_cmd.py:28-31  (validation_list)
  [cb9ebedb82c1a435]   STRU  main  L=19 N=2 saved=19 sim=1.00
      examples/webhooks/discord-webhook.py:89-107  (main)
      examples/webhooks/slack-webhook.py:101-119  (main)
  [eb3783695175b171]   STRU  _update_toml_version  L=18 N=2 saved=18 sim=1.00
      goal/cli/version_sync.py:28-45  (_update_toml_version)
      goal/cli/version_sync.py:48-65  (_update_cargo_version)
  [90e6c0a8cb78d015]   STRU  authors  L=3 N=6 saved=15 sim=1.00
      goal/cli/authors_cmd.py:34-36  (authors)
      goal/cli/config_cmd.py:11-13  (config)
      goal/cli/hooks_cmd.py:33-35  (hooks)
      goal/cli/license_cmd.py:18-20  (license)
      goal/cli/postcommit_cmd.py:10-12  (postcommit)
      goal/cli/validation_cmd.py:10-12  (validation)
  [79664e1b14e94359]   STRU  get_git_user_name  L=14 N=2 saved=14 sim=1.00
      goal/user_config.py:75-88  (get_git_user_name)
      goal/user_config.py:91-104  (get_git_user_email)
  [61866fcb488af822]   STRU  install_hooks  L=12 N=2 saved=12 sim=1.00
      goal/hooks/manager.py:264-275  (install_hooks)
      goal/hooks/manager.py:291-302  (run_hooks)
  [7aa96675d99bbfa5]   STRU  postcommit_validate  L=11 N=2 saved=11 sim=1.00
      goal/cli/postcommit_cmd.py:35-45  (postcommit_validate)
      goal/cli/validation_cmd.py:35-45  (validation_validate)
  [647457419bebba7a]   STRU  is_copyleft  L=10 N=2 saved=10 sim=1.00
      goal/license/spdx.py:201-210  (is_copyleft)
      goal/license/spdx.py:213-222  (is_permissive)
  [be5dc2ccfaf1a50f]   STRU  postcommit_run  L=9 N=2 saved=9 sim=1.00
      goal/cli/postcommit_cmd.py:16-24  (postcommit_run)
      goal/cli/validation_cmd.py:16-24  (validation_run)
  [395199f7c31b5150]   STRU  get_npm_version  L=9 N=2 saved=9 sim=1.00
      goal/version_validation.py:23-31  (get_npm_version)
      goal/version_validation.py:34-42  (get_cargo_version)
  [79344c1fc3ff9956]   EXAC  __init__  L=8 N=2 saved=8 sim=1.00
      goal/postcommit/manager.py:15-22  (__init__)
      goal/validation/manager.py:16-23  (__init__)
  [ec98b40481b22142]   STRU  install_editable  L=8 N=2 saved=8 sim=1.00
      goal/installers/managers/pdm.py:14-21  (install_editable)
      goal/installers/managers/poetry.py:14-22  (install_editable)
  [20e408c9d9d242cc]   STRU  validate_summary  L=8 N=2 saved=8 sim=1.00
      goal/summary/__init__.py:15-22  (validate_summary)
      goal/summary/__init__.py:25-32  (auto_fix_summary)
  [144ef4134cc76962]   STRU  install_from_lockfile  L=3 N=3 saved=6 sim=1.00
      goal/installers/managers/pdm.py:27-29  (install_from_lockfile)
      goal/installers/managers/poetry.py:30-32  (install_from_lockfile)
      goal/installers/managers/uv.py:35-37  (install_from_lockfile)
  [dbda8ef1dc9b7e17]   STRU  authors_add  L=4 N=2 saved=4 sim=1.00
      goal/cli/authors_cmd.py:51-54  (authors_add)
      goal/cli/authors_cmd.py:70-73  (authors_update)
  [432344fee46df3c6]   STRU  display_success_message  L=4 N=2 saved=4 sim=1.00
      goal/cli/hooks_cmd.py:9-12  (display_success_message)
      goal/cli/hooks_cmd.py:15-18  (display_failure_message)
  [a056b755248bcc9e]   EXAC  get_name  L=3 N=2 saved=3 sim=1.00
      goal/postcommit/actions.py:30-32  (get_name)
      goal/validation/rules.py:29-31  (get_name)
  [8d361abedd2fedda]   EXAC  validate_config  L=3 N=2 saved=3 sim=1.00
      goal/postcommit/actions.py:35-37  (validate_config)
      goal/validation/rules.py:34-36  (validate_config)

REFACTOR[19] (ranked by priority):
  [1] ○ extract_function   → goal/utils/uninstall_hooks.py
      WHY: 3 occurrences of 11-line block across 3 files — saves 22 lines
      FILES: goal/hooks/manager.py, goal/postcommit/manager.py, goal/validation/manager.py
  [2] ○ extract_function   → goal/cli/utils/authors_list.py
      WHY: 6 occurrences of 4-line block across 4 files — saves 20 lines
      FILES: goal/cli/authors_cmd.py, goal/cli/hooks_cmd.py, goal/cli/postcommit_cmd.py, goal/cli/validation_cmd.py
  [3] ○ extract_function   → examples/webhooks/utils/main.py
      WHY: 2 occurrences of 19-line block across 2 files — saves 19 lines
      FILES: examples/webhooks/discord-webhook.py, examples/webhooks/slack-webhook.py
  [4] ○ extract_function   → goal/cli/utils/_update_toml_version.py
      WHY: 2 occurrences of 18-line block across 1 files — saves 18 lines
      FILES: goal/cli/version_sync.py
  [5] ○ extract_function   → goal/cli/utils/authors.py
      WHY: 6 occurrences of 3-line block across 6 files — saves 15 lines
      FILES: goal/cli/authors_cmd.py, goal/cli/config_cmd.py, goal/cli/hooks_cmd.py, goal/cli/license_cmd.py, goal/cli/postcommit_cmd.py +1 more
  [6] ○ extract_function   → goal/utils/get_git_user_name.py
      WHY: 2 occurrences of 14-line block across 1 files — saves 14 lines
      FILES: goal/user_config.py
  [7] ○ extract_function   → goal/hooks/utils/install_hooks.py
      WHY: 2 occurrences of 12-line block across 1 files — saves 12 lines
      FILES: goal/hooks/manager.py
  [8] ○ extract_function   → goal/cli/utils/postcommit_validate.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: goal/cli/postcommit_cmd.py, goal/cli/validation_cmd.py
  [9] ○ extract_function   → goal/license/utils/is_copyleft.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: goal/license/spdx.py
  [10] ○ extract_function   → goal/cli/utils/postcommit_run.py
      WHY: 2 occurrences of 9-line block across 2 files — saves 9 lines
      FILES: goal/cli/postcommit_cmd.py, goal/cli/validation_cmd.py
  [11] ○ extract_function   → goal/utils/get_npm_version.py
      WHY: 2 occurrences of 9-line block across 1 files — saves 9 lines
      FILES: goal/version_validation.py
  [12] ○ extract_function   → goal/utils/__init__.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: goal/postcommit/manager.py, goal/validation/manager.py
  [13] ○ extract_function   → goal/installers/managers/utils/install_editable.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: goal/installers/managers/pdm.py, goal/installers/managers/poetry.py
  [14] ○ extract_function   → goal/summary/utils/validate_summary.py
      WHY: 2 occurrences of 8-line block across 1 files — saves 8 lines
      FILES: goal/summary/__init__.py
  [15] ○ extract_function   → goal/installers/managers/utils/install_from_lockfile.py
      WHY: 3 occurrences of 3-line block across 3 files — saves 6 lines
      FILES: goal/installers/managers/pdm.py, goal/installers/managers/poetry.py, goal/installers/managers/uv.py
  [16] ○ extract_function   → goal/cli/utils/authors_add.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: goal/cli/authors_cmd.py
  [17] ○ extract_function   → goal/cli/utils/display_success_message.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: goal/cli/hooks_cmd.py
  [18] ○ extract_function   → goal/utils/get_name.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: goal/postcommit/actions.py, goal/validation/rules.py
  [19] ○ extract_function   → goal/utils/validate_config.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: goal/postcommit/actions.py, goal/validation/rules.py

QUICK_WINS[15] (low risk, high savings — do first):
  [1] extract_function   saved=22L  → goal/utils/uninstall_hooks.py
      FILES: manager.py, manager.py, manager.py
  [2] extract_function   saved=20L  → goal/cli/utils/authors_list.py
      FILES: authors_cmd.py, hooks_cmd.py, postcommit_cmd.py +1
  [3] extract_function   saved=19L  → examples/webhooks/utils/main.py
      FILES: discord-webhook.py, slack-webhook.py
  [4] extract_function   saved=18L  → goal/cli/utils/_update_toml_version.py
      FILES: version_sync.py
  [5] extract_function   saved=15L  → goal/cli/utils/authors.py
      FILES: authors_cmd.py, config_cmd.py, hooks_cmd.py +3
  [6] extract_function   saved=14L  → goal/utils/get_git_user_name.py
      FILES: user_config.py
  [7] extract_function   saved=12L  → goal/hooks/utils/install_hooks.py
      FILES: manager.py
  [8] extract_function   saved=11L  → goal/cli/utils/postcommit_validate.py
      FILES: postcommit_cmd.py, validation_cmd.py
  [9] extract_function   saved=10L  → goal/license/utils/is_copyleft.py
      FILES: spdx.py
  [10] extract_function   saved=9L  → goal/cli/utils/postcommit_run.py
      FILES: postcommit_cmd.py, validation_cmd.py

EFFORT_ESTIMATE (total ≈ 6.8h):
  medium uninstall_hooks                     saved=22L  ~44min
  medium authors_list                        saved=20L  ~40min
  medium main                                saved=19L  ~38min
  medium _update_toml_version                saved=18L  ~36min
  medium authors                             saved=15L  ~30min
  easy   get_git_user_name                   saved=14L  ~28min
  easy   install_hooks                       saved=12L  ~24min
  easy   postcommit_validate                 saved=11L  ~22min
  easy   is_copyleft                         saved=10L  ~20min
  easy   postcommit_run                      saved=9L  ~18min
  ... +9 more (~106min)

METRICS-TARGET:
  dup_groups:  19 → 0
  saved_lines: 203 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 20122 func | 100f | 2026-04-26

NEXT[3] (ranked by impact):
  [1] !! SPLIT           goal/project_bootstrap.py
      WHY: 1288L, 0 classes, max CC=14
      EFFORT: ~4h  IMPACT: 18032

  [2] !! SPLIT           goal/doctor/python.py
      WHY: 625L, 1 classes, max CC=10
      EFFORT: ~4h  IMPACT: 6250

  [3] !! SPLIT           goal/package_managers.py
      WHY: 616L, 1 classes, max CC=5
      EFFORT: ~4h  IMPACT: 3080


RISKS[3]:
  ⚠ Splitting goal/project_bootstrap.py may break 40 import paths
  ⚠ Splitting goal/doctor/python.py may break 31 import paths
  ⚠ Splitting goal/package_managers.py may break 16 import paths

METRICS-TARGET:
  CC̄:          0.2 → ≤0.1
  max-CC:      14 → ≤7
  god-modules: 8 → 0
  high-CC(≥15): 0 → ≤0
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=2.7 → now CC̄=0.2
```

### Validation (`project/validation.toon.yaml`)

```toon markpact:analysis path=project/validation.toon.yaml
# vallm batch | 264f | 0✓ 181⚠ 0✗ | 2026-04-26

SUMMARY:
  scanned: 264  passed: 0 (0.0%)  warnings: 181  errors: 0  unsupported: 0

WARNINGS[181]{path,score}:
  examples/validation/test_api_signatures.py,0.71
    issues[3]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
      complexity.lizard_cc,warning,extract_function_calls: CC=20 exceeds limit 15,27
      complexity.lizard_cc,warning,validate_call: CC=20 exceeds limit 15,123
  examples/validation/test_readme_consistency.py,0.74
    issues[2]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
      complexity.lizard_cc,warning,validate_readme: CC=22 exceeds limit 15,92
  integration/run_matrix.sh,0.74
    issues[2]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse BASH: Download error: Language 'BASH' not available for download. Available groups: [""all""]",
      complexity.lizard_length,warning,run_case: 175 lines exceeds limit 100,11
  .aider/analytics.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  .aider/caches/model_prices_and_context_window.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  .aider/caches/openrouter_models.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  .aider/installs.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  .pre-commit-config.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  .taskill/state.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  examples/api-usage/01_basic_api.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/api-usage/02_git_operations.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/api-usage/03_commit_generation.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/api-usage/04_version_validation.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/api-usage/05_programmatic_workflow.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/api-usage/test_integration.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/custom-hooks/post-commit.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/custom-hooks/pre-commit.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/custom-hooks/pre-publish.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/enhanced-summary/config-example.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  examples/git-hooks/install.sh,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse BASH: Download error: Language 'BASH' not available for download. Available groups: [""all""]",
  examples/go-project/main.go,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse GO: Download error: Language 'GO' not available for download. Available groups: [""all""]",
  examples/java-project/src/main/java/com/example/Main.java,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JAVA: Download error: Language 'JAVA' not available for download. Available groups: [""all""]",
  examples/java-project/src/test/java/com/example/MainTest.java,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JAVA: Download error: Language 'JAVA' not available for download. Available groups: [""all""]",
  examples/markdown-demo.sh,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse BASH: Download error: Language 'BASH' not available for download. Available groups: [""all""]",
  examples/my-new-project/goal.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  examples/my-new-project/pyproject.toml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse TOML: Download error: Language 'TOML' not available for download. Available groups: [""all""]",
  examples/my-new-project/src/my-new-project/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/my-new-project/tests/test_my-new-project.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/nodejs-app/package.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  examples/php-project/composer.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  examples/php-project/src/Example.php,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PHP: Download error: Language 'PHP' not available for download. Available groups: [""all""]",
  examples/python-package/pyproject.toml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse TOML: Download error: Language 'TOML' not available for download. Available groups: [""all""]",
  examples/rust-crate/Cargo.toml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse TOML: Download error: Language 'TOML' not available for download. Available groups: [""all""]",
  examples/template-generator/generate.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/testing/03_advanced_mocking.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/testing/04_debugging_diagnostics.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/validation/run_all_validation.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/validation/test_imports.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/validation/test_syntax_check.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/webhooks/discord-webhook.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  examples/webhooks/slack-webhook.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  goal/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/__main__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/authors/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/authors/manager.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/authors/utils.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/changelog.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/authors_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/commit_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/config_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/config_validate_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/doctor_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/hooks_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/license_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/postcommit_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/publish.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/publish_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/push_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/recover_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/tests.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/utils_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/validation_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/version.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/version_sync.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/version_types.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/version_utils.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/cli/wizard_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/commit_generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/config.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/config/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/config/constants.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/config/manager.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/config/validation.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/deep_analyzer.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/core.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/dotnet.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/go.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/java.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/logging.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/models.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/nodejs.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/php.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/python.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/ruby.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/rust.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/doctor/todo.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/enhanced_summary.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/formatter.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/generator/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/generator/analyzer.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/generator/generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/generator/git_ops.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/git_ops.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/hooks/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/hooks/config.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/hooks/manager.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/license/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/license/manager.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/license/spdx.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/package_managers.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/postcommit/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/postcommit/actions.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/postcommit/manager.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/project_bootstrap.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/project_doctor.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/commands.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/core.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/changelog.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/commit.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/costs.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/dry_run.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/publish.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/push_remote.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/tag.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/test.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/todo.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/push/stages/version.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/auth.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/base.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/corrupted.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/divergent.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/exceptions.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/force_push.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/large_file.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/lfs.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/manager.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/recovery/strategies.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/smart_commit.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/smart_commit/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/smart_commit/abstraction.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/smart_commit/generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/summary/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/summary/body_formatter.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/summary/generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/summary/quality_filter.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/summary/validator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/toml_validation.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/user_config.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/validation/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/validation/manager.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/validation/rules.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/validators/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/validators/dot_folders.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/validators/exceptions.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/validators/file_validator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/validators/gitignore.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/validators/tokens.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  goal/version_validation.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  integration/run_docker_matrix.sh,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse BASH: Download error: Language 'BASH' not available for download. Available groups: [""all""]",
  planfile.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  prefact.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  project.sh,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse BASH: Download error: Language 'BASH' not available for download. Available groups: [""all""]",
  project.toon-schema.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  project/calls.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  project/project.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  pyproject.toml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse TOML: Download error: Language 'TOML' not available for download. Available groups: [""all""]",
  pyqual.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  redsl.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  test_recovery.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_changelog.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_cli_options.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_clone_repo.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_config_shim.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_config_validation.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_file_validation.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_formatter.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_git_ops.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_project_bootstrap.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_project_doctor.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_push_e2e.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_smart_commit_shim.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_user_config.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_version_sync.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_version_validation.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
```

## Intent

Goal - Automated git push with enterprise-grade commit intelligence, smart conventional commit generation based on deep code analysis, and interactive release workflow management.

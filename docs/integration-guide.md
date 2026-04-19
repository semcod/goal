## Badge

Dodaj ten badge do swojego `README.md` aby pokazać że projekt używa `goal`:

### Markdown
```markdown
[![Goal](https://img.shields.io/badge/managed%20by-goal-blue.svg)](https://github.com/wronai/goal)
```

### HTML
```html
<a href="https://github.com/wronai/goal">
  <img src="https://img.shields.io/badge/managed%20by-goal-blue.svg" alt="Goal">
</a>
```

### Badge Preview
[![Goal](https://img.shields.io/badge/managed%20by-goal-blue.svg)](https://github.com/wronai/goal)

---

## Czas wykonania `goal -a`

Od wersji 2.1.127+, `goal -a` automatycznie wyświetla czas wykonania na końcu:

```
⏱️  Total time: 12.5s
```

### Badge z czasem wykonania (via GitHub Actions)

Dodaj do workflow generowanie badge z czasem:

```yaml
      - name: Run goal -a with timing
        id: goal
        env:
          PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: |
          start_time=$(date +%s)
          goal -a
          end_time=$(date +%s)
          duration=$((end_time - start_time))
          echo "duration=$duration" >> $GITHUB_OUTPUT
          echo "⏱️ Goal -a completed in ${duration}s"

      - name: Create timing badge
        uses: schneegans/dynamic-badges-action@v1.7.0
        with:
          auth: ${{ secrets.GIST_SECRET }}
          gistID: your-gist-id
          filename: goal-timing.json
          label: "goal -a"
          message: "${{ steps.goal.outputs.duration }}s"
          color: "green"
```

Badge w README:
```markdown
![Goal Timing](https://img.shields.io/badge/dynamic/json?url=https://gist.githubusercontent.com/YOUR_USER/YOUR_GIST_ID/raw/goal-timing.json&label=goal%20-a&color=green)
```

### Lokalne mierzenie czasu

Dodaj alias do `.bashrc` / `.zshrc`:

```bash
timegoal() {
    local start=$(date +%s)
    goal -a
    local end=$(date +%s)
    echo "⏱️ Total time: $((end - start)) seconds"
}
```

Użycie: `timegoal`

### Timing w Makefile

```makefile
.PHONY: release

release:
	@echo "⏱️ Starting goal -a..."
	@start=$$(date +%s); \
	goal -a; \
	exit_code=$$?; \
	end=$$(date +%s); \
	duration=$$((end - start)); \
	if [ $$exit_code -eq 0 ]; then \
		echo "✓ Goal -a completed in $${duration}s"; \
	else \
		echo "✗ Goal -a failed after $${duration}s"; \
	fi; \
	exit $$exit_code
```

---

### Opcja 1: GitHub Actions (zalecana)

Stwórz plik `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install pytest
      
      - name: Run tests
        run: pytest
        id: tests

  release:
    needs: test  # Uruchomi się tylko gdy testy przejdą
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Potrzebne dla git historii
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install goal
        run: pip install goal
      
      - name: Configure Git
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
      
      - name: Run goal -a
        env:
          PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: goal -a
```

### Opcja 2: Pre-commit hook

Stwórz plik `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: python -m pytest
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
      
      - id: goal-release
        name: Goal release
        entry: goal -a
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

**WAŻNE:** Pre-commit hook uruchomi się przed commit, nie po. Aby uruchomić po testach, użyj GitHub Actions.

### Opcja 3: Makefile + local workflow

Dodaj do `Makefile`:

```makefile
.PHONY: test release

test:
	python -m pytest

release: test
	@if [ $$? -eq 0 ]; then \
		echo "✓ Tests passed, running goal -a..."; \
		goal -a; \
	else \
		echo "✗ Tests failed, skipping release"; \
		exit 1; \
	fi
```

Użycie: `make release`

### Opcja 4: Tox (dla Python)

Dodaj do `tox.ini`:

```ini
[tox]
envlist = py311

[testenv]
deps = pytest
commands = pytest

[testenv:release]
deps = 
    {[testenv]deps}
    goal
commands = 
    {[testenv]commands}
    goal -a
```

Użycie: `tox -e release`

---

## Wymagane zmienne środowiskowe

Upewnij się że masz ustawione:

```bash
export PYPI_TOKEN="pypi-xxxxxxxx"
```

Dla GitHub Actions dodaj w Settings → Secrets and variables → Actions:
- `PYPI_TOKEN` - token do PyPI

---

## Konfiguracja goal.yaml

Przykładowa konfiguracja dla projektu Python:

```yaml
name: myproject
version: 0.1.0

publish_enabled: true
publish: twine upload dist/myproject-{version}*

test:
  command: pytest
  min_coverage: 80

auto_version: true
changelog: true
```

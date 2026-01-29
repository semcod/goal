SHELL := /bin/bash

# Define colors for better output
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

# Project information
PACKAGE = weekly
PYTHON = poetry run python
PIP = poetry run pip
PYTEST = poetry run pytest
MYPY = poetry run mypy
BLACK = poetry run black
ISORT = poetry run isort
FLAKE8 = poetry run flake8
COVERAGE = poetry run coverage
PART = patch

.PHONY: help install dev test build publish clean push

help:
	@echo "Targets:"
	@echo "  make install  - install goal locally"
	@echo "  make dev      - install in development mode"
	@echo "  make test     - run tests"
	@echo "  make build    - build package for PyPI"
	@echo "  make publish  - build and upload to PyPI"
	@echo "  make clean    - remove build artifacts"
	@echo "  make push     - use goal to push changes"

install:
	pip install .

dev:
	pip install -e ".[dev]"

test:
	python -m pytest -q

build: clean
	python -m pip install --upgrade build twine
	python -m build --sdist --wheel


publish: bump-version build
	python -m twine upload dist/*

clean:
	rm -rf dist build *.egg-info .pytest_cache __pycache__ goal/__pycache__

push: bump-version
	@if command -v goal &> /dev/null; then \
		goal push; \
	else \
		echo "Goal not installed. Run 'make install' first."; \
	fi


docker-matrix:
	bash integration/run_docker_matrix.sh


## Bump version (e.g., make bump-version PART=patch)
bump-version:
	@if [ -z "$(PART)" ]; then \
		echo "${YELLOW}Error: PART variable not set. Usage: make bump-version PART=<major|minor|patch>${RESET}"; \
		exit 1; \
	fi
	@echo "${YELLOW}Bumping $(PART) version...${RESET}"
	poetry version $(PART)
	git add pyproject.toml
	@VERSION=$$(poetry version -s); \
	git commit -m "Bump version to $$VERSION"; \
	if git rev-parse "v$$VERSION" >/dev/null 2>&1; then \
		echo "${YELLOW}Error: tag 'v$$VERSION' already exists${RESET}"; \
		exit 1; \
	fi; \
	git tag -a "v$$VERSION" -m "Version $$VERSION"; \
	echo "${GREEN}Version bumped to $$VERSION${RESET}"

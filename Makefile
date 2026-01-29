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

publish: build
	python -m twine upload dist/*

clean:
	rm -rf dist build *.egg-info .pytest_cache __pycache__ goal/__pycache__

push: bump-version
	@if command -v goal &> /dev/null; then \
		goal push; \
	else \
		echo "Goal not installed. Run 'make install' first."; \
	fi


## Bump version (e.g., make bump-version PART=patch)
bump-version:
	@if [ -z "$(PART)" ]; then \
		echo "${YELLOW}Error: PART variable not set. Usage: make bump-version PART=<major|minor|patch>${RESET}"; \
		exit 1; \
	fi
	@echo "${YELLOW}Bumping $(PART) version...${RESET}"
	poetry version $(PART)
	git add pyproject.toml
	git commit -m "Bump version to $(shell poetry version -s)"
	git tag -a v$(shell poetry version -s) -m "Version $(shell poetry version -s)"
	@echo "${GREEN}Version bumped to $(shell poetry version -s)${RESET}"

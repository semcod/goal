SHELL := /bin/bash

# Define colors for better output
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

# Project information
PACKAGE = goal
PYTHON = python3
PIP = pip3
PYTEST = python3 -m pytest
MYPY = python3 -m mypy
BLACK = python3 -m black
ISORT = python3 -m isort
FLAKE8 = python3 -m flake8
COVERAGE = python3 -m coverage
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
	@current_version=$$(grep '^version = ' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/'); \
	echo "Current version: $$current_version"; \
	IFS='.' read -r major minor patch <<< "$$current_version"; \
	case "$(PART)" in \
		major) major=$$((major + 1)); minor=0; patch=0 ;; \
		minor) minor=$$((minor + 1)); patch=0 ;; \
		patch) patch=$$((patch + 1)) ;; \
		*) echo "${YELLOW}Error: PART must be major, minor, or patch${RESET}"; exit 1 ;; \
	esac; \
	new_version="$${major}.$${minor}.$${patch}"; \
	sed -i "s/^version = \"$$current_version\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "${GREEN}Version bumped to $$new_version${RESET}"; \
	git add pyproject.toml; \
	git commit -m "Bump version to $$new_version"; \
	if git rev-parse "v$$new_version" >/dev/null 2>&1; then \
		echo "${YELLOW}Error: tag 'v$$new_version' already exists${RESET}"; \
		exit 1; \
	fi; \
	git tag -a "v$$new_version" -m "Version $$new_version"; \
	echo "${GREEN}Created tag v$$new_version${RESET}"

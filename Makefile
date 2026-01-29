SHELL := /bin/bash

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

push:
	@if command -v goal &> /dev/null; then \
		goal push; \
	else \
		echo "Goal not installed. Run 'make install' first."; \
	fi

.PHONY: help install test lint format clean build release patch minor major dry-run

# Default target
help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean build artifacts"
	@echo "  build       - Build the project"
	@echo "  release     - Interactive release with Goal"
	@echo "  patch       - Automatic patch release"
	@echo "  minor       - Automatic minor release"
	@echo "  major       - Automatic major release"
	@echo "  dry-run     - Show what would be released"
	@echo ""
	@echo "Examples:"
	@echo "  make release      # Interactive release"
	@echo "  make patch        # Automatic patch bump"
	@echo "  goal --all        # Full automation"

# Development tasks
install:
	pip install -e ".[dev]"
	npm install
	cargo install --path .

test:
	goal status
	@echo "Running tests..."
	pytest
	npm test
	cargo test
	go test ./...

lint:
	@echo "Running linters..."
	flake8 src
	eslint src/**/*.js
	cargo clippy
	golangci-lint run

format:
	@echo "Formatting code..."
	black src
	prettier --write src/**/*.js
	cargo fmt
	go fmt ./...

# Build tasks
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ target/ node_modules/
	cargo clean
	go clean -cache

build:
	@echo "Building project..."
	python -m build
	npm run build
	cargo build --release
	go build ./...

# Release tasks with Goal
release:
	@echo "Starting interactive release..."
	goal

patch:
	@echo "Starting automatic patch release..."
	goal push --yes

minor:
	@echo "Starting automatic minor release..."
	goal push --yes --bump minor

major:
	@echo "Starting automatic major release..."
	goal push --yes --bump major

# Full automation with --all flag
all:
	@echo "Starting fully automated release..."
	goal --all

# Preview release
dry-run:
	@echo "Previewing release..."
	goal push --dry-run

# CI/CD helper targets
ci-test: install test lint
ci-release: patch
ci-release-minor: minor
ci-release-major: major

# Development workflow
dev: format lint test
	@echo "Development checks complete!"

# Quick commit without tests (for docs, etc.)
quick:
	@echo "Quick release (no tests)..."
	goal push --yes -m "docs: update documentation"

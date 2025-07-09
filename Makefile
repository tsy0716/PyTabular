# Makefile for PyTabular development with uv
# Use 'make help' to see available targets

.PHONY: help install dev-install test lint format type-check docs clean build publish pre-commit

# Default target
help:
	@echo "Available targets:"
	@echo "  help          - Show this help message"
	@echo "  install       - Install package dependencies"
	@echo "  dev-install   - Install package in development mode with dev dependencies"
	@echo "  test          - Run tests"
	@echo "  test-all      - Run tests on all Python versions"
	@echo "  lint          - Run linting (ruff)"
	@echo "  format        - Format code (ruff)"
	@echo "  type-check    - Run type checking (mypy)"
	@echo "  docs          - Build documentation"
	@echo "  docs-serve    - Serve documentation locally"
	@echo "  clean         - Clean build artifacts"
	@echo "  build         - Build package"
	@echo "  publish       - Publish package to PyPI"
	@echo "  pre-commit    - Install pre-commit hooks"
	@echo "  coverage      - Run tests with coverage"
	@echo "  docstring     - Check docstring coverage"
	@echo "  security      - Run security checks"
	@echo "  all-checks    - Run all quality checks"
	@echo ""
	@echo "Linux Migration:"
	@echo "  test-adomo-update    - Test ADOMO update script functionality"
	@echo "  update-adomo-preview - Preview ADOMO library updates (dry run)"
	@echo "  update-adomo         - Update ADOMO libraries for Linux compatibility"
	@echo "  migrate-linux        - Full Linux migration workflow"

# Install package dependencies
install:
	uv sync

# Install package in development mode with dev dependencies
dev-install:
	uv sync --dev

# Run tests
test:
	uv run pytest

# Run tests on all Python versions (requires multiple Python versions installed)
test-all:
	uv run --python 3.8 pytest
	uv run --python 3.9 pytest
	uv run --python 3.10 pytest
	uv run --python 3.11 pytest
	uv run --python 3.12 pytest
	uv run --python 3.13 pytest

# Run linting
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .

# Run type checking
type-check:
	uv run mypy pytabular/

# Build documentation
docs:
	uv run mkdocs build

# Serve documentation locally
docs-serve:
	uv run mkdocs serve

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf dll_backup/
	rm -rf update_adomo.log
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build package
build:
	uv build

# Publish package to PyPI
publish:
	uv publish

# Install pre-commit hooks
pre-commit:
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg

# Run tests with coverage
coverage:
	uv run pytest --cov=pytabular --cov-report=html --cov-report=term-missing

# Check docstring coverage
docstring:
	uv run docstr-coverage pytabular/ --badge=docs/docstring_coverage.svg

# Run security checks
security:
	uv run bandit -c pyproject.toml -r pytabular/

# Run all quality checks
all-checks: lint type-check test coverage docstring security
	@echo "All quality checks completed!"

# Development workflow - install everything and run checks
dev-setup: dev-install pre-commit
	@echo "Development environment setup complete!"

# CI workflow - what gets run in CI
ci: lint type-check test coverage
	@echo "CI checks completed!"

# Quick development cycle
dev: format lint type-check test
	@echo "Development cycle completed!"

# Linux Migration Targets
test-adomo-update:
	@echo "🧪 Testing ADOMO update script functionality..."
	uv run python script/test_adomo_update.py

update-adomo-preview:
	@echo "🔍 Previewing ADOMO library updates..."
	uv run python script/update_adomo_linux.py --dry-run --verbose

update-adomo:
	@echo "🚀 Updating ADOMO libraries for Linux compatibility..."
	uv run python script/update_adomo_linux.py --verbose

migrate-linux: test-adomo-update update-adomo-preview
	@echo "🐧 Starting Linux migration workflow..."
	@echo "Review the preview above. Press Enter to continue or Ctrl+C to cancel."
	@read dummy
	$(MAKE) update-adomo
	@echo "Testing updated libraries..."
	$(MAKE) test
	@echo "Building package..."
	$(MAKE) build
	@echo "🎉 Linux migration completed successfully!"
	@echo "Your PyTabular project is now Linux-compatible!" 
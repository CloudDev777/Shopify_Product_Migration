# Use uv for Python commands
UV := uv
VENV := .venv
VENV_BIN := $(VENV)/bin

# Environment setup
.PHONY: setup
setup: $(VENV)
	cp -n .env.sample .env || true
	$(UV) pip install -e ".[test]"

# Create virtual environment
$(VENV):
	$(UV) venv

# Install dependencies
.PHONY: install
install: $(VENV)
	$(UV) pip install -e ".[test]"

# Run tests
.PHONY: test
test: install
	$(UV) run pytest tests/

# Run migration
.PHONY: migrate
migrate: install
	$(UV) run python -m shopify_migration.main

# Clean up
.PHONY: clean
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

.DEFAULT_GOAL := help

# Help target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  setup    - Initial setup (copy .env.sample and install package)"
	@echo "  install  - Install package in development mode"
	@echo "  test     - Run tests"
	@echo "  migrate  - Run product migration"
	@echo "  clean    - Clean up build files"

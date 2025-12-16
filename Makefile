# Makefile for Combined Autonomous Coding Agent

# Variables
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
PYTHON_VENV := $(BIN)/python

# Default target
.PHONY: all
all: help

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  setup        : Create virtual environment and install dependencies"
	@echo "  install      : Install dependencies (requirements.txt and requirements-dev.txt)"
	@echo "  test         : Run all tests and CI checks (wraps run_tests.sh)"
	@echo "  lint         : Run linter (Flake8) only"
	@echo "  format       : Auto-format code (autopep8 + autoflake)"
	@echo "  clean        : Remove virtual environment and temporary files"
	@echo "  run-dashboard: Run the dashboard server"
	@echo "  docker-build : Build the Docker image"

# Setup: Create venv and install
.PHONY: setup
setup: $(VENV)/bin/activate install

# Create virtual environment
$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created at $(VENV)"

# Install dependencies
.PHONY: install
install: $(VENV)/bin/activate
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	$(PIP) install autopep8 autoflake
	@echo "Dependencies installed."

# Run tests (CI Check)
.PHONY: test
test:
	@# Ensure run_tests.sh is executable
	@chmod +x run_tests.sh
	@# Run run_tests.sh with the venv path explicitly added to PATH
	@export PATH=$(shell pwd)/$(BIN):$(PATH) && ./run_tests.sh

# Linting
.PHONY: lint
lint:
	$(BIN)/flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv,venv
	$(BIN)/flake8 . --count --exit-zero --max-complexity=35 --max-line-length=160 --statistics --exclude=.venv,venv

# Formatting
.PHONY: format
format:
	@echo "Removing unused imports..."
	$(BIN)/autoflake --in-place --remove-all-unused-imports --recursive --exclude .venv,*/__init__.py .
	@echo "Formatting code..."
	$(BIN)/autopep8 --in-place --aggressive --aggressive --recursive --exclude .venv .
	@echo "Done."

# Monitoring
.PHONY: monitor-up monitor-down monitor-logs
monitor-up:
	docker compose -f docker-compose.monitoring.yml up -d

monitor-down:
	docker compose -f docker-compose.monitoring.yml down

monitor-logs:
	docker compose -f docker-compose.monitoring.yml logs -f

# Clean
.PHONY: clean
clean:
	rm -rf __pycache__ .venv .mypy_cache .pytest_cache
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned up."

# Run Dashboard
.PHONY: run-dashboard
run-dashboard:
	$(PYTHON_VENV) main.py --dashboard-only

# Docker Build
.PHONY: docker-build
docker-build:
	docker build -t combined-autonomous-coding:latest .

# Docker Run Interactive
.PHONY: docker-run
docker-run:
	./bin/start_agent --build bash

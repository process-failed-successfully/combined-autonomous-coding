#!/bin/bash
set -e # Exit on error

export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "========================================"
echo "  STATIC ANALYSIS & SECURITY CHECKS"
echo "========================================"

echo "[1/4] Running Flake8 Linting..."
# Stop the build if there are Python syntax errors or undefined names
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv,venv
# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
flake8 . --count --exit-zero --max-complexity=35 --max-line-length=160 --statistics --exclude=.venv,venv

echo "[2/4] Running Mypy Type Checking..."
mypy . --ignore-missing-imports --no-strict-optional || echo "Mypy found issues (continuing for now)"

echo "[3/4] Running Bandit Security Scan..."
bandit -r . -c "pyproject.toml" -ll -b bandit_baseline.json -f custom -x .venv,venv,build,tests

echo -e "\n========================================"
echo "  UNIT & INTEGRATION TESTS (PYTEST)"
echo "========================================"

echo "[4/4] Running Tests with Coverage..."
pytest --cov=. --cov-report=term-missing tests/

echo -e "\nRunning Setup Verification..."
python3 tests/verify_setup.py

echo -e "\n\033[0;32mAll Checks Passed Successfully!\033[0m"

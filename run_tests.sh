#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
echo "Running Unit Tests..."
python3 tests/test_utils.py

echo -e "\nRunning Setup Verification..."
python3 tests/verify_setup.py

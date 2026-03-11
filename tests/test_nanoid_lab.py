import sys
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import argparse

from shared.nanoid_lab import NanoIDLabManager, run_nanoid_lab_logic
import nanoid

def test_manager_generate_nanoid_default():
    ids = NanoIDLabManager.generate_nanoid()
    assert len(ids) == 1
    assert len(ids[0]) == 21

def test_manager_generate_nanoid_custom_size():
    ids = NanoIDLabManager.generate_nanoid(size=10, count=2)
    assert len(ids) == 2
    assert len(ids[0]) == 10
    assert len(ids[1]) == 10

def test_manager_generate_nanoid_custom_alphabet():
    alphabet = "abc"
    ids = NanoIDLabManager.generate_nanoid(size=10, alphabet=alphabet, count=1)
    assert len(ids) == 1
    assert len(ids[0]) == 10
    for char in ids[0]:
        assert char in alphabet

def test_manager_validate_nanoid_valid_default():
    valid_id = nanoid.generate()
    assert NanoIDLabManager.validate_nanoid(valid_id) is True

def test_manager_validate_nanoid_invalid_size():
    invalid_id = "12345"
    assert NanoIDLabManager.validate_nanoid(invalid_id) is False

def test_manager_validate_nanoid_invalid_alphabet():
    invalid_id = "A" * 21
    # alphabet only lowercase
    assert NanoIDLabManager.validate_nanoid(invalid_id, alphabet="abc") is False

def test_manager_validate_nanoid_valid_custom():
    valid_id = nanoid.generate(alphabet="abc", size=10)
    assert NanoIDLabManager.validate_nanoid(valid_id, size=10, alphabet="abc") is True

@patch("sys.stdout", new_callable=StringIO)
def test_cli_generate_default(mock_stdout):
    args = argparse.Namespace(action="generate", size=21, alphabet=None, count=1)
    try:
        run_nanoid_lab_logic(args)
    except SystemExit as e:
        assert e.code == 0

    output = mock_stdout.getvalue().strip()
    assert len(output) == 21

@patch("sys.stdout", new_callable=StringIO)
def test_cli_generate_custom(mock_stdout):
    args = argparse.Namespace(action="generate", size=10, alphabet="a", count=3)
    try:
        run_nanoid_lab_logic(args)
    except SystemExit as e:
        assert e.code == 0

    output = mock_stdout.getvalue().strip().split("\n")
    assert len(output) == 3
    for line in output:
        assert line == "a" * 10

@patch("sys.stdout", new_callable=StringIO)
def test_cli_validate_valid(mock_stdout):
    valid_id = nanoid.generate(size=21)
    args = argparse.Namespace(action="validate", nanoid=valid_id, size=21, alphabet=None)
    try:
        run_nanoid_lab_logic(args)
    except SystemExit as e:
        assert e.code == 0

    output = mock_stdout.getvalue().strip()
    assert "is a valid NanoID" in output

@patch("sys.stderr", new_callable=StringIO)
def test_cli_validate_invalid(mock_stderr):
    args = argparse.Namespace(action="validate", nanoid="invalid", size=21, alphabet=None)
    with pytest.raises(SystemExit) as e:
        run_nanoid_lab_logic(args)
    assert e.value.code == 1

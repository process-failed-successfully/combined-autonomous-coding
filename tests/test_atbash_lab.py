from unittest.mock import patch
from io import StringIO
import argparse

from shared.atbash_lab import atbash_cipher, run_atbash_lab_logic

def test_atbash_cipher():
    # Lowercase
    assert atbash_cipher("abc") == "zyx"
    assert atbash_cipher("xyz") == "cba"
    # Uppercase
    assert atbash_cipher("ABC") == "ZYX"
    # Mixed and spaces
    assert atbash_cipher("Hello World") == "Svool Dliow"
    # Numbers and symbols
    assert atbash_cipher("123!@#") == "123!@#"
    assert atbash_cipher("Test 123!") == "Gvhg 123!"
    # Non-ASCII characters (should remain untouched)
    assert atbash_cipher("Café naïve") == "Xzué mzïev"

def test_run_atbash_lab_logic_with_text():
    args = argparse.Namespace(text="Hello", tui=False)
    with patch("sys.stdout", new=StringIO()) as fake_stdout:
        assert run_atbash_lab_logic(args) is True
        assert fake_stdout.getvalue() == "Svool"

def test_run_atbash_lab_logic_stdin():
    args = argparse.Namespace(text=None, tui=False)
    with patch("sys.stdin.isatty", return_value=False), \
         patch("sys.stdin.read", return_value="apple"), \
         patch("sys.stdout", new=StringIO()) as fake_stdout:
        assert run_atbash_lab_logic(args) is True
        assert fake_stdout.getvalue() == "zkkov"

def test_run_atbash_lab_logic_no_input():
    args = argparse.Namespace(text=None, tui=False)
    with patch("sys.stdin.isatty", return_value=True), \
         patch("sys.stderr", new=StringIO()) as fake_stderr:
        assert run_atbash_lab_logic(args) is False
        assert "Error: No input text provided" in fake_stderr.getvalue()

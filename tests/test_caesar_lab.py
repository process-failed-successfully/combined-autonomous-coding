
from unittest.mock import patch
from io import StringIO

import argparse

from shared.caesar_lab import caesar_cipher, run_caesar_lab_logic

def test_caesar_cipher_encode():
    assert caesar_cipher("hello world", 3) == "khoor zruog"
    assert caesar_cipher("HELLO WORLD", 3) == "KHOOR ZRUOG"

def test_caesar_cipher_decode():
    assert caesar_cipher("khoor zruog", 3, decode=True) == "hello world"
    assert caesar_cipher("KHOOR ZRUOG", 3, decode=True) == "HELLO WORLD"

def test_caesar_cipher_wrap_around():
    assert caesar_cipher("xyz", 3) == "abc"
    assert caesar_cipher("abc", 3, decode=True) == "xyz"

def test_caesar_cipher_special_chars():
    assert caesar_cipher("hello, world! 123", 5) == "mjqqt, btwqi! 123"

def test_caesar_cipher_negative_shift():
    assert caesar_cipher("abc", -1) == "zab"

def test_run_caesar_lab_logic_with_text():
    args = argparse.Namespace(text="hello", shift=13, decode=False)
    with patch("sys.stdout", new=StringIO()) as fake_stdout:
        assert run_caesar_lab_logic(args)
        assert fake_stdout.getvalue() == "uryyb"

def test_run_caesar_lab_logic_with_text_and_decode():
    args = argparse.Namespace(text="uryyb", shift=13, decode=True)
    with patch("sys.stdout", new=StringIO()) as fake_stdout:
        assert run_caesar_lab_logic(args)
        assert fake_stdout.getvalue() == "hello"

def test_run_caesar_lab_logic_stdin():
    args = argparse.Namespace(text=None, shift=5, decode=False)
    with patch("sys.stdin.isatty", return_value=False), \
         patch("sys.stdin.read", return_value="apple"), \
         patch("sys.stdout", new=StringIO()) as fake_stdout:
        assert run_caesar_lab_logic(args)
        assert fake_stdout.getvalue() == "fuuqj"

def test_run_caesar_lab_logic_no_input():
    args = argparse.Namespace(text=None, shift=13, decode=False)
    with patch("sys.stdin.isatty", return_value=True), \
         patch("sys.stderr", new=StringIO()) as fake_stderr:
        assert run_caesar_lab_logic(args) is False
        assert "Error: No input text provided" in fake_stderr.getvalue()

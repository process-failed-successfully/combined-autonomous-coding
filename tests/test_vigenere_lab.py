from unittest.mock import patch
from io import StringIO
import argparse

from shared.vigenere_lab import vigenere_cipher, run_vigenere_lab_logic

def test_vigenere_cipher_encode():
    assert vigenere_cipher("hello world", "key") == "rijvs uyvjn"
    assert vigenere_cipher("HELLO WORLD", "KEY") == "RIJVS UYVJN"
    # test wrapping key
    assert vigenere_cipher("attackatdawn", "lemon") == "lxfopvefrnhr"

def test_vigenere_cipher_decode():
    assert vigenere_cipher("rijvs uyvjn", "key", decode=True) == "hello world"
    assert vigenere_cipher("RIJVS UYVJN", "KEY", decode=True) == "HELLO WORLD"
    assert vigenere_cipher("lxfopvefrnhr", "lemon", decode=True) == "attackatdawn"

def test_vigenere_cipher_special_chars():
    assert vigenere_cipher("hello, world! 123", "key") == "rijvs, uyvjn! 123"

def test_vigenere_cipher_no_key():
    assert vigenere_cipher("hello", "") == "hello"
    assert vigenere_cipher("hello", "123") == "hello"

def test_run_vigenere_lab_logic_with_text():
    args = argparse.Namespace(text="hello", key="key", decode=False)
    with patch("sys.stdout", new=StringIO()) as fake_stdout:
        assert run_vigenere_lab_logic(args)
        assert fake_stdout.getvalue() == "rijvs"

def test_run_vigenere_lab_logic_with_text_and_decode():
    args = argparse.Namespace(text="rijvs", key="key", decode=True)
    with patch("sys.stdout", new=StringIO()) as fake_stdout:
        assert run_vigenere_lab_logic(args)
        assert fake_stdout.getvalue() == "hello"

def test_run_vigenere_lab_logic_stdin():
    args = argparse.Namespace(text=None, key="key", decode=False)
    with patch("sys.stdin.isatty", return_value=False), \
         patch("sys.stdin.read", return_value="apple"), \
         patch("sys.stdout", new=StringIO()) as fake_stdout:
        assert run_vigenere_lab_logic(args)
        assert fake_stdout.getvalue() == "ktnvi"

def test_run_vigenere_lab_logic_no_input():
    args = argparse.Namespace(text=None, key="key", decode=False)
    with patch("sys.stdin.isatty", return_value=True), \
         patch("sys.stderr", new=StringIO()) as fake_stderr:
        assert run_vigenere_lab_logic(args) is False
        assert "Error: No input text provided" in fake_stderr.getvalue()

def test_run_vigenere_lab_logic_no_key():
    args = argparse.Namespace(text="hello", key="", decode=False)
    with patch("sys.stderr", new=StringIO()) as fake_stderr:
        assert run_vigenere_lab_logic(args) is False
        assert "Error: Vigenère cipher requires a --key" in fake_stderr.getvalue()

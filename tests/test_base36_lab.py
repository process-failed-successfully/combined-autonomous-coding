import pytest
import argparse
from shared.base36_lab import base36_encode, base36_decode, run_base36_lab_logic

def test_base36_encode_decode():
    # Empty byte array
    assert base36_encode(b"") == ""
    assert base36_decode("") == b""

    # Hello world
    encoded = base36_encode(b"hello")
    assert encoded == "5pzcszu7"
    assert base36_decode(encoded) == b"hello"

    # Text test
    assert base36_decode(base36_encode(b"Testing Base36!")) == b"Testing Base36!"

def test_base36_leading_zeros():
    # Single zero byte
    assert base36_encode(b"\x00") == "0"
    # Technically, we mapped \x00 to '0', decoding '0' returns b'\x00' with our logic
    assert base36_decode("0") == b"\x00"

    # Multiple zero bytes
    assert base36_encode(b"\x00\x00") == "00"
    assert base36_decode("00") == b"\x00\x00"

    assert base36_encode(b"\x00hello") == "05pzcszu7"
    assert base36_decode("05pzcszu7") == b"\x00hello"

def test_base36_invalid_decode():
    with pytest.raises(ValueError):
        base36_decode("hello_world") # _ is invalid

def test_run_base36_lab_logic_encode(capsys):
    args = argparse.Namespace(encode="hello", decode=None, tui=False)
    result = run_base36_lab_logic(args)
    assert result is True
    captured = capsys.readouterr()
    assert "5pzcszu7" in captured.out

def test_run_base36_lab_logic_decode(capsys):
    args = argparse.Namespace(encode=None, decode="5pzcszu7", tui=False)
    result = run_base36_lab_logic(args)
    assert result is True
    captured = capsys.readouterr()
    assert "hello" in captured.out

def test_run_base36_lab_logic_no_args(capsys):
    args = argparse.Namespace(encode=None, decode=None, tui=False)
    result = run_base36_lab_logic(args)
    assert result is False
    captured = capsys.readouterr()
    assert "Error: must provide either --encode, --decode, or --tui" in captured.err

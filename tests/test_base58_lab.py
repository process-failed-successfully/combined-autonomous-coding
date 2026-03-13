import pytest
import argparse
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
from textual.widgets import Input, Button, Label

from shared.base58_lab import b58encode, b58decode, run_base58_lab_logic
from shared.tui_base58 import Base58LabTab


class DummyInput:
    def __init__(self, value=""):
        self.value = value

class DummyLabel:
    def __init__(self):
        self.text = ""
        self.renderable = ""
    def update(self, content):
        self.text = str(content)
        self.renderable = str(content)

class DummyButton:
    def __init__(self, id):
        self.id = id

class DummyEvent:
    def __init__(self, button_id):
        self.button = DummyButton(button_id)


def test_b58encode():
    # Test valid encodings
    assert b58encode(b"hello world") == "StV1DL6CwTryKyV"
    assert b58encode(b"") == ""
    assert b58encode(b"\0\0hello") == "11Cn8eVZg"

    # Test type error
    with pytest.raises(TypeError):
        b58encode("hello") # type: ignore


def test_b58decode():
    # Test valid decodings
    assert b58decode("StV1DL6CwTryKyV") == b"hello world"
    assert b58decode("") == b""
    assert b58decode("11Cn8eVZg") == b"\0\0hello"

    # Test string auto-encode logic
    assert b58decode(b"StV1DL6CwTryKyV") == b"hello world" # type: ignore

    # Test invalid char
    with pytest.raises(ValueError, match="Invalid character 'I' in base58 string"):
        b58decode("StV1DL6CwTryKIyV") # I is not in alphabet


def test_run_base58_lab_logic_encode():
    args = argparse.Namespace(encode="hello", decode=None)
    with patch('sys.stdout', new=StringIO()) as fake_out:
        success = run_base58_lab_logic(args)
        assert success is True
        assert "Cn8eVZg" in fake_out.getvalue()


def test_run_base58_lab_logic_decode():
    args = argparse.Namespace(encode=None, decode="Cn8eVZg")
    with patch('sys.stdout', new=StringIO()) as fake_out:
        success = run_base58_lab_logic(args)
        assert success is True
        assert "hello" in fake_out.getvalue()


def test_run_base58_lab_logic_error():
    args = argparse.Namespace(encode=None, decode=None)
    with patch('sys.stderr', new=StringIO()) as fake_err:
        success = run_base58_lab_logic(args)
        assert success is False
        assert "must provide either --encode, --decode, or --tui" in fake_err.getvalue()


def test_run_base58_lab_logic_exception():
    args = argparse.Namespace(encode=None, decode="Cn8eVZgI") # Invalid
    with patch('sys.stderr', new=StringIO()) as fake_err:
        success = run_base58_lab_logic(args)
        assert success is False
        assert "Error processing base58: Invalid character 'I'" in fake_err.getvalue()


def test_tui_base58_lab_tab_encode():
    tab = Base58LabTab()

    dummy_input = DummyInput(value="hello")
    dummy_label = DummyLabel()
    tab.output_label = dummy_label

    # Mock query_one to return our dummy input
    tab.query_one = MagicMock(return_value=dummy_input)

    event = DummyEvent("btn-encode-base58")
    tab.on_button_pressed(event)

    assert dummy_label.text == "Cn8eVZg"


def test_tui_base58_lab_tab_decode():
    tab = Base58LabTab()

    dummy_input = DummyInput(value="Cn8eVZg")
    dummy_label = DummyLabel()
    tab.output_label = dummy_label

    # Mock query_one to return our dummy input
    tab.query_one = MagicMock(return_value=dummy_input)

    event = DummyEvent("btn-decode-base58")
    tab.on_button_pressed(event)

    assert dummy_label.text == "hello"


def test_tui_base58_lab_tab_empty():
    tab = Base58LabTab()

    dummy_input = DummyInput(value="")
    dummy_label = DummyLabel()
    tab.output_label = dummy_label

    # Mock query_one to return our dummy input
    tab.query_one = MagicMock(return_value=dummy_input)

    event = DummyEvent("btn-encode-base58")
    tab.on_button_pressed(event)

    assert dummy_label.text == "Error: Input cannot be empty."


def test_tui_base58_lab_tab_error():
    tab = Base58LabTab()

    dummy_input = DummyInput(value="Cn8eVZgI")
    dummy_label = DummyLabel()
    tab.output_label = dummy_label

    # Mock query_one to return our dummy input
    tab.query_one = MagicMock(return_value=dummy_input)

    event = DummyEvent("btn-decode-base58")
    tab.on_button_pressed(event)

    assert "Error: Invalid character 'I'" in dummy_label.text

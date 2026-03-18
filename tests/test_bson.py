import json
import pytest
from unittest.mock import patch
import argparse
from pathlib import Path
import unittest
from shared.bson_lab import HAS_BSON

# Need to import Any for TUI tests to avoid missing type parameters error
from typing import Any
from textual.app import App

from shared.bson_lab import BsonManager, run_bson_lab_logic
from shared.tui_bson import BsonLabTab


class DummyApp(App[Any]):
    """A dummy app for testing BsonLabTab."""

    def compose(self):
        yield BsonLabTab()


@pytest.fixture
def tui_app():
    return DummyApp()


@unittest.skipIf(not HAS_BSON, "bson is not installed")
def test_bson_encode():
    # Valid encode
    data = '{"test": 123}'
    encoded = BsonManager.encode(data)
    assert isinstance(encoded, bytes)

    # Invalid json
    with pytest.raises(ValueError, match="Invalid JSON"):
        BsonManager.encode("invalid json")

    # Invalid root level
    with pytest.raises(ValueError, match="BSON encoding requires a JSON object"):
        BsonManager.encode('["array"]')


@unittest.skipIf(not HAS_BSON, "bson is not installed")
def test_bson_decode():
    encoded = BsonManager.encode('{"test": 123}')
    decoded = BsonManager.decode(encoded)
    assert json.loads(decoded) == {"test": 123}

    # Invalid bson
    with pytest.raises(ValueError, match="Invalid BSON input"):
        BsonManager.decode(b'invalid bson bytes')


@unittest.skipIf(not HAS_BSON, "bson is not installed")
def test_run_bson_lab_logic_encode_success(capsys):
    data = '{"test": 123}'
    args = argparse.Namespace(action="encode", data=data)

    assert run_bson_lab_logic(args) is True
    captured = capsys.readouterr()
    assert captured.out.strip() != ""  # Output hex string


@unittest.skipIf(not HAS_BSON, "bson is not installed")
def test_run_bson_lab_logic_encode_missing_data(capsys):
    args = argparse.Namespace(action="encode", data=None)
    assert run_bson_lab_logic(args) is False
    captured = capsys.readouterr()
    assert "Error: --data is required for encoding." in captured.err


@unittest.skipIf(not HAS_BSON, "bson is not installed")
def test_run_bson_lab_logic_decode_success(capsys):
    data = '{"test": 123}'
    encoded_hex = BsonManager.encode(data).hex()
    args = argparse.Namespace(action="decode", data=encoded_hex)

    assert run_bson_lab_logic(args) is True
    captured = capsys.readouterr()
    assert '"test": 123' in captured.out


@unittest.skipIf(not HAS_BSON, "bson is not installed")
def test_run_bson_lab_logic_decode_missing_data(capsys):
    args = argparse.Namespace(action="decode", data=None)
    assert run_bson_lab_logic(args) is False
    captured = capsys.readouterr()
    assert "Error: --data is required for decoding." in captured.err


@unittest.skipIf(not HAS_BSON, "bson is not installed")
def test_run_bson_lab_logic_invalid_action(capsys):
    args = argparse.Namespace(action="invalid", data="something")
    assert run_bson_lab_logic(args) is False
    captured = capsys.readouterr()
    assert "Error: Invalid action." in captured.err


@patch('shared.bson_lab.bson', None)
def test_bson_module_not_installed_encode():
    with pytest.raises(ImportError, match="bson module is not installed"):
        BsonManager.encode('{"test": 123}')


@patch('shared.bson_lab.bson', None)
def test_bson_module_not_installed_decode():
    with pytest.raises(ImportError, match="bson module is not installed"):
        BsonManager.decode(b'hex')


@patch('shared.bson_lab.bson', None)
def test_run_bson_lab_logic_no_bson(capsys):
    args = argparse.Namespace(action="encode", data="{}")
    assert run_bson_lab_logic(args) is False
    captured = capsys.readouterr()
    assert "The 'bson' library is required" in captured.err


@unittest.skipIf(not HAS_BSON, "bson is not installed")
@pytest.mark.asyncio
async def test_bson_lab_tui_encode(tui_app):
    async with tui_app.run_test() as pilot:
        tab = tui_app.query_one(BsonLabTab)
        assert tab.has_bson is True  # since it's installed

        input_area = tab.query_one("#input_area")
        input_area.text = '{"tui": "test"}'

        await pilot.click("#btn_encode")

        output_area = tab.query_one("#output_area")
        assert output_area.text != ""
        assert tab.error_message == ""


@unittest.skipIf(not HAS_BSON, "bson is not installed")
@pytest.mark.asyncio
async def test_bson_lab_tui_decode(tui_app):
    async with tui_app.run_test() as pilot:
        tab = tui_app.query_one(BsonLabTab)

        encoded_hex = BsonManager.encode('{"tui": "test"}').hex()

        input_area = tab.query_one("#input_area")
        input_area.text = encoded_hex

        await pilot.click("#btn_decode")

        output_area = tab.query_one("#output_area")
        assert '"tui": "test"' in output_area.text
        assert tab.error_message == ""


@unittest.skipIf(not HAS_BSON, "bson is not installed")
@pytest.mark.asyncio
async def test_bson_lab_tui_decode_error(tui_app):
    async with tui_app.run_test() as pilot:
        tab = tui_app.query_one(BsonLabTab)

        input_area = tab.query_one("#input_area")
        input_area.text = "invalid_hex"

        await pilot.click("#btn_decode")

        assert "Decode Error:" in tab.error_message


@unittest.skipIf(not HAS_BSON, "bson is not installed")
def test_run_bson_lab_tui_action():
    from main import run_bson_lab
    args = argparse.Namespace(command="bson-lab", action="tui", project_dir=Path("."))

    with patch("sys.exit") as mock_exit:
        mock_exit.side_effect = SystemExit
        with patch("shared.tui.AgentTUI.run") as mock_run:
            try:
                run_bson_lab(args)
            except SystemExit:
                pass
            mock_run.assert_called_once()

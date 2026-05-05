import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from shared.ini2json_lab import Ini2JsonManager, run_ini2json_lab_logic
from shared.tui_ini2json import Ini2JsonLabTab

def test_ini2json_convert_simple():
    manager = Ini2JsonManager()
    ini_data = """
[Section1]
key1 = value1
key2 = value2

[Section2]
key3 = 123
"""
    json_output = manager.convert(ini_data)
    data = json.loads(json_output)
    assert "Section1" in data
    assert "Section2" in data
    assert data["Section1"]["key1"] == "value1"
    assert data["Section1"]["key2"] == "value2"
    assert data["Section2"]["key3"] == "123"

def test_ini2json_convert_global():
    manager = Ini2JsonManager()
    ini_data = """
key1 = value1

[Global]
key2 = value2
"""
    json_output = manager.convert(ini_data)
    data = json.loads(json_output)
    # The default key1 goes into DEFAULT and Global stays in Global
    assert "DEFAULT" in data
    assert data["DEFAULT"]["key1"] == "value1"
    assert "Global" in data
    assert data["Global"]["key2"] == "value2"

def test_ini2json_convert_only_global():
    manager = Ini2JsonManager()
    ini_data = """
[Global]
key1 = value1
key2 = value2
"""
    json_output = manager.convert(ini_data)
    data = json.loads(json_output)
    # If the only section is Global, we unwrap it
    assert "key1" in data
    assert "key2" in data
    assert data["key1"] == "value1"
    assert data["key2"] == "value2"

def test_ini2json_convert_invalid_ini():
    manager = Ini2JsonManager()
    ini_data = "invalid\n[unclosed section"
    with pytest.raises(ValueError, match="Invalid INI string"):
        manager.convert(ini_data)

def test_run_ini2json_lab_logic_cli_file(tmp_path, capsys):
    input_file = tmp_path / "input.ini"
    input_file.write_text("[test]\nkey=val")

    args = MagicMock()
    args.action = None
    args.tui = False
    args.file = str(input_file)
    args.text = None
    args.output = None

    run_ini2json_lab_logic(args)

    captured = capsys.readouterr()
    output_json = json.loads(captured.out)
    assert output_json["test"]["key"] == "val"

def test_run_ini2json_lab_logic_cli_text(capsys):
    args = MagicMock()
    args.action = None
    args.tui = False
    args.file = None
    args.text = "[test]\nkey=val2"
    args.output = None

    run_ini2json_lab_logic(args)

    captured = capsys.readouterr()
    output_json = json.loads(captured.out)
    assert output_json["test"]["key"] == "val2"

def test_run_ini2json_lab_logic_cli_output(tmp_path, capsys):
    output_file = tmp_path / "output.json"

    args = MagicMock()
    args.action = None
    args.tui = False
    args.file = None
    args.text = "[test]\nkey=val3"
    args.output = str(output_file)

    run_ini2json_lab_logic(args)

    captured = capsys.readouterr()
    assert "✅ Converted JSON saved to" in captured.out

    output_content = json.loads(output_file.read_text())
    assert output_content["test"]["key"] == "val3"

def test_run_ini2json_lab_logic_missing_input(capsys):
    args = MagicMock()
    args.action = None
    args.tui = False
    args.file = None
    args.text = None
    args.output = None

    with patch('sys.stdin.isatty', return_value=True):
        with pytest.raises(SystemExit) as e:
            run_ini2json_lab_logic(args)
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "No input provided" in captured.err

def test_run_ini2json_lab_logic_missing_file(capsys):
    args = MagicMock()
    args.action = None
    args.tui = False
    args.file = "non_existent_file.ini"
    args.text = None
    args.output = None

    with pytest.raises(SystemExit) as e:
        run_ini2json_lab_logic(args)
    assert e.value.code == 1

    captured = capsys.readouterr()
    assert "File 'non_existent_file.ini' not found" in captured.err

@pytest.mark.asyncio
async def test_ini2json_tui_convert():
    """Test TUI conversion flow."""
    from textual.app import App
    class TestApp(App):
        def compose(self):
            yield Ini2JsonLabTab()

    app = TestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Ini2JsonLabTab)
        tab.ini_input.text = "[tui]\nkey=val"
        await pilot.click("#btn-convert")

        output_data = json.loads(tab.json_output.text)
        assert output_data["tui"]["key"] == "val"

@pytest.mark.asyncio
async def test_ini2json_tui_empty_input():
    """Test TUI conversion with empty input."""
    from textual.app import App
    class TestApp(App):
        def compose(self):
            yield Ini2JsonLabTab()

    app = TestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Ini2JsonLabTab)
        tab.ini_input.text = ""
        await pilot.click("#btn-convert")
        assert tab.json_output.text == ""

@pytest.mark.asyncio
async def test_ini2json_tui_invalid_input():
    """Test TUI conversion with invalid INI."""
    from textual.app import App
    class TestApp(App):
        def compose(self):
            yield Ini2JsonLabTab()

    app = TestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Ini2JsonLabTab)
        tab.ini_input.text = "invalid\n[unclosed"
        await pilot.click("#btn-convert")
        assert "Error: Invalid INI string" in tab.json_output.text

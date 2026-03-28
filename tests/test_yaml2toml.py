import pytest
import argparse
import unittest.mock
import unittest.mock
from pathlib import Path
from unittest.mock import patch, mock_open
from shared.yaml2toml_lab import Yaml2TomlManager, run_yaml2toml_lab_logic

@pytest.fixture
def manager():
    return Yaml2TomlManager()

def test_convert_yaml_to_toml_success(manager):
    yaml_input = "key: value\nnested:\n  item: 1"
    result = manager.convert_yaml_to_toml(yaml_input)
    assert 'key = "value"' in result
    assert "[nested]" in result
    assert "item = 1" in result

def test_convert_yaml_to_toml_invalid_yaml(manager):
    invalid_yaml = "key: : value"
    with pytest.raises(ValueError, match="Invalid YAML"):
        manager.convert_yaml_to_toml(invalid_yaml)

def test_convert_yaml_to_toml_non_dict(manager):
    yaml_list = "- item1\n- item2"
    with pytest.raises(ValueError, match="YAML input must be an object"):
        manager.convert_yaml_to_toml(yaml_list)

def test_convert_toml_to_yaml_success(manager):
    toml_input = 'key = "value"\n[nested]\nitem = 1'
    result = manager.convert_toml_to_yaml(toml_input)
    assert "key: value" in result
    assert "nested:" in result
    assert "item: 1" in result

def test_convert_toml_to_yaml_invalid_toml(manager):
    invalid_toml = "key = value"  # Missing quotes for string
    with pytest.raises(ValueError, match="Invalid TOML"):
        manager.convert_toml_to_yaml(invalid_toml)

@patch("shared.yaml2toml_lab.Yaml2TomlManager.convert_yaml_to_toml")
def test_run_logic_yaml2toml_print(mock_convert, capsys):
    mock_convert.return_value = 'key = "value"'
    args = argparse.Namespace(action="yaml2toml", input="key: value", output=None)

    success = run_yaml2toml_lab_logic(args)

    assert success is True
    mock_convert.assert_called_once_with("key: value")
    captured = capsys.readouterr()
    assert 'key = "value"' in captured.out

@patch("shared.yaml2toml_lab.Yaml2TomlManager.convert_yaml_to_toml")
def test_run_logic_yaml2toml_file(mock_convert, capsys):
    mock_convert.return_value = 'key = "value"'
    args = argparse.Namespace(action="yaml2toml", input="key: value", output="out.toml")

    m_open = mock_open()
    with patch("builtins.open", m_open):
        success = run_yaml2toml_lab_logic(args)

    assert success is True
    m_open.assert_called_once_with("out.toml", "w", encoding="utf-8")
    m_open().write.assert_called_once_with('key = "value"')
    captured = capsys.readouterr()
    assert "Output written to out.toml" in captured.out

@patch("shared.yaml2toml_lab.Yaml2TomlManager.convert_toml_to_yaml")
def test_run_logic_toml2yaml_print(mock_convert, capsys):
    mock_convert.return_value = "key: value"
    args = argparse.Namespace(action="toml2yaml", input='key = "value"', output=None)

    success = run_yaml2toml_lab_logic(args)

    assert success is True
    mock_convert.assert_called_once_with('key = "value"')
    captured = capsys.readouterr()
    assert "key: value" in captured.out

@patch("shared.yaml2toml_lab.Yaml2TomlManager.convert_toml_to_yaml")
def test_run_logic_toml2yaml_file(mock_convert, capsys):
    mock_convert.return_value = "key: value"
    args = argparse.Namespace(action="toml2yaml", input='key = "value"', output="out.yaml")

    m_open = mock_open()
    with patch("builtins.open", m_open):
        success = run_yaml2toml_lab_logic(args)

    assert success is True
    m_open.assert_called_once_with("out.yaml", "w", encoding="utf-8")
    m_open().write.assert_called_once_with("key: value")
    captured = capsys.readouterr()
    assert "Output written to out.yaml" in captured.out

def test_run_logic_invalid_action():
    args = argparse.Namespace(action="invalid_action", input="data")
    assert run_yaml2toml_lab_logic(args) is False

@pytest.mark.asyncio
async def test_tui_yaml2toml_app():
    from shared.tui_yaml2toml import Yaml2TomlLabTab
    from textual.app import App
    from typing import Any
    from textual.widgets import Select, TextArea

    class DummyApp(App[Any]):
        def compose(self):
            yield Yaml2TomlLabTab()

    app = DummyApp()
    async with app.run_test(size=(200, 100)) as pilot:
        # Test TOML to JSON convert
        tab = app.query_one(Yaml2TomlLabTab)
        mode_select = tab.query_one("#yaml2toml-mode-select", Select)
        input_ta = tab.query_one("#yaml2toml-input-ta", TextArea)
        output_ta = tab.query_one("#yaml2toml-output-ta", TextArea)

        # TOML to YAML
        mode_select.value = "toml2yaml"
        input_ta.text = 'key = "value"\n[nested]\nitem = 1'
        await pilot.click("#yaml2toml-convert-btn")

        assert "key: value" in output_ta.text
        assert "nested:" in output_ta.text
        assert "item: 1" in output_ta.text

        # YAML to TOML
        mode_select.value = "yaml2toml"
        input_ta.text = "key: value\nnested:\n  item: 1"
        await pilot.click("#yaml2toml-convert-btn")

        assert 'key = "value"' in output_ta.text
        assert "[nested]" in output_ta.text
        assert "item = 1" in output_ta.text

def test_convert_yaml_to_toml_path_success(manager, tmp_path):
    yaml_file = tmp_path / "input.yaml"
    yaml_file.write_text("key: value")
    result = manager.convert_yaml_to_toml(str(yaml_file))
    assert 'key = "value"' in result

def test_convert_toml_to_yaml_path_success(manager, tmp_path):
    toml_file = tmp_path / "input.toml"
    toml_file.write_text('key = "value"')
    result = manager.convert_toml_to_yaml(str(toml_file))
    assert 'key: value' in result

def test_convert_yaml_to_toml_invalid_yaml_file(manager, tmp_path):
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_text("key: : value")
    with pytest.raises(ValueError, match="Invalid YAML"):
        manager.convert_yaml_to_toml(str(yaml_file))

def test_convert_yaml_to_toml_invalid_dict_file(manager, tmp_path):
    yaml_file = tmp_path / "invalid_type.yaml"
    yaml_file.write_text("- item1\n- item2")
    with pytest.raises(ValueError, match="YAML input must be an object"):
        manager.convert_yaml_to_toml(str(yaml_file))

def test_convert_toml_to_yaml_invalid_toml_file(manager, tmp_path):
    toml_file = tmp_path / "invalid.toml"
    toml_file.write_text("key = value")
    with pytest.raises(ValueError, match="Invalid TOML"):
        manager.convert_toml_to_yaml(str(toml_file))

@patch("shared.yaml2toml_lab.Yaml2TomlManager.convert_yaml_to_toml")
def test_run_logic_yaml2toml_exception(mock_convert, capsys):
    mock_convert.side_effect = ValueError("Some error")
    args = argparse.Namespace(action="yaml2toml", input="key: value", output=None)
    success = run_yaml2toml_lab_logic(args)
    assert success is False
    captured = capsys.readouterr()
    assert "Error: Some error" in captured.err

@patch("shared.yaml2toml_lab.Yaml2TomlManager.convert_toml_to_yaml")
def test_run_logic_toml2yaml_exception(mock_convert, capsys):
    mock_convert.side_effect = ValueError("Some error")
    args = argparse.Namespace(action="toml2yaml", input="key = 1", output=None)
    success = run_yaml2toml_lab_logic(args)
    assert success is False
    captured = capsys.readouterr()
    assert "Error: Some error" in captured.err

@pytest.mark.asyncio
async def test_tui_yaml2toml_app_blank_mode():
    from shared.tui_yaml2toml import Yaml2TomlLabTab
    from textual.app import App
    from typing import Any
    from textual.widgets import Select, TextArea, Static

    class DummyApp(App[Any]):
        def compose(self):
            yield Yaml2TomlLabTab()

    app = DummyApp()
    async with app.run_test(size=(200, 100)) as pilot:
        tab = app.query_one(Yaml2TomlLabTab)
        mode_select = tab.query_one("#yaml2toml-mode-select", Select)
        mode_select.clear()

        await pilot.click("#yaml2toml-convert-btn")

        status_static = tab.query_one("#yaml2toml-status", Static)
        assert "Please select a conversion mode" in str(status_static.render())

@pytest.mark.asyncio
async def test_tui_yaml2toml_app_empty_input():
    from shared.tui_yaml2toml import Yaml2TomlLabTab
    from textual.app import App
    from typing import Any
    from textual.widgets import Select, TextArea, Static

    class DummyApp(App[Any]):
        def compose(self):
            yield Yaml2TomlLabTab()

    app = DummyApp()
    async with app.run_test(size=(200, 100)) as pilot:
        tab = app.query_one(Yaml2TomlLabTab)
        input_ta = tab.query_one("#yaml2toml-input-ta", TextArea)
        input_ta.text = "   "

        await pilot.click("#yaml2toml-convert-btn")

        status_static = tab.query_one("#yaml2toml-status", Static)
        assert "Input is empty" in str(status_static.render())

@pytest.mark.asyncio
async def test_tui_yaml2toml_app_conversion_error():
    from shared.tui_yaml2toml import Yaml2TomlLabTab
    from textual.app import App
    from typing import Any
    from textual.widgets import Select, TextArea, Static

    class DummyApp(App[Any]):
        def compose(self):
            yield Yaml2TomlLabTab()

    app = DummyApp()
    async with app.run_test(size=(200, 100)) as pilot:
        tab = app.query_one(Yaml2TomlLabTab)
        input_ta = tab.query_one("#yaml2toml-input-ta", TextArea)
        mode_select = tab.query_one("#yaml2toml-mode-select", Select)

        mode_select.value = "toml2yaml"
        input_ta.text = "invalid = "

        await pilot.click("#yaml2toml-convert-btn")

        status_static = tab.query_one("#yaml2toml-status", Static)
        assert "Error: Invalid TOML" in str(status_static.render())

@pytest.mark.asyncio
async def test_tui_yaml2toml_app_unknown_mode():
    from shared.tui_yaml2toml import Yaml2TomlLabTab
    from textual.app import App
    from typing import Any
    from textual.widgets import Select, TextArea, Static

    class DummyApp(App[Any]):
        def compose(self):
            yield Yaml2TomlLabTab()

    app = DummyApp()
    async with app.run_test(size=(200, 100)) as pilot:
        tab = app.query_one(Yaml2TomlLabTab)
        input_ta = tab.query_one("#yaml2toml-input-ta", TextArea)
        mode_select = tab.query_one("#yaml2toml-mode-select", Select)

        # We need to bypass the select's valid options for test purposes
        # Since Select doesn't let us easily set an invalid value, we'll patch the manager or the action
        # Actually, let's just patch mode_select.value for the duration of the convert

        mode_select.value = "yaml2toml" # Set valid first
        # To bypass Select validation, we can directly manipulate it or mock the value access
        with patch.object(type(mode_select), 'value', new_callable=unittest.mock.PropertyMock) as mock_val:
            mock_val.return_value = "unknown_mode"
            input_ta.text = "key: val"
            await pilot.click("#yaml2toml-convert-btn")

        status_static = tab.query_one("#yaml2toml-status", Static)
        assert "Unknown mode: unknown_mode" in str(status_static.render())


def test_convert_yaml_to_toml_file_not_found(manager, tmp_path):
    # Pass a path that doesn't exist, it should fallback to parsing it as string
    # but fail since it's an invalid yaml dict.
    # To hit line 22, it needs to be a path-like string (<1000 chars) that doesn't exist.
    with pytest.raises(ValueError, match="YAML input must be an object"):
        manager.convert_yaml_to_toml("non_existent_file.yaml")

def test_convert_toml_to_yaml_file_not_found(manager, tmp_path):
    with pytest.raises(ValueError, match="Invalid TOML"):
        manager.convert_toml_to_yaml("non_existent_file.toml")

def test_convert_yaml_to_toml_oserror(manager):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = OSError("Mock OS Error")
        with pytest.raises(ValueError):
             manager.convert_yaml_to_toml("some_string")

def test_convert_toml_to_yaml_oserror(manager):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = OSError("Mock OS Error")
        with pytest.raises(ValueError):
             manager.convert_toml_to_yaml("some_string")

def test_convert_yaml_to_toml_oserror_invalid_yaml(manager):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = OSError("Mock OS Error")
        with pytest.raises(ValueError):
             manager.convert_yaml_to_toml("invalid : : yaml")

def test_convert_toml_to_yaml_oserror_invalid_toml(manager):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = OSError("Mock OS Error")
        with pytest.raises(ValueError):
             manager.convert_toml_to_yaml("invalid = ")


def test_convert_yaml_to_toml_exception_propagation(manager):
    with patch("yaml.safe_load", side_effect=Exception("Unexpected")):
        with pytest.raises(ValueError, match="Error converting YAML to TOML: Unexpected"):
            manager.convert_yaml_to_toml("data")

def test_convert_toml_to_yaml_exception_propagation(manager):
    with patch("tomlkit.parse", side_effect=Exception("Unexpected")):
        with pytest.raises(ValueError, match="Error converting TOML to YAML: Unexpected"):
            manager.convert_toml_to_yaml("data")


def test_convert_yaml_to_toml_oserror_fallback_success(manager):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = OSError("Mock OS Error")
        result = manager.convert_yaml_to_toml("key: value")
        assert 'key = "value"' in result

def test_convert_toml_to_yaml_oserror_fallback_success(manager):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = OSError("Mock OS Error")
        result = manager.convert_toml_to_yaml('key = "value"')
        assert 'key: value' in result

def test_convert_yaml_to_toml_invalid_type_fallback(manager):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = OSError("Mock OS Error")
        with pytest.raises(ValueError, match="YAML input must be an object"):
            manager.convert_yaml_to_toml("[]")


def test_convert_yaml_to_toml_too_long(manager):
    long_string = "a: " + "b" * 1000
    result = manager.convert_yaml_to_toml(long_string)
    assert 'a = "bbbb' in result

def test_convert_toml_to_yaml_too_long(manager):
    long_string = 'a = "' + 'b' * 1000 + '"'
    result = manager.convert_toml_to_yaml(long_string)
    assert "a: bbbb" in result

def test_convert_toml_to_yaml_fallback_invalid_toml(manager):
    with patch("pathlib.Path.exists") as mock_exists:
         mock_exists.side_effect = OSError("Mock OS Error")
         with pytest.raises(ValueError, match="Invalid TOML:"):
              manager.convert_toml_to_yaml("invalid : \0")

def test_convert_toml_to_yaml_fallback_other_exception(manager):
    with patch("tomlkit.parse") as mock_parse:
        mock_parse.side_effect = Exception("General Failure")
        with pytest.raises(ValueError, match="Error converting TOML to YAML: General Failure"):
             manager.convert_toml_to_yaml('a = 1')


def test_convert_toml_to_yaml_fallback_other_exception_within_oserror(manager):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = OSError("Mock OS Error")
        with patch("tomlkit.parse") as mock_parse:
             mock_parse.side_effect = Exception("Fallback Failure")
             with pytest.raises(ValueError, match="Error converting TOML to YAML: Fallback Failure"):
                  manager.convert_toml_to_yaml('a = 1')


def test_convert_yaml_to_toml_fallback_other_exception_within_oserror(manager):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = OSError("Mock OS Error")
        with patch("yaml.safe_load") as mock_parse:
             mock_parse.side_effect = Exception("Fallback Failure")
             with pytest.raises(ValueError, match="Error converting YAML to TOML: Fallback Failure"):
                  manager.convert_yaml_to_toml('a: 1')

def test_convert_toml_to_yaml_other_exception_unwrapped(manager):
    with patch("tomlkit.parse") as mock_parse:
         mock_parse.side_effect = TypeError("Other unhandled type error")
         with pytest.raises(ValueError, match="Error converting TOML to YAML: Other unhandled type error"):
              manager.convert_toml_to_yaml("input")

def test_convert_toml_to_yaml_other_exception_unwrapped_val(manager):
    with patch("tomlkit.parse") as mock_parse:
         mock_parse.side_effect = ValueError("ValueError is raised back up")
         with pytest.raises(ValueError, match="ValueError is raised back up"):
              manager.convert_toml_to_yaml("input")

def test_convert_yaml_to_toml_other_exception_unwrapped_val(manager):
    with patch("yaml.safe_load") as mock_parse:
         mock_parse.side_effect = ValueError("ValueError is raised back up")
         with pytest.raises(ValueError, match="ValueError is raised back up"):
              manager.convert_yaml_to_toml("input")

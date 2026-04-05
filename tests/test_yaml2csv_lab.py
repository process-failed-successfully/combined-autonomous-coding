import pytest
import argparse
import io
import csv
from pathlib import Path
from unittest.mock import patch

from shared.yaml2csv_lab import Yaml2CsvManager, run_yaml2csv_lab_logic


def test_yaml2csv_manager_convert_string():
    """Test converting YAML string to CSV string."""
    manager = Yaml2CsvManager()
    yaml_data = """
    - name: Alice
      age: 30
      city: New York
    - name: Bob
      age: 25
      city: Los Angeles
    """
    csv_str = manager.convert(yaml_data)

    # Parse resulting CSV back
    reader = csv.DictReader(io.StringIO(csv_str))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
    assert rows[1]["age"] == "25"


def test_yaml2csv_manager_convert_nested():
    """Test flattening nested YAML objects to CSV."""
    manager = Yaml2CsvManager()
    yaml_data = """
    name: Alice
    address:
      city: New York
      zip: "10001"
    """
    csv_str = manager.convert(yaml_data)

    reader = csv.DictReader(io.StringIO(csv_str))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
    assert rows[0]["address.city"] == "New York"
    assert rows[0]["address.zip"] == "10001"


def test_yaml2csv_manager_convert_list_property():
    """Test flattening when a property is a list (should be JSON stringified)."""
    manager = Yaml2CsvManager()
    yaml_data = """
    name: Alice
    tags:
      - admin
      - user
    """
    csv_str = manager.convert(yaml_data)

    reader = csv.DictReader(io.StringIO(csv_str))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
    assert rows[0]["tags"] == '["admin", "user"]'


def test_yaml2csv_manager_invalid_yaml():
    """Test error handling for invalid YAML."""
    manager = Yaml2CsvManager()
    with pytest.raises(ValueError, match="Invalid YAML string"):
        manager.convert("invalid: yaml: :")


def test_yaml2csv_manager_invalid_data_type():
    """Test error handling for non-object/array input."""
    manager = Yaml2CsvManager()
    with pytest.raises(ValueError, match="YAML data must be an object or an array of objects."):
        manager.convert("123")


def test_yaml2csv_manager_empty():
    """Test handling empty data."""
    manager = Yaml2CsvManager()
    assert manager.convert("[]") == ""


@patch('sys.stdout', new_callable=io.StringIO)
def test_run_yaml2csv_lab_logic_text(mock_stdout):
    """Test CLI dispatch with text input."""
    args = argparse.Namespace(
        text="""
        name: Charlie
        age: 40
        """,
        file=None,
        output=None,
        tui=False,
        action=None
    )
    with patch('sys.exit') as mock_exit:
        run_yaml2csv_lab_logic(args)
        mock_exit.assert_not_called()

    output = mock_stdout.getvalue()
    assert "age,name" in output
    assert "40,Charlie" in output


def test_run_yaml2csv_lab_logic_file(tmp_path):
    """Test CLI dispatch with file input and output."""
    yaml_file = tmp_path / "input.yaml"
    yaml_file.write_text("name: David\n", encoding="utf-8")

    csv_file = tmp_path / "output.csv"

    args = argparse.Namespace(
        text=None,
        file=str(yaml_file),
        output=str(csv_file),
        tui=False,
        action=None
    )
    with patch('sys.stdout'):
        with patch('sys.exit') as mock_exit:
            run_yaml2csv_lab_logic(args)
            mock_exit.assert_not_called()

    assert csv_file.exists()
    assert "name" in csv_file.read_text()
    assert "David" in csv_file.read_text()


@patch('sys.stderr', new_callable=io.StringIO)
def test_run_yaml2csv_lab_logic_missing_input(mock_stderr):
    """Test CLI dispatch missing input."""
    args = argparse.Namespace(
        text=None,
        file=None,
        output=None,
        tui=False,
        action=None
    )
    # Simulate not being a tty so stdin isn't read by default (if testing environment acts like it)
    with patch('sys.stdin.isatty', return_value=True):
        with pytest.raises(SystemExit) as e:
            run_yaml2csv_lab_logic(args)
        assert e.value.code == 1

    assert "No input provided" in mock_stderr.getvalue()


@pytest.mark.asyncio
async def test_tui_yaml2csv():
    """Test the Textual TUI interface."""
    pytest.importorskip("textual")
    from textual.app import App, ComposeResult
    from shared.tui_yaml2csv import Yaml2CsvTab
    from textual.widgets import TextArea, Static

    class MockApp(App):
        def compose(self) -> ComposeResult:
            yield Yaml2CsvTab()

    app = MockApp()
    async with app.run_test(size=(80, 40)) as pilot:
        await pilot.pause(0.1)

        input_ta = app.query_one("#yaml2csv-input-ta", TextArea)
        output_ta = app.query_one("#yaml2csv-output-ta", TextArea)
        status_static = app.query_one("#yaml2csv-status", Static)

        # Test empty conversion
        app.query_one("#yaml2csv-convert-btn").press()
        await pilot.pause()
        await pilot.pause(0.1)
        assert "Input is empty" in str(status_static.render())

        # Test valid conversion
        yaml_data = """
        user:
          id: 123
          role: admin
        """
        input_ta.load_text(yaml_data)
        app.query_one("#yaml2csv-convert-btn").press()
        await pilot.pause()
        await pilot.pause(0.1)

        assert "Conversion successful" in str(status_static.render())
        assert "user.id,user.role" in output_ta.text
        assert "123,admin" in output_ta.text

        # Test invalid conversion
        input_ta.load_text("invalid: [yaml: [")
        app.query_one("#yaml2csv-convert-btn").press()
        await pilot.pause()
        await pilot.pause(0.1)

        assert "Error:" in str(status_static.render())


def test_yaml2csv_manager_convert_dict():
    """Test converting YAML dict to CSV string directly."""
    manager = Yaml2CsvManager()
    yaml_data = [{"name": "Eve", "age": "45"}]
    csv_str = manager.convert(yaml_data)

    reader = csv.DictReader(io.StringIO(csv_str))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["name"] == "Eve"
    assert rows[0]["age"] == "45"

@patch('builtins.__import__')
def test_run_yaml2csv_lab_logic_tui(mock_import):
    """Test CLI dispatch for TUI."""
    args = argparse.Namespace(
        tui=True,
        action=None,
        project_dir=Path(".")
    )

    # Mocking AgentTUI and loop to avoid actually starting TUI
    import asyncio
    class MockLoop:
        def is_running(self):
            return False

    with patch('asyncio.get_running_loop', return_value=MockLoop()):
        with pytest.raises(SystemExit) as e:
            run_yaml2csv_lab_logic(args)
        assert e.value.code == 0


def test_run_yaml2csv_lab_logic_missing_file(tmp_path):
    """Test CLI dispatch with missing file."""
    yaml_file = tmp_path / "missing.yaml"

    args = argparse.Namespace(
        text=None,
        file=str(yaml_file),
        output=None,
        tui=False,
        action=None
    )

    with pytest.raises(SystemExit) as e:
        run_yaml2csv_lab_logic(args)
    assert e.value.code == 1

def test_run_yaml2csv_lab_logic_exception():
    """Test CLI dispatch exception handling."""
    args = argparse.Namespace(
        text="invalid: [yaml: [",
        file=None,
        output=None,
        tui=False,
        action=None
    )

    with pytest.raises(SystemExit) as e:
        run_yaml2csv_lab_logic(args)
    assert e.value.code == 1

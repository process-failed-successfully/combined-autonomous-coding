import pytest
import sys
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO
from shared.csv2yaml_lab import Csv2YamlManager, run_csv2yaml_lab_logic
import yaml

@pytest.fixture
def manager():
    return Csv2YamlManager()

def test_convert_valid_csv(manager):
    csv_text = "name,age\nAlice,30\nBob,25"
    result = manager.convert(csv_text)
    assert len(result) == 2
    assert result[0] == {"name": "Alice", "age": "30"}
    assert result[1] == {"name": "Bob", "age": "25"}

def test_convert_empty_csv(manager):
    csv_text = ""
    result = manager.convert(csv_text)
    assert result == []

def test_convert_custom_delimiter(manager):
    csv_text = "name|age\nAlice|30"
    result = manager.convert(csv_text, delimiter='|')
    assert len(result) == 1
    assert result[0] == {"name": "Alice", "age": "30"}

def test_process_file_success(manager, tmp_path):
    input_file = tmp_path / "input.csv"
    input_file.write_text("name,age\nAlice,30\nBob,25")

    output_file = tmp_path / "output.yaml"

    result = manager.process_file(input_file, output_file)
    assert result is True
    assert output_file.exists()

    with open(output_file, 'r') as f:
        data = yaml.safe_load(f)

    assert len(data) == 2
    assert data[0] == {"name": "Alice", "age": "30"}

def test_process_file_stdout_success(manager, tmp_path, capsys):
    input_file = tmp_path / "input.csv"
    input_file.write_text("name,age\nAlice,30")

    result = manager.process_file(input_file, None)
    assert result is True

    captured = capsys.readouterr()
    expected_yaml = yaml.dump([{"name": "Alice", "age": "30"}], sort_keys=False)
    assert captured.out.strip() == expected_yaml.strip()

def test_process_file_not_found(manager, capsys):
    filepath = Path("nonexistent.csv")
    result = manager.process_file(filepath)
    assert result is False
    captured = capsys.readouterr()
    assert "Error: File" in captured.err

@patch('shared.csv2yaml_lab.Csv2YamlManager.process_file')
def test_run_csv2yaml_lab_logic_file(mock_process_file):
    mock_process_file.return_value = True
    args = argparse.Namespace(
        tui=False,
        file="input.csv",
        output="output.yaml",
        delimiter=",",
        text=None
    )
    result = run_csv2yaml_lab_logic(args)
    assert result is True
    mock_process_file.assert_called_once_with(Path("input.csv"), Path("output.yaml"), delimiter=",")

@patch('sys.stdout', new_callable=StringIO)
def test_run_csv2yaml_lab_logic_text(mock_stdout):
    args = argparse.Namespace(
        tui=False,
        file=None,
        output=None,
        delimiter=",",
        text="name,age\nAlice,30"
    )
    result = run_csv2yaml_lab_logic(args)
    assert result is True

    expected_yaml = yaml.dump([{"name": "Alice", "age": "30"}], sort_keys=False)
    assert mock_stdout.getvalue().strip() == expected_yaml.strip()

@patch('sys.stderr', new_callable=StringIO)
def test_run_csv2yaml_lab_logic_no_args(mock_stderr):
    args = argparse.Namespace(
        tui=False,
        file=None,
        output=None,
        delimiter=",",
        text=None
    )
    result = run_csv2yaml_lab_logic(args)
    assert result is False
    assert "Either --file or --text must be provided." in mock_stderr.getvalue()

@patch('sys.exit')
def test_run_csv2yaml_lab_logic_tui(mock_exit):
    pytest.importorskip("textual")

    mock_app_instance = MagicMock()

    with patch('shared.tui.AgentTUI') as mock_app_class:
        mock_app_class.return_value = mock_app_instance

        with patch('asyncio.get_running_loop', side_effect=RuntimeError('no loop')):
            args = argparse.Namespace(
                tui=True,
                project_dir=Path(".")
            )

            run_csv2yaml_lab_logic(args)

            mock_app_class.assert_called_once_with(project_dir=Path("."), start_tab="tab-csv2yaml")
            mock_app_instance.run.assert_called_once()
            mock_exit.assert_called_once_with(0)

def test_tui_component():
    pytest.importorskip("textual")
    from textual.app import App
    from shared.tui_csv2yaml import Csv2YamlTab
    from textual.widgets import TextArea, Input

    class TestApp(App):
        def compose(self):
            yield Csv2YamlTab()

    async def run_test():
        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Csv2YamlTab)
            assert tab is not None

            # Test default setup
            assert app.query_one("#csv2yaml-delimiter", Input).value == ","

            # Test text conversion
            app.query_one("#csv2yaml-input", TextArea).text = "name,age\nAlice,30"
            await pilot.click("#btn-convert-csv2yaml")
            await pilot.pause()

            expected_yaml = yaml.dump([{"name": "Alice", "age": "30"}], sort_keys=False, allow_unicode=True)
            assert app.query_one("#csv2yaml-output", TextArea).text == expected_yaml

            # Test clear
            await pilot.click("#btn-clear-csv2yaml")
            await pilot.pause()

            assert app.query_one("#csv2yaml-input", TextArea).text == ""
            assert app.query_one("#csv2yaml-output", TextArea).text == ""

    import asyncio
    asyncio.run(run_test())

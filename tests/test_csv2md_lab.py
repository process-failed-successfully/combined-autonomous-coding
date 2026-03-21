import pytest
import io
import argparse
from unittest.mock import patch, MagicMock

from shared.csv2md_lab import Csv2MdManager, run_csv2md_lab_logic

class TestCsv2MdManager:
    @pytest.fixture
    def manager(self):
        return Csv2MdManager()

    def test_convert_to_markdown_valid(self, manager):
        csv_data = "Name,Age,City\nAlice,30,New York\nBob,25,San Francisco"
        expected = (
            "| Name  | Age | City          |\n"
            "| ----- | --- | ------------- |\n"
            "| Alice | 30  | New York      |\n"
            "| Bob   | 25  | San Francisco |"
        )
        result = manager.convert_to_markdown(csv_data)
        assert result == expected

    def test_convert_to_markdown_semicolon(self, manager):
        csv_data = "Name;Age;City\nAlice;30;New York\nBob;25;San Francisco"
        expected = (
            "| Name  | Age | City          |\n"
            "| ----- | --- | ------------- |\n"
            "| Alice | 30  | New York      |\n"
            "| Bob   | 25  | San Francisco |"
        )
        result = manager.convert_to_markdown(csv_data, delimiter=';')
        assert result == expected

    def test_convert_to_markdown_empty(self, manager):
        assert manager.convert_to_markdown("") == ""
        assert manager.convert_to_markdown("   \n  ") == ""

    def test_convert_to_markdown_missing_columns(self, manager):
        csv_data = "col1,col2,col3\nval1,val2\nval1,val2,val3,val4"
        expected = (
            "| col1 | col2 | col3 |\n"
            "| ---- | ---- | ---- |\n"
            "| val1 | val2 |      |\n"
            "| val1 | val2 | val3 |"
        )
        result = manager.convert_to_markdown(csv_data)
        assert result == expected

    def test_convert_to_markdown_newline_in_cell(self, manager):
        csv_data = 'Col1,Col2\n"Line1\nLine2",Val'
        expected = (
            "| Col1        | Col2 |\n"
            "| ----------- | ---- |\n"
            "| Line1 Line2 | Val  |"
        )
        result = manager.convert_to_markdown(csv_data)
        assert result == expected

def test_run_csv2md_lab_logic_text():
    args = argparse.Namespace(text="A,B\n1,2", file=None, tui=False, delimiter=",", output=None)
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_csv2md_lab_logic(args)
        assert success
        output = fake_stdout.getvalue().strip()
        assert "| A | B |" in output
        assert "| --- | --- |" in output
        assert "| 1 | 2 |" in output

def test_run_csv2md_lab_logic_stdin():
    args = argparse.Namespace(text=None, file=None, tui=False, delimiter=",", output=None)
    with patch('sys.stdin', io.StringIO("A,B\n1,2")), \
         patch('sys.stdin.isatty', return_value=False), \
         patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_csv2md_lab_logic(args)
        assert success
        assert "| A | B |" in fake_stdout.getvalue()

def test_run_csv2md_lab_logic_no_input():
    args = argparse.Namespace(text=None, file=None, tui=False, delimiter=",", output=None)
    with patch('sys.stdin.isatty', return_value=True), \
         patch('sys.stderr', new=io.StringIO()) as fake_stderr:
        success = run_csv2md_lab_logic(args)
        assert not success
        assert "No input provided" in fake_stderr.getvalue()

def test_run_csv2md_lab_logic_file(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("A,B\n1,2")
    args = argparse.Namespace(text=None, file=str(csv_file), tui=False, delimiter=",", output=None)
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_csv2md_lab_logic(args)
        assert success
        assert "| A | B |" in fake_stdout.getvalue()

def test_run_csv2md_lab_logic_output_file(tmp_path):
    output_file = tmp_path / "out.md"
    args = argparse.Namespace(text="A,B\n1,2", file=None, tui=False, delimiter=",", output=str(output_file))
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_csv2md_lab_logic(args)
        assert success
        assert output_file.exists()
        content = output_file.read_text()
        assert "| A | B |" in content

def test_run_csv2md_lab_logic_tui():
    args = argparse.Namespace(tui=True, project_dir=".")

    mock_app = MagicMock()
    # Ensure run_async exists so the asyncio checking branch executes
    mock_app.run_async = MagicMock()
    mock_agent_tui = MagicMock(return_value=mock_app)

    with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
        with patch('sys.exit') as mock_exit:
            success = run_csv2md_lab_logic(args)
            # Because we mocked sys.exit, run_csv2md_lab_logic will continue and return True
            assert success
            mock_exit.assert_called_once_with(0)

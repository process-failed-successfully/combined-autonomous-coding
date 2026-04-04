import pytest
import io
import argparse
from unittest.mock import patch, MagicMock

from textual.app import App, ComposeResult

from shared.csv2yaml_lab import Csv2YamlManager, run_csv2yaml_lab_logic
from shared.tui_csv2yaml import Csv2YamlTab


class DummyApp(App[None]):
    def compose(self) -> ComposeResult:
        yield Csv2YamlTab()


class TestCsv2YamlManager:
    @pytest.fixture
    def manager(self):
        return Csv2YamlManager()

    def test_convert_csv_to_yaml_valid(self, manager):
        csv_data = "Name,Age,City\nAlice,30,New York\nBob,25,San Francisco"
        result = manager.convert_csv_to_yaml(csv_data)

        # Validating output contains the expected substrings
        assert "- Name: Alice" in result
        assert "  Age: '30'" in result
        assert "  City: New York" in result
        assert "- Name: Bob" in result
        assert "  Age: '25'" in result
        assert "  City: San Francisco" in result

    def test_convert_csv_to_yaml_semicolon(self, manager):
        csv_data = "Name;Age;City\nAlice;30;New York\nBob;25;San Francisco"
        result = manager.convert_csv_to_yaml(csv_data, delimiter=';')

        assert "- Name: Alice" in result
        assert "  Age: '30'" in result
        assert "  City: New York" in result

    def test_convert_csv_to_yaml_empty(self, manager):
        assert manager.convert_csv_to_yaml("") == ""
        assert manager.convert_csv_to_yaml("   \n  ") == ""

    def test_convert_csv_to_yaml_invalid(self, manager):
        with patch('csv.DictReader', side_effect=Exception("mocked error")):
            with pytest.raises(ValueError, match="Failed to parse CSV or generate YAML"):
                manager.convert_csv_to_yaml("bad data")


def test_run_csv2yaml_lab_logic_text():
    args = argparse.Namespace(text="A,B\n1,2", file=None, tui=False, delimiter=",", output=None)
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_csv2yaml_lab_logic(args)
        assert success
        output = fake_stdout.getvalue().strip()
        assert "- A: '1'" in output
        assert "  B: '2'" in output


def test_run_csv2yaml_lab_logic_stdin():
    args = argparse.Namespace(text=None, file=None, tui=False, delimiter=",", output=None)
    with patch('sys.stdin', io.StringIO("A,B\n1,2")), \
         patch('sys.stdin.isatty', return_value=False), \
         patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_csv2yaml_lab_logic(args)
        assert success
        assert "- A: '1'" in fake_stdout.getvalue()


def test_run_csv2yaml_lab_logic_no_input():
    args = argparse.Namespace(text=None, file=None, tui=False, delimiter=",", output=None)
    with patch('sys.stdin.isatty', return_value=True), \
         patch('sys.stderr', new=io.StringIO()) as fake_stderr:
        success = run_csv2yaml_lab_logic(args)
        assert not success
        assert "No input provided" in fake_stderr.getvalue()


def test_run_csv2yaml_lab_logic_file(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("A,B\n1,2")
    args = argparse.Namespace(text=None, file=str(csv_file), tui=False, delimiter=",", output=None)
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_csv2yaml_lab_logic(args)
        assert success
        assert "- A: '1'" in fake_stdout.getvalue()


def test_run_csv2yaml_lab_logic_file_not_found(tmp_path):
    args = argparse.Namespace(text=None, file=str(tmp_path / "not_found.csv"), tui=False, delimiter=",", output=None)
    with patch('sys.stderr', new=io.StringIO()) as fake_stderr:
        success = run_csv2yaml_lab_logic(args)
        assert not success
        assert "Error reading file" in fake_stderr.getvalue()


def test_run_csv2yaml_lab_logic_output_file(tmp_path):
    output_file = tmp_path / "out.yaml"
    args = argparse.Namespace(text="A,B\n1,2", file=None, tui=False, delimiter=",", output=str(output_file))
    with patch('sys.stdout', new=io.StringIO()):
        success = run_csv2yaml_lab_logic(args)
        assert success
        assert output_file.exists()
        content = output_file.read_text()
        assert "- A: '1'" in content
        assert "  B: '2'" in content


def test_run_csv2yaml_lab_logic_error():
    args = argparse.Namespace(text="A,B\n1,2", file=None, tui=False, delimiter=",", output=None)
    with patch('shared.csv2yaml_lab.Csv2YamlManager.convert_csv_to_yaml', side_effect=ValueError("mock error")):
        with patch('sys.stderr', new=io.StringIO()) as fake_stderr:
            success = run_csv2yaml_lab_logic(args)
            assert not success
            assert "Error converting CSV to YAML" in fake_stderr.getvalue()


def test_run_csv2yaml_lab_logic_tui():
    args = argparse.Namespace(tui=True, project_dir=".")

    mock_app = MagicMock()
    mock_agent_tui = MagicMock(return_value=mock_app)

    with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
        with patch('asyncio.get_running_loop') as mock_get_running_loop, \
             patch('asyncio.ensure_future') as mock_ensure_future:
            # Simulate no running loop
            mock_get_running_loop.side_effect = RuntimeError("no running event loop")
            success = run_csv2yaml_lab_logic(args)
            assert success
            mock_agent_tui.assert_called_once()
            mock_app.run.assert_called_once()

            # Reset
            mock_agent_tui.reset_mock()
            mock_app.run.reset_mock()

            # Simulate running loop
            mock_loop = MagicMock()
            mock_loop.is_running.return_value = True
            mock_get_running_loop.side_effect = None
            mock_get_running_loop.return_value = mock_loop

            success = run_csv2yaml_lab_logic(args)
            assert success
            mock_agent_tui.assert_called_once()
            mock_ensure_future.assert_called_once_with(mock_app.run_async())


@pytest.mark.asyncio
async def test_tui_csv2yaml_tab_integration():
    app = DummyApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Csv2YamlTab)

        # Test valid conversion
        input_ta = tab.query_one("#csv2yaml-input-ta")
        input_ta.text = "Name,Age\nAlice,30"

        btn = tab.query_one("#csv2yaml-convert-btn")
        btn.press()
        await pilot.pause()

        output_ta = tab.query_one("#csv2yaml-output-ta")
        assert "- Name: Alice" in output_ta.text
        assert "  Age: '30'" in output_ta.text

        status = tab.query_one("#csv2yaml-status")
        assert "Conversion successful" in str(status.render())

        # Test empty
        input_ta.text = ""
        btn.press()
        await pilot.pause()
        assert output_ta.text == ""
        assert "Input is empty" in str(status.render())

        # Test error
        with patch.object(tab.manager, 'convert_csv_to_yaml', side_effect=Exception("mock conversion error")):
            input_ta.text = "Something"
            btn.press()
            await pilot.pause()
            assert output_ta.text == ""
            assert "mock conversion error" in str(status.render())
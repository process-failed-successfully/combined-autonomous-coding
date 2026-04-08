import pytest
import io
import argparse
from unittest.mock import patch, MagicMock

from textual.app import App, ComposeResult

from shared.csv2xml_lab import Csv2XmlManager, run_csv2xml_lab_logic
from shared.tui_csv2xml import Csv2XmlTab


class DummyApp(App[None]):
    def compose(self) -> ComposeResult:
        yield Csv2XmlTab()


class TestCsv2XmlManager:
    @pytest.fixture
    def manager(self):
        return Csv2XmlManager()

    def test_convert_valid_csv(self, manager):
        csv_data = "name,age\nAlice,30\nBob,25"
        result = manager.convert(csv_data)

        assert "<root>" in result
        assert "<item>" in result
        assert "<name>Alice</name>" in result
        assert "<age>30</age>" in result
        assert "<name>Bob</name>" in result
        assert "<age>25</age>" in result

    def test_convert_custom_elements(self, manager):
        csv_data = "id,value\n1,yes"
        result = manager.convert(csv_data, root_element="data", row_element="record")

        assert "<data>" in result
        assert "<record>" in result
        assert "<id>1</id>" in result
        assert "<value>yes</value>" in result

    def test_convert_invalid_tags(self, manager):
        csv_data = "123 invalid tag,normal\nval1,val2"
        result = manager.convert(csv_data)

        # Tags starting with number should be prefixed with _
        assert "<_123_invalid_tag>val1</_123_invalid_tag>" in result
        assert "<normal>val2</normal>" in result

    def test_convert_empty(self, manager):
        result = manager.convert("")
        assert result.strip() == ""

    def test_convert_semicolon_delim(self, manager):
        csv_data = "name;age\nAlice;30\nBob;25"
        result = manager.convert(csv_data, delimiter=';')

        assert "<root>" in result
        assert "<name>Alice</name>" in result
        assert "<age>30</age>" in result

    def test_process_file(self, manager, tmp_path):
        input_file = tmp_path / "test.csv"
        input_file.write_text("a,b\n1,2")
        output_file = tmp_path / "out.xml"

        with patch('sys.stdout', new=io.StringIO()):
            success = manager.process_file(input_file, output_file)
            assert success
            assert output_file.exists()
            content = output_file.read_text()
            assert "<a>1</a>" in content
            assert "<b>2</b>" in content

    def test_process_file_stdout(self, manager, tmp_path):
        input_file = tmp_path / "test.csv"
        input_file.write_text("a,b\n1,2")

        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            success = manager.process_file(input_file)
            assert success
            content = fake_stdout.getvalue()
            assert "<a>1</a>" in content


def test_run_csv2xml_lab_logic_text():
    args = argparse.Namespace(text="A,B\n1,2", file=None, tui=False, delimiter=",", root="root", row="item", output=None)
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_csv2xml_lab_logic(args)
        assert success
        output = fake_stdout.getvalue().strip()
        assert "<root>" in output
        assert "<A>1</A>" in output
        assert "<B>2</B>" in output


def test_run_csv2xml_lab_logic_stdin():
    args = argparse.Namespace(text=None, file=None, tui=False, delimiter=",", root="root", row="item", output=None)
    with patch('sys.stdin', io.StringIO("A,B\n1,2")), \
         patch('sys.stdin.isatty', return_value=False), \
         patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_csv2xml_lab_logic(args)
        assert success
        assert "<root>" in fake_stdout.getvalue()


def test_run_csv2xml_lab_logic_no_input():
    args = argparse.Namespace(text=None, file=None, tui=False, delimiter=",", root="root", row="item", output=None)
    with patch('sys.stdin.isatty', return_value=True), \
         patch('sys.stderr', new=io.StringIO()) as fake_stderr:
        success = run_csv2xml_lab_logic(args)
        assert not success
        assert "No input provided" in fake_stderr.getvalue()


def test_run_csv2xml_lab_logic_tui():
    args = argparse.Namespace(tui=True, project_dir=".")

    mock_app = MagicMock()
    mock_agent_tui = MagicMock(return_value=mock_app)

    with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
        with patch('asyncio.get_running_loop') as mock_get_running_loop, \
             patch('asyncio.ensure_future'), \
             patch('sys.exit') as mock_exit, \
             patch('sys.stdin.isatty', return_value=True):
            # Simulate no running loop
            mock_get_running_loop.side_effect = RuntimeError("no running event loop")
            run_csv2xml_lab_logic(args)
            mock_agent_tui.assert_called_once()
            mock_app.run.assert_called_once()
            mock_exit.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_tui_csv2xml_tab_integration():
    app = DummyApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Csv2XmlTab)

        # Test valid conversion
        input_ta = tab.query_one("#csv2xml_input")
        input_ta.text = "Name,Age\nAlice,30"

        btn = tab.query_one("#btn_convert")
        btn.press()
        await pilot.pause()

        output_ta = tab.query_one("#csv2xml_output")
        assert "<root>" in output_ta.text
        assert "<item>" in output_ta.text
        assert "<Name>Alice</Name>" in output_ta.text
        assert "<Age>30</Age>" in output_ta.text

        # Test clear
        clear_btn = tab.query_one("#btn_clear")
        clear_btn.press()
        await pilot.pause()
        assert input_ta.text == ""
        assert output_ta.text == ""

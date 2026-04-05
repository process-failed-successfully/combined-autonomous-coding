import pytest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch, MagicMock

from shared.csv2xml_lab import Csv2XmlManager, run_csv2xml_lab_logic

# TUI check


class TestCsv2XmlManager:
    def setup_method(self):
        self.manager = Csv2XmlManager()

    def test_convert_string_basic(self):
        csv_data = "name,age\nAlice,30\nBob,25"
        xml_result = self.manager.convert_string(csv_data)

        # Verify it parses back to XML
        root = ET.fromstring(xml_result)
        assert root.tag == "root"
        assert len(root) == 2

        row1 = root[0]
        assert row1.tag == "row"
        assert row1.find("name").text == "Alice"
        assert row1.find("age").text == "30"

    def test_convert_string_empty(self):
        csv_data = ""
        xml_result = self.manager.convert_string(csv_data)
        assert "<root></root>" in xml_result

    def test_convert_string_custom_tags(self):
        csv_data = "city,pop\nNY,8000\nLA,4000"
        xml_result = self.manager.convert_string(csv_data, delimiter=",", root_tag="data", row_tag="city_info")

        root = ET.fromstring(xml_result)
        assert root.tag == "data"
        assert root[0].tag == "city_info"
        assert root[0].find("city").text == "NY"

    def test_convert_string_invalid_headers(self):
        csv_data = "123invalid,valid name,   \nval1,val2,val3"
        xml_result = self.manager.convert_string(csv_data)
        root = ET.fromstring(xml_result)
        row = root[0]

        # "123invalid" should be prefixed with "_" because XML tags cannot start with numbers
        assert row.find("_123invalid") is not None
        # "valid name" should have space replaced with "_"
        assert row.find("valid_name") is not None

        assert row.find("_123invalid").text == "val1"
        assert row.find("valid_name").text == "val2"
        assert row.find("column").text == "val3"

    def test_convert_file(self, tmp_path):
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,val\n1,A", encoding="utf-8")

        xml_result = self.manager.convert_file(test_file)
        assert "<id>1</id>" in xml_result

    def test_convert_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            self.manager.convert_file(Path("nonexistent.csv"))


class TestCsv2XmlCLI:
    @patch('sys.stdout', new_callable=MagicMock)
    def test_run_logic_with_text(self, mock_stdout):
        args = MagicMock()
        args.file = None
        args.text = "col1,col2\nval1,val2"
        args.output = None
        args.delimiter = ","
        args.root_tag = "root"
        args.row_tag = "row"

        with pytest.raises(SystemExit) as e:
            run_csv2xml_lab_logic(args)

        assert e.value.code == 0

    @patch('sys.stderr', new_callable=MagicMock)
    def test_run_logic_missing_input(self, mock_stderr):
        args = MagicMock()
        args.file = None
        args.text = None
        args.output = None

        with patch('sys.stdin.isatty', return_value=True):
            with pytest.raises(SystemExit) as e:
                run_csv2xml_lab_logic(args)

            assert e.value.code == 1


@pytest.mark.asyncio
async def test_csv2xml_tui():
    pytest.importorskip("textual")
    from textual.app import App
    from shared.tui_csv2xml import Csv2XmlTab

    class Csv2XmlTestApp(App):
        def compose(self):
            yield Csv2XmlTab()

    app = Csv2XmlTestApp()
    async with app.run_test() as pilot:
        # Check initial rendering
        assert app.query_one("#csv2xml-input") is not None

        # Enter CSV
        input_area = app.query_one("#csv2xml-input")
        input_area.text = "name,score\nDave,100"

        # Trigger conversion
        await pilot.click("#btn-convert-csv2xml")
        await pilot.pause()

        output_area = app.query_one("#csv2xml-output")
        assert "<name>Dave</name>" in output_area.text

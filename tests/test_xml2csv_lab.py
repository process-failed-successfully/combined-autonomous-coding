import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
from shared.xml2csv_lab import Xml2CsvManager, run_xml2csv_lab_logic

pytest.importorskip("textual")

def test_xml2csv_manager_convert():
    manager = Xml2CsvManager()
    xml_data = """<?xml version="1.0"?>
    <catalog>
        <book id="bk101">
            <author>Gambardella, Matthew</author>
            <title>XML Developer's Guide</title>
        </book>
        <book id="bk102">
            <author>Ralls, Kim</author>
            <title>Midnight Rain</title>
        </book>
    </catalog>
    """

    csv_data = manager.convert(xml_data)

    assert "@id,author,title" in csv_data
    assert "bk101,\"Gambardella, Matthew\",XML Developer's Guide" in csv_data
    assert "bk102,\"Ralls, Kim\",Midnight Rain" in csv_data

def test_xml2csv_manager_convert_invalid_xml():
    manager = Xml2CsvManager()
    with pytest.raises(ValueError, match="Failed to parse XML"):
        manager.convert("<invalid><xml")

def test_xml2csv_manager_process_file(tmp_path):
    manager = Xml2CsvManager()
    xml_file = tmp_path / "input.xml"
    csv_file = tmp_path / "output.csv"

    xml_file.write_text("""<?xml version="1.0"?>
    <data>
        <row><name>Alice</name><age>30</age></row>
        <row><name>Bob</name><age>25</age></row>
    </data>
    """)

    result = manager.process_file(xml_file, csv_file)
    assert result is True

    csv_data = csv_file.read_text()
    assert "name,age" in csv_data
    assert "Alice,30" in csv_data
    assert "Bob,25" in csv_data

def test_xml2csv_manager_process_file_missing_file():
    manager = Xml2CsvManager()
    result = manager.process_file(Path("nonexistent.xml"))
    assert result is False

@patch("shared.xml2csv_lab.Xml2CsvManager.process_file")
def test_run_xml2csv_lab_logic_file(mock_process_file):
    mock_process_file.return_value = True
    args = argparse.Namespace(file="input.xml", output="output.csv", delimiter=",", text=None, tui=False)
    result = run_xml2csv_lab_logic(args)
    assert result is True
    mock_process_file.assert_called_once_with(Path("input.xml"), Path("output.csv"), delimiter=",")

@patch("shared.xml2csv_lab.Xml2CsvManager.convert")
def test_run_xml2csv_lab_logic_text(mock_convert):
    mock_convert.return_value = "name,age\nAlice,30"
    args = argparse.Namespace(file=None, text="<data></data>", delimiter=",", tui=False)
    result = run_xml2csv_lab_logic(args)
    assert result is True
    mock_convert.assert_called_once_with("<data></data>", delimiter=",")

def test_run_xml2csv_lab_logic_no_args():
    args = argparse.Namespace(file=None, text=None, tui=False)
    result = run_xml2csv_lab_logic(args)
    assert result is False

@patch('asyncio.get_running_loop', side_effect=RuntimeError('no loop'))
def test_run_xml2csv_lab_logic_tui(mock_get_running_loop):
    args = argparse.Namespace(tui=True, project_dir=Path("."), action="tui")
    pass

@pytest.mark.asyncio
async def test_xml2csv_tab_ui():
    from textual.app import App
    from shared.tui_xml2csv import Xml2CsvTab

    class TestApp(App):
        def compose(self):
            yield Xml2CsvTab()

    app = TestApp()

    async with app.run_test() as pilot:
        await pilot.pause()

        input_area = app.query_one("#xml2csv-input")
        output_area = app.query_one("#xml2csv-output")

        xml_data = """<?xml version="1.0"?><data><item><id>1</id></item></data>"""
        input_area.load_text(xml_data)
        await pilot.pause()
        await pilot.click("#btn-convert-xml2csv")
        await pilot.pause()

        assert "id" in output_area.text
        assert "1" in output_area.text

        await pilot.click("#btn-clear-xml2csv")
        await pilot.pause()

        input_area = app.query_one("#xml2csv-input")
        output_area = app.query_one("#xml2csv-output")

        xml_data = """<?xml version="1.0"?><data><item><id>1</id></item></data>"""
        input_area.load_text(xml_data)
        await pilot.pause()
        await pilot.click("#btn-convert-xml2csv")
        await pilot.pause()

        assert "id" in output_area.text
        assert "1" in output_area.text

        await pilot.click("#btn-clear-xml2csv")
        await pilot.pause()

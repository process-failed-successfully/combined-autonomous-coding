import pytest
import io
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.xml2csv_lab import Xml2CsvManager, run_xml2csv_lab_logic

def test_xml2csv_manager_convert_flat():
    xml = "<root><item><name>Alice</name><age>30</age></item><item><name>Bob</name><age>25</age></item></root>"
    manager = Xml2CsvManager()
    csv_result = manager.convert(xml)

    assert "age,name" in csv_result
    assert "30,Alice" in csv_result
    assert "25,Bob" in csv_result

def test_xml2csv_manager_convert_nested():
    xml = "<root><item><user><name>Alice</name></user><age>30</age></item></root>"
    manager = Xml2CsvManager()
    csv_result = manager.convert(xml)

    assert "item.age,item.user.name" in csv_result
    assert "30,Alice" in csv_result

def test_xml2csv_manager_convert_with_attributes():
    xml = '<root><item id="1"><name>Alice</name></item></root>'
    manager = Xml2CsvManager()
    csv_result = manager.convert(xml)

    assert "item.@attributes.id,item.name" in csv_result
    assert "1,Alice" in csv_result

def test_xml2csv_manager_empty():
    manager = Xml2CsvManager()
    assert manager.convert("") == ""
    assert manager.convert("   ") == ""

def test_xml2csv_manager_invalid_xml():
    manager = Xml2CsvManager()
    with pytest.raises(ValueError, match="XML Parse Error"):
        manager.convert("<root><unclosed></root>")

@patch("sys.stdout", new_callable=io.StringIO)
def test_run_xml2csv_lab_logic_text(mock_stdout):
    args = MagicMock()
    args.action = None
    args.tui = False
    args.text = "<root><item><name>Alice</name></item></root>"
    args.file = None
    args.output = None

    run_xml2csv_lab_logic(args)
    assert "name" in mock_stdout.getvalue()
    assert "Alice" in mock_stdout.getvalue()

def test_run_xml2csv_lab_logic_file(tmp_path):
    input_file = tmp_path / "input.xml"
    input_file.write_text("<root><item><name>Alice</name></item></root>")

    output_file = tmp_path / "output.csv"

    args = MagicMock()
    args.action = None
    args.tui = False
    args.text = None
    args.file = str(input_file)
    args.output = str(output_file)

    run_xml2csv_lab_logic(args)

    assert output_file.exists()
    content = output_file.read_text()
    assert "name" in content
    assert "Alice" in content

@pytest.mark.asyncio
async def test_tui_xml2csv_tab(tmp_path):
    pytest.importorskip("textual")
    from shared.tui import AgentTUI
    import sqlite3
    from shared.database import init_db

    # Initialize DB for TUI
    db_path = tmp_path / "test_agent_lab.db"
    init_db(db_path)

    app = AgentTUI(project_dir=tmp_path, start_tab="tab-xml2csv")
    async with app.run_test() as pilot:
        # Load valid XML
        xml_input = app.query_one("#input-xml")
        xml_input.load_text("<root><item><name>Test</name></item></root>")

        # Trigger conversion
        await pilot.click("#btn-convert-xml2csv")
        await pilot.pause()

        # Check output
        output_csv = app.query_one("#output-csv-xml2csv")
        assert "name" in output_csv.text
        assert "Test" in output_csv.text

        # Test error handling
        xml_input.load_text("<invalid>")
        await pilot.click("#btn-convert-xml2csv")
        await pilot.pause()
        assert "XML Parse Error" in output_csv.text

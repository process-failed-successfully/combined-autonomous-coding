import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip('textual')
pytest.importorskip('sqlalchemy')

from textual.app import App
from textual.widgets import TextArea
from shared.tui_xml2csv import Xml2CsvTab
from shared.tui import AgentTUI
from shared.database import init_db


@pytest.fixture
def app(tmp_path):
    init_db(tmp_path / "test.db")
    return AgentTUI(project_dir=tmp_path, start_tab="tab-xml2csv")


@pytest.mark.asyncio
async def test_xml2csv_tab_conversion(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Xml2CsvTab)

        # Get components
        input_area = tab.query_one("#xml2csv-input", TextArea)
        output_area = tab.query_one("#xml2csv-output", TextArea)

        # Set valid XML
        xml_text = "<r><row><col1>A</col1></row><row><col1>B</col1></row></r>"
        input_area.load_text(xml_text)

        # Click convert
        tab.on_convert()
        await pilot.pause()

        # Check output
        expected_csv = "col1\r\nA\r\nB"
        assert expected_csv.strip() in output_area.text.strip()


@pytest.mark.asyncio
async def test_xml2csv_tab_empty_input(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Xml2CsvTab)
        output_area = tab.query_one("#xml2csv-output", TextArea)

        # Click convert with empty input
        tab.on_convert()
        await pilot.pause()

        assert "Error: Input is empty." in output_area.text


@pytest.mark.asyncio
async def test_xml2csv_tab_unexpected_error(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Xml2CsvTab)
        input_area = tab.query_one("#xml2csv-input", TextArea)
        output_area = tab.query_one("#xml2csv-output", TextArea)

        input_area.load_text("<xml></xml>")

        with patch("shared.xml2csv_lab.Xml2CsvManager.convert_xml_to_csv", side_effect=Exception("Unexpected")):
            tab.on_convert()
            await pilot.pause()

        assert "An unexpected error occurred" in output_area.text


@pytest.mark.asyncio
async def test_xml2csv_tab_invalid_xml(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Xml2CsvTab)
        input_area = tab.query_one("#xml2csv-input", TextArea)
        output_area = tab.query_one("#xml2csv-output", TextArea)

        # Set invalid XML
        input_area.load_text("<invalid><<")

        tab.on_convert()
        await pilot.pause()

        assert "Invalid XML" in output_area.text

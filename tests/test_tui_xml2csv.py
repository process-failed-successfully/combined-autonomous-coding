import pytest
from textual.app import App
from shared.tui_xml2csv import Xml2CsvTab
from unittest.mock import MagicMock, patch


class DummyApp(App):
    def compose(self):
        yield Xml2CsvTab()


@pytest.mark.asyncio
async def test_xml2csv_tab_conversion():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Get components
        input_area = app.query_one("#xml2csv-input")
        output_area = app.query_one("#xml2csv-output")

        # Set valid XML
        xml_text = "<r><row><col1>A</col1></row><row><col1>B</col1></row></r>"
        input_area.load_text(xml_text)

        # Click convert
        await pilot.click("#btn-convert-xml2csv")
        await pilot.pause()

        # Check output
        expected_csv = "col1\r\nA\r\nB"
        assert output_area.text.strip() == expected_csv.strip()


@pytest.mark.asyncio
async def test_xml2csv_tab_empty_input():
    app = DummyApp()
    async with app.run_test() as pilot:
        output_area = app.query_one("#xml2csv-output")

        # Click convert with empty input
        await pilot.click("#btn-convert-xml2csv")
        await pilot.pause()

        assert "Error: Input is empty." in output_area.text


@pytest.mark.asyncio
async def test_xml2csv_tab_unexpected_error():
    app = DummyApp()
    async with app.run_test() as pilot:
        input_area = app.query_one("#xml2csv-input")
        output_area = app.query_one("#xml2csv-output")

        input_area.load_text("<xml></xml>")

        with patch("shared.xml2csv_lab.Xml2CsvManager.convert_xml_to_csv", side_effect=Exception("Unexpected")):
            await pilot.click("#btn-convert-xml2csv")
            await pilot.pause()

        assert "An unexpected error occurred" in output_area.text

@pytest.mark.asyncio
async def test_xml2csv_tab_invalid_xml():
    app = DummyApp()
    async with app.run_test() as pilot:
        input_area = app.query_one("#xml2csv-input")
        output_area = app.query_one("#xml2csv-output")

        # Set invalid XML
        input_area.load_text("<invalid><<")

        await pilot.click("#btn-convert-xml2csv")
        await pilot.pause()

        assert "Invalid XML" in output_area.text

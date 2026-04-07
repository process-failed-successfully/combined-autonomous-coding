import pytest
from textual.app import App
from shared.tui_md2csv import Md2CsvTab
from textual.widgets import TextArea, Input, Button

@pytest.fixture
def tui_app():
    class TestApp(App):
        def compose(self):
            yield Md2CsvTab()
    return TestApp()

@pytest.mark.asyncio
async def test_md2csv_tab_initial_conversion(tui_app):
    async with tui_app.run_test() as pilot:
        # Initially, the text area has the default Markdown content
        # It should trigger do_conversion on mount
        await pilot.pause()

        result_area = tui_app.query_one("#md2csv-result-textarea", TextArea)
        assert result_area.text.replace("\r\n", "\n") == "Header 1,Header 2\nData 1,Data 2\n"

@pytest.mark.asyncio
async def test_md2csv_tab_conversion_on_change(tui_app):
    async with tui_app.run_test() as pilot:
        await pilot.pause()

        # Change input text
        input_area = tui_app.query_one("#md2csv-textarea", TextArea)
        input_area.text = "| ID | Status |\n|---|---|\n| 1 | Active |"
        await pilot.pause()

        result_area = tui_app.query_one("#md2csv-result-textarea", TextArea)
        assert result_area.text.replace("\r\n", "\n") == "ID,Status\n1,Active\n"

@pytest.mark.asyncio
async def test_md2csv_tab_custom_delimiter(tui_app):
    async with tui_app.run_test() as pilot:
        await pilot.pause()

        input_area = tui_app.query_one("#md2csv-textarea", TextArea)
        input_area.text = "| ID | Status |\n|---|---|\n| 1 | Active |"
        await pilot.pause()

        # Change delimiter
        delim_input = tui_app.query_one("#md2csv-delimiter", Input)
        delim_input.value = ";"
        await pilot.pause()

        result_area = tui_app.query_one("#md2csv-result-textarea", TextArea)
        assert result_area.text.replace("\r\n", "\n") == "ID;Status\n1;Active\n"

@pytest.mark.asyncio
async def test_md2csv_tab_empty_input(tui_app):
    async with tui_app.run_test() as pilot:
        await pilot.pause()

        # Change input text
        input_area = tui_app.query_one("#md2csv-textarea", TextArea)
        input_area.text = ""
        await pilot.pause()

        result_area = tui_app.query_one("#md2csv-result-textarea", TextArea)
        assert result_area.text == ""

@pytest.mark.asyncio
async def test_md2csv_tab_button_convert(tui_app):
    async with tui_app.run_test() as pilot:
        await pilot.pause()

        # Change input without triggering events if possible, or just change it and press button
        input_area = tui_app.query_one("#md2csv-textarea", TextArea)
        input_area.text = "| X | Y |\n|---|---|\n| a | b |"
        await pilot.pause()

        # Trigger conversion manually via button
        tui_app.query_one("#btn-md2csv-convert", Button).press()
        await pilot.pause()

        result_area = tui_app.query_one("#md2csv-result-textarea", TextArea)
        assert result_area.text.replace("\r\n", "\n") == "X,Y\na,b\n"

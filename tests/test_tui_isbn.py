import pytest
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Input, Button, Label, Select
from shared.tui_isbn import IsbnLabTab

class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield IsbnLabTab()

@pytest.mark.asyncio
async def test_tui_isbn_validate_valid():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Setup inputs
        input_widget = app.query_one("#isbn-validate-input", Input)
        input_widget.value = "0-306-40615-2"

        # Trigger button
        app.query_one("#btn-isbn-validate", Button).press()
        await pilot.pause(0.1)

        # Assert output
        output_label = app.query_one("#isbn-validate-output", Label)
        assert "is a valid ISBN" in str(output_label.renderable) if hasattr(output_label, "renderable") else "is a valid ISBN" in str(output_label.render())

@pytest.mark.asyncio
async def test_tui_isbn_validate_invalid():
    app = DummyApp()
    async with app.run_test(size=(80, 200)) as pilot:
        input_widget = app.query_one("#isbn-validate-input", Input)
        input_widget.value = "invalid-123"

        app.query_one("#btn-isbn-validate", Button).press()
        await pilot.pause(0.1)

        output_label = app.query_one("#isbn-validate-output", Label)
        assert "is INVALID" in str(output_label.renderable) if hasattr(output_label, "renderable") else "is INVALID" in str(output_label.render())

@pytest.mark.asyncio
async def test_tui_isbn_generate():
    app = DummyApp()
    async with app.run_test(size=(80, 200)) as pilot:
        format_select = app.query_one("#isbn-generate-format", Select)
        prefix_input = app.query_one("#isbn-generate-prefix", Input)

        # Test 13
        format_select.value = "13"
        prefix_input.value = "978"

        app.query_one("#btn-isbn-generate", Button).press()
        await pilot.pause(0.1)

        output_label = app.query_one("#isbn-generate-output", Label)
        output_str = str(output_label.renderable) if hasattr(output_label, "renderable") else str(output_label.render())
        assert "Generated ISBN-13:" in output_str
        assert "978" in output_str

@pytest.mark.asyncio
async def test_tui_isbn_parse():
    app = DummyApp()
    async with app.run_test(size=(80, 200)) as pilot:
        input_widget = app.query_one("#isbn-parse-input", Input)
        input_widget.value = "978-0-306-40615-7"

        app.query_one("#btn-isbn-parse", Button).press()
        await pilot.pause(0.1)

        output_label = app.query_one("#isbn-parse-output", Label)
        output_str = str(output_label.renderable) if hasattr(output_label, "renderable") else str(output_label.render())
        assert "Format: ISBN-13" in output_str
        assert "Prefix: 978" in output_str
        assert "Checksum: 7" in output_str
        assert "Valid:" in output_str

@pytest.mark.asyncio
async def test_tui_isbn_convert():
    app = DummyApp()
    async with app.run_test(size=(80, 200)) as pilot:
        input_widget = app.query_one("#isbn-convert-input", Input)
        input_widget.value = "0-306-40615-2"

        app.query_one("#btn-isbn-convert", Button).press()
        await pilot.pause(0.1)

        output_label = app.query_one("#isbn-convert-output", Label)
        assert "Converted to ISBN-13: 9780306406157" in str(output_label.renderable) if hasattr(output_label, "renderable") else "Converted to ISBN-13: 9780306406157" in str(output_label.render())

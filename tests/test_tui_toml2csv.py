import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import textual inside test to skip gracefully if not installed
pytest.importorskip("textual")
from textual.app import App
from shared.tui_toml2csv import Toml2CsvLabTab
from shared.database import init_db

class Toml2CsvTestApp(App):
    def compose(self):
        yield Toml2CsvLabTab()

@pytest.mark.asyncio
async def test_toml2csv_tui_convert_success(tmp_path):
    # Initialize a temporary database for TUI components that might require it implicitly
    db_path = tmp_path / "test.db"
    init_db(db_path)

    app = Toml2CsvTestApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        # Set input TOML
        input_ta = app.query_one("#toml2csv-input-ta")
        input_ta.load_text('''
[[items]]
name = "Test"
''')

        # Verify output is empty
        output_ta = app.query_one("#toml2csv-output-ta")
        assert output_ta.text == ""

        # Trigger conversion
        app.query_one("#toml2csv-convert-btn").press()
        await pilot.pause()

        # Check output and status
        assert "Test" in output_ta.text

        status = app.query_one("#toml2csv-status")
        assert "Conversion successful." in str(status.renderable)

@pytest.mark.asyncio
async def test_toml2csv_tui_convert_empty(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    app = Toml2CsvTestApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        input_ta = app.query_one("#toml2csv-input-ta")
        input_ta.load_text("")

        app.query_one("#toml2csv-convert-btn").press()
        await pilot.pause()

        output_ta = app.query_one("#toml2csv-output-ta")
        assert output_ta.text == ""

        status = app.query_one("#toml2csv-status")
        assert "Input is empty." in str(status.renderable)

@pytest.mark.asyncio
async def test_toml2csv_tui_convert_error(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    app = Toml2CsvTestApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        input_ta = app.query_one("#toml2csv-input-ta")
        input_ta.load_text("invalid toml { ")

        app.query_one("#toml2csv-convert-btn").press()
        await pilot.pause()

        output_ta = app.query_one("#toml2csv-output-ta")
        assert output_ta.text == ""

        status = app.query_one("#toml2csv-status")
        assert "Error:" in str(status.renderable)

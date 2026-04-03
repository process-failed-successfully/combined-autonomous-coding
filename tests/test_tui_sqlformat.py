import pytest
from unittest.mock import patch

pytest.importorskip("textual")
from textual.app import App, ComposeResult  # noqa: E402
from textual.widgets import TextArea, Button  # noqa: E402

from shared.tui_sqlformat import TabSqlFormat  # noqa: E402


class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield TabSqlFormat()


@pytest.mark.asyncio
async def test_tui_sqlformat_basic():
    app = DummyApp()
    async with app.run_test(size=(80, 24)) as pilot:
        # Give textual time to mount
        await pilot.pause()

        input_area = app.query_one("#input-sql", TextArea)
        output_area = app.query_one("#output-sql", TextArea)

        # Set some raw SQL
        input_area.load_text("select * from users where id=1")

        # Trigger formatting
        app.query_one("#btn-format", Button).press()
        await pilot.pause()

        formatted = output_area.text
        assert "SELECT" in formatted
        assert "FROM" in formatted
        assert "users" in formatted


@pytest.mark.asyncio
async def test_tui_sqlformat_empty():
    app = DummyApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()

        input_area = app.query_one("#input-sql", TextArea)
        output_area = app.query_one("#output-sql", TextArea)

        # Ensure empty input
        input_area.load_text("   \n   ")

        # Output should be some placeholder or previous value, but we press btn
        app.query_one("#btn-format", Button).press()
        await pilot.pause()

        assert output_area.text == ""


@pytest.mark.asyncio
@patch("shared.tui_sqlformat.sqlparse.format")
async def test_tui_sqlformat_error(mock_format):
    mock_format.side_effect = Exception("Parse error!")

    app = DummyApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()

        input_area = app.query_one("#input-sql", TextArea)
        output_area = app.query_one("#output-sql", TextArea)

        input_area.load_text("select oops")

        app.query_one("#btn-format", Button).press()
        await pilot.pause()

        assert "Error formatting SQL" in output_area.text
        assert "Parse error!" in output_area.text

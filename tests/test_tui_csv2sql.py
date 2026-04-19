import pytest
from unittest.mock import patch

try:
    from textual.app import App
    from textual.widgets import Input, TextArea, TabbedContent
    from shared.tui_csv2sql import Csv2SqlTab
except ImportError:
    pass

pytest.importorskip('textual')


class DummyApp(App):
    def compose(self):
        with TabbedContent():
            yield Csv2SqlTab()

@pytest.fixture
def app():
    return DummyApp()


@pytest.mark.asyncio
async def test_csv2sqltab_renders(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Csv2SqlTab)
        assert tab is not None
        assert tab.query_one("#csv2sql-table-input") is not None
        assert tab.query_one("#csv2sql-input") is not None
        assert tab.query_one("#csv2sql-output") is not None


@pytest.mark.asyncio
async def test_csv2sqltab_conversion_action(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Csv2SqlTab)

        # Access widgets directly
        csv_input = tab.query_one("#csv2sql-input", TextArea)
        table_input = tab.query_one("#csv2sql-table-input", Input)

        # Use text assignment
        csv_input.text = "id,name\n1,Alice\n2,Bob"
        table_input.value = "users_table"

        tab.convert_csv()
        await pilot.pause()

        sql_output = tab.query_one("#csv2sql-output", TextArea)
        assert "INSERT INTO users_table (id, name) VALUES ('1', 'Alice');" in sql_output.text
        assert "INSERT INTO users_table (id, name) VALUES ('2', 'Bob');" in sql_output.text


@pytest.mark.asyncio
async def test_csv2sqltab_clear_action(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Csv2SqlTab)

        csv_input = tab.query_one("#csv2sql-input", TextArea)
        sql_output = tab.query_one("#csv2sql-output", TextArea)

        csv_input.text = "id,name\n1,Alice"
        tab.convert_csv()
        await pilot.pause()
        assert "INSERT" in sql_output.text

        tab.clear_inputs()
        await pilot.pause()
        assert csv_input.text == ""
        assert sql_output.text == ""


@pytest.mark.asyncio
async def test_csv2sqltab_error_handling(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Csv2SqlTab)

        csv_input = tab.query_one("#csv2sql-input", TextArea)
        csv_input.text = "id,name\n1,Alice"

        with patch('shared.csv2sql_lab.Csv2SqlManager.convert', side_effect=Exception("Mock TUI Error")):
            tab.convert_csv()
            await pilot.pause()
            sql_output = tab.query_one("#csv2sql-output", TextArea)
            assert "Error: Mock TUI Error" in sql_output.text

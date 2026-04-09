import pytest
from unittest.mock import patch

try:
    from textual.widgets import Input, TextArea
    from shared.database import init_db
    from shared.tui_csv2sql import Csv2SqlTab
    from shared.tui import AgentTUI
except ImportError:
    pass

pytest.importorskip('textual')


@pytest.fixture
def app(tmp_path):
    init_db(tmp_path / "test.db")
    return AgentTUI(project_dir=tmp_path, start_tab="tab-csv2sql")


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

        # Use load_text for TextArea
        csv_input.load_text("id,name\n1,Alice\n2,Bob")
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

        csv_input.load_text("id,name\n1,Alice")
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
        csv_input.load_text("id,name\n1,Alice")

        with patch('shared.csv2sql_lab.Csv2SqlManager.convert', side_effect=Exception("Mock TUI Error")):
            tab.convert_csv()
            await pilot.pause()
            sql_output = tab.query_one("#csv2sql-output", TextArea)
            assert "Error: Mock TUI Error" in sql_output.text

import pytest
from unittest.mock import patch

pytest.importorskip('textual')

from textual.widgets import Input, TextArea
from shared.database import init_db
from shared.tui_json2sql import Json2SqlTab
from shared.tui import AgentTUI


@pytest.fixture
def app(tmp_path):
    init_db(tmp_path / "test.db")
    return AgentTUI(project_dir=tmp_path, start_tab="tab-json2sql")


@pytest.mark.asyncio
async def test_json2sqltab_renders(app):
    async with app.run_test(size=(100, 100)):
        tab = app.query_one(Json2SqlTab)
        assert tab is not None
        assert tab.query_one("#json2sql_table_input") is not None
        assert tab.query_one("#json2sql_input") is not None
        assert tab.query_one("#json2sql_output") is not None


@pytest.mark.asyncio
async def test_json2sqltab_conversion_action(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Json2SqlTab)

        # Access widgets directly
        json_input = tab.query_one("#json2sql_input", TextArea)
        table_input = tab.query_one("#json2sql_table_input", Input)

        # Use load_text for TextArea
        json_input.load_text('[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]')
        table_input.value = "users_table"

        tab.query_one("#btn_convert_json2sql").press()
        await pilot.pause()

        sql_output = tab.query_one("#json2sql_output", TextArea)
        assert "INSERT INTO users_table (id, name) VALUES ('1', 'Alice');" in sql_output.text
        assert "INSERT INTO users_table (id, name) VALUES ('2', 'Bob');" in sql_output.text


@pytest.mark.asyncio
async def test_json2sqltab_clear_action(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Json2SqlTab)

        json_input = tab.query_one("#json2sql_input", TextArea)
        sql_output = tab.query_one("#json2sql_output", TextArea)

        json_input.load_text('[{"id": 1, "name": "Alice"}]')
        tab.query_one("#btn_convert_json2sql").press()
        await pilot.pause()
        assert "INSERT" in sql_output.text

        tab.query_one("#btn_clear_json2sql").press()
        await pilot.pause()
        assert json_input.text == ""
        assert sql_output.text == ""


@pytest.mark.asyncio
async def test_json2sqltab_error_handling(app):
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(Json2SqlTab)

        json_input = tab.query_one("#json2sql_input", TextArea)
        json_input.load_text('invalid json')

        tab.query_one("#btn_convert_json2sql").press()
        await pilot.pause()
        sql_output = tab.query_one("#json2sql_output", TextArea)
        assert "Error: Invalid JSON string:" in sql_output.text

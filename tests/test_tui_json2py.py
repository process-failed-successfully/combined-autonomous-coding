import pytest
from textual.app import App
from shared.tui_json2py import Json2PyLabTab
import pytest_asyncio

from textual.widgets import TabbedContent

class Json2PyTestApp(App):
    def compose(self):
        with TabbedContent():
            yield Json2PyLabTab()

@pytest.mark.asyncio
async def test_json2py_tab_generate():
    app = Json2PyTestApp()
    async with app.run_test() as pilot:
        # Set input json
        tab = pilot.app.query_one(Json2PyLabTab)
        in_editor = tab.query_one("#editor-json2py-in")
        in_editor.text = '{"name": "test", "age": 30}'

        # Set root name
        root_input = tab.query_one("#input-json2py-root")
        root_input.value = "TestUser"

        # Click generate
        from textual.widgets import Button
        btn = tab.query_one("#btn-generate-json2py", Button)
        btn.press()
        await pilot.pause()

        # Check output
        out_editor = tab.query_one("#editor-json2py-out")
        assert "class TestUser:" in out_editor.text
        assert "name: Optional[str] = None" in out_editor.text
        assert "age: Optional[int] = None" in out_editor.text

@pytest.mark.asyncio
async def test_json2py_tab_generate_pydantic():
    app = Json2PyTestApp()
    async with app.run_test() as pilot:
        tab = pilot.app.query_one(Json2PyLabTab)
        in_editor = tab.query_one("#editor-json2py-in")
        in_editor.text = '{"name": "test", "age": 30}'

        # Select pydantic
        select = tab.query_one("#select-json2py-framework")
        select.value = "pydantic"

        # Click generate
        from textual.widgets import Button
        btn = tab.query_one("#btn-generate-json2py", Button)
        btn.press()
        await pilot.pause()

        # Check output
        out_editor = tab.query_one("#editor-json2py-out")
        assert "class RootModel(BaseModel):" in out_editor.text

@pytest.mark.asyncio
async def test_json2py_tab_empty_input():
    app = Json2PyTestApp()
    async with app.run_test() as pilot:
        # Click generate with empty input
        from textual.widgets import Button
        tab = pilot.app.query_one(Json2PyLabTab)
        btn = tab.query_one("#btn-generate-json2py", Button)
        btn.press()
        await pilot.pause()

        # The output shouldn't change
        tab = pilot.app.query_one(Json2PyLabTab)
        out_editor = tab.query_one("#editor-json2py-out")
        assert out_editor.text == ""

@pytest.mark.asyncio
async def test_json2py_tab_copy():
    app = Json2PyTestApp()
    async with app.run_test() as pilot:
        tab = pilot.app.query_one(Json2PyLabTab)
        out_editor = tab.query_one("#editor-json2py-out")
        out_editor.text = "test output"

        from textual.widgets import Button
        btn = tab.query_one("#btn-copy-json2py", Button)
        btn.press()
        await pilot.pause()

@pytest.mark.asyncio
async def test_json2py_tab_invalid_json():
    app = Json2PyTestApp()
    async with app.run_test() as pilot:
        tab = pilot.app.query_one(Json2PyLabTab)
        in_editor = tab.query_one("#editor-json2py-in")
        in_editor.text = '{"name": "test", ' # invalid json

        from textual.widgets import Button
        btn = tab.query_one("#btn-generate-json2py", Button)
        btn.press()
        await pilot.pause()

        out_editor = tab.query_one("#editor-json2py-out")
        assert "Error generating code:" in out_editor.text

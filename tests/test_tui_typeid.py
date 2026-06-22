import pytest
import asyncio
from textual.widgets import Input, Static, RichLog, Button
from shared.tui_typeid import TypeIDLabTab
from textual.app import App, ComposeResult
from typing import Any
from shared.typeid_lab import HAS_TYPEID

pytestmark = pytest.mark.skipif(not HAS_TYPEID, reason="typeid-python library not installed")

class TypeIDLabApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield TypeIDLabTab()

@pytest.mark.asyncio
async def test_typeid_tab_generate():
    app = TypeIDLabApp()
    async with app.run_test() as pilot:
        tab = app.query_one(TypeIDLabTab)

        prefix_input = app.query_one("#typeid-prefix", Input)
        count_input = app.query_one("#typeid-count", Input)
        output = app.query_one("#typeid-gen-output", Static)

        prefix_input.value = "test"
        count_input.value = "2"

        await pilot.click("#btn-typeid-generate")
        await pilot.pause()

        out_text = output.render()
        assert "Generated TypeID(s):" in str(out_text)
        assert "test_" in str(out_text)

@pytest.mark.asyncio
async def test_typeid_tab_parse():
    app = TypeIDLabApp()
    async with app.run_test() as pilot:
        tab = app.query_one(TypeIDLabTab)

        # Need a valid TypeID first
        from shared.typeid_lab import TypeIDLabManager
        manager = TypeIDLabManager()
        valid_tid = manager.generate(prefix="org")[0]

        parse_input = app.query_one("#typeid-parse-input", Input)
        result_log = app.query_one("#typeid-parse-result", RichLog)

        parse_input.value = valid_tid

        await pilot.click("#btn-typeid-parse")
        await pilot.pause()

        lines = list(result_log.lines)
        assert len(lines) > 0
        joined_lines = "".join(str(line) for line in lines)
        assert "Valid TypeID" in joined_lines
        assert "org" in joined_lines

import pytest
from textual.app import App, ComposeResult
from textual.widgets import TabbedContent
from unittest.mock import patch, MagicMock

pytest.importorskip('textual')

def test_json2ts_lab_tab_mount():
    from shared.tui_json2ts import Json2TsLabTab

    class Json2TsApp(App):
        def compose(self) -> ComposeResult:
            with TabbedContent():
                yield Json2TsLabTab()

    app = Json2TsApp()

    async def run_test():
        async with app.run_test() as pilot:
            tab = app.query_one(Json2TsLabTab)
            assert tab is not None
            assert tab.id == "tab-json2ts"

            in_editor = app.query_one("#editor-json2ts-in")
            out_editor = app.query_one("#editor-json2ts-out")
            btn_generate = app.query_one("#btn-generate-json2ts")

            # Input valid JSON
            in_editor.text = '{"name": "Alice"}'

            # Click generate
            # Need to call actual event handler
            event = MagicMock()
            event.button.id = "btn-generate-json2ts"
            await tab.on_button_pressed(event)
            await pilot.pause()

            # Check output
            assert "export interface RootInterface" in out_editor.text
            assert "name: string;" in out_editor.text

    import asyncio
    asyncio.run(run_test())

def test_json2ts_lab_cli_logic():
    from shared.json2ts_lab import run_json2ts_lab_logic

    args = MagicMock()
    args.file = None
    args.text = '{"key": "value"}'
    args.name = "MyIntf"
    args.output = None

    with patch("sys.stdout", new_callable=MagicMock) as mock_stdout:
        success = run_json2ts_lab_logic(args)
        assert success is True

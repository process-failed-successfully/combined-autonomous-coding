import pytest

from textual.app import App, ComposeResult
from shared.tui_msgpack import MsgpackLabTab


class MsgpackApp(App):
    def compose(self) -> ComposeResult:
        yield MsgpackLabTab()


@pytest.mark.asyncio
async def test_msgpack_lab_tui_encode():
    app = MsgpackApp()
    async with app.run_test() as pilot:
        json_area = app.query_one("#msgpack-json-area")
        b64_area = app.query_one("#msgpack-b64-area")

        json_area.text = '{"test": 123}'
        pilot.app.query_one("#btn-msgpack-encode").press()
        await pilot.pause()
        assert b64_area.text == "gaR0ZXN0ew=="


@pytest.mark.asyncio
async def test_msgpack_lab_tui_decode():
    app = MsgpackApp()
    async with app.run_test() as pilot:
        json_area = app.query_one("#msgpack-json-area")
        b64_area = app.query_one("#msgpack-b64-area")

        b64_area.text = "gaR0ZXN0ew=="
        pilot.app.query_one("#btn-msgpack-decode").press()
        await pilot.pause()
        assert '"test": 123' in json_area.text


@pytest.mark.asyncio
async def test_msgpack_lab_tui_clear():
    app = MsgpackApp()
    async with app.run_test() as pilot:
        json_area = app.query_one("#msgpack-json-area")
        b64_area = app.query_one("#msgpack-b64-area")

        json_area.text = "data"
        b64_area.text = "data"

        pilot.app.query_one("#btn-msgpack-clear").press()
        await pilot.pause()

        assert json_area.text == ""
        assert b64_area.text == ""

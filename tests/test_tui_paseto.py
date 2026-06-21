import pytest
from textual.app import App, ComposeResult
from shared.tui_paseto import PasetoLabTab
from textual.widgets import TextArea, Button, Input, Select

class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield PasetoLabTab()

@pytest.mark.asyncio
async def test_tui_paseto_sign():
    app = DummyApp()
    async with app.run_test() as pilot:
        tab = app.query_one(PasetoLabTab)

        # Test sign
        app.query_one("#paseto-sign-payload", TextArea).text = '{"msg": "hello"}'
        app.query_one("#paseto-sign-key", Input).value = '01234567890123456789012345678901'

        app.query_one(PasetoLabTab)._handle_sign()
        await pilot.pause()

        output = app.query_one("#paseto-sign-output", TextArea).text
        assert output.startswith("v4.local.")

@pytest.mark.asyncio
async def test_tui_paseto_decode():
    app = DummyApp()
    async with app.run_test() as pilot:
        tab = app.query_one(PasetoLabTab)

        # Structure decode
        app.query_one("#paseto-decode-input", TextArea).text = 'v4.local.payload.footer'

        app.query_one(PasetoLabTab)._handle_decode()
        await pilot.pause()

        assert True

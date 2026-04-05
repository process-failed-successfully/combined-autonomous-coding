import pytest
from textual.widgets import Input, Button, Static
from shared.tui_nanoid import NanoIDLab

@pytest.mark.asyncio
async def test_nanoid_tui():
    app = NanoIDLab()
    from textual.app import App

    class DummyApp(App):
        def compose(self):
            yield app

    test_app = DummyApp()
    async with test_app.run_test() as pilot:
        size_input = test_app.query_one("#nanoid-size-input", Input)
        size_input.value = "15"

        count_input = test_app.query_one("#nanoid-count-input", Input)
        count_input.value = "2"

        alphabet_input = test_app.query_one("#nanoid-alphabet-input", Input)
        alphabet_input.value = "a"

        btn = test_app.query_one("#btn-generate-nanoid", Button)
        app.query_one("#btn-generate-nanoid").press()
        await pilot.pause()
        await pilot.pause(0.2)

        output = test_app.query_one("#nanoid-output", Static)
        assert len(str(output.render()).split("\n")) == 2
        assert "a" * 15 in str(output.render())

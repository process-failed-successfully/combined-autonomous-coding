import pytest
from textual.app import App
from shared.tui_hashids import HashidsLabTab
from textual.widgets import Input, Button, Static
from shared.hashids_lab import HAS_HASHIDS

pytestmark = pytest.mark.skipif(not HAS_HASHIDS, reason="hashids library not installed")

class DummyApp(App):
    def compose(self):
        yield HashidsLabTab()

@pytest.mark.asyncio
async def test_hashids_encode():
    app = DummyApp()
    async with app.run_test() as pilot:
        await pilot.pause(0.1)

        salt_input = app.query_one("#hashids-salt", Input)
        salt_input.value = "my salt"

        numbers_input = app.query_one("#hashids-numbers", Input)
        numbers_input.value = "1 2 3"

        pilot.app.query_one("#btn-hashids-encode").press()
        await pilot.pause()

        output = app.query_one("#hashids-output", Static)
        assert "Encoded:" in str(output.render())

@pytest.mark.asyncio
async def test_hashids_decode():
    app = DummyApp()
    async with app.run_test() as pilot:
        await pilot.pause(0.1)

        salt_input = app.query_one("#hashids-salt", Input)
        salt_input.value = "my salt"

        hash_input = app.query_one("#hashids-hash", Input)
        hash_input.value = "1dSoHw"

        pilot.app.query_one("#btn-hashids-decode").press()
        await pilot.pause()

        output = app.query_one("#hashids-output", Static)
        # It should decode back to "1 2 3"
        assert "Decoded:" in str(output.render())
        assert "1 2 3" in str(output.render())

@pytest.mark.asyncio
async def test_hashids_invalid_numbers():
    app = DummyApp()
    async with app.run_test() as pilot:
        await pilot.pause(0.1)

        numbers_input = app.query_one("#hashids-numbers", Input)
        numbers_input.value = "abc 2 3"

        pilot.app.query_one("#btn-hashids-encode").press()
        await pilot.pause()

        output = app.query_one("#hashids-output", Static)
        assert "must be space-separated integers" in str(output.render())

@pytest.mark.asyncio
async def test_hashids_decode_invalid():
    app = DummyApp()
    async with app.run_test() as pilot:
        await pilot.pause(0.1)

        hash_input = app.query_one("#hashids-hash", Input)
        hash_input.value = "invalid_hash!"

        pilot.app.query_one("#btn-hashids-decode").press()
        await pilot.pause()

        output = app.query_one("#hashids-output", Static)
        assert "Could not decode" in str(output.render())

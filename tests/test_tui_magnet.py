import unittest
from unittest.mock import patch, MagicMock
import pytest
from textual.app import App
from shared.tui_magnet import MagnetLabTab

class MagnetLabApp(App):
    def compose(self):
        yield MagnetLabTab()

@pytest.mark.asyncio
async def test_magnet_tui_parse():
    app = MagnetLabApp()
    async with app.run_test(size=(100, 100)) as pilot:
        # Get elements
        input_parse = app.query_one("#input-parse-uri")
        btn_parse = app.query_one("#btn-parse")
        output = app.query_one("#magnet-output")

        # Set valid URI
        input_parse.value = "magnet:?xt=urn:btih:b415c913643e5ff49fe37d304bbb5e6e11ad5101&dn=ubuntu.iso"

        # Click
        await pilot.click("#btn-parse")

        # Verify
        assert "ubuntu.iso" in output.text
        assert "urn:btih:b415c913643e5ff49fe37d304bbb5e6e11ad5101" in output.text

@pytest.mark.asyncio
async def test_magnet_tui_build():
    app = MagnetLabApp()
    async with app.run_test(size=(100, 100)) as pilot:
        # Get elements
        input_hash = app.query_one("#input-build-hash")
        input_name = app.query_one("#input-build-name")
        output = app.query_one("#magnet-output")

        # Set input
        input_hash.value = "b415c913643e5ff49fe37d304bbb5e6e11ad5101"
        input_name.value = "ubuntu.iso"

        # Click
        await pilot.click("#btn-build")

        # Verify
        assert "magnet:?xt=urn:btih:b415c913643e5ff49fe37d304bbb5e6e11ad5101" in output.text
        assert "dn=ubuntu.iso" in output.text

@pytest.mark.asyncio
async def test_magnet_tui_from_torrent():
    app = MagnetLabApp()
    async with app.run_test(size=(100, 100)) as pilot:
        with patch('shared.magnet_lab.MagnetLabManager.from_torrent', return_value={"success": True, "uri": "magnet:?xt=urn:btih:mocked"}):
            # Get elements
            input_torrent = app.query_one("#input-torrent-path")
            output = app.query_one("#magnet-output")

            # Set input
            input_torrent.value = "dummy.torrent"

            # Click
            await pilot.click("#btn-torrent")

            # Verify
            assert "magnet:?xt=urn:btih:mocked" in output.text

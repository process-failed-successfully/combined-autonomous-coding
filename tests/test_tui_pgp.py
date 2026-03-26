import pytest
from textual.app import App
from textual.widgets import Input, TextArea, DataTable
from shared.tui_pgp import PGPLabTab
from typing import Any
import tempfile
import os

class DummyApp(App[Any]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gnupg_home = tempfile.TemporaryDirectory()

    def compose(self):
        tab = PGPLabTab()
        tab.manager.gpg.gnupghome = self.gnupg_home.name
        yield tab

@pytest.mark.asyncio
async def test_tui_pgp_render():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Check that UI elements render
        assert app.query_one("#pgp-gen-name", Input) is not None
        assert app.query_one("#pgp-gen-email", Input) is not None
        assert app.query_one("#pgp-gen-passphrase", Input) is not None
        assert app.query_one("#pgp-keys-table", DataTable) is not None
        assert app.query_one("#pgp-crypto-input", TextArea) is not None
        assert app.query_one("#pgp-sign-input", TextArea) is not None

@pytest.mark.asyncio
async def test_tui_pgp_generate_key():
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        # Generate a small key to save time
        app.query_one("#pgp-gen-name", Input).value = "Test User"
        app.query_one("#pgp-gen-email", Input).value = "test@example.com"
        app.query_one("#pgp-gen-passphrase", Input).value = "secret"

        # The actual generation is slow, so we can't easily wait for it without mocking
        # Just click the button to ensure it doesn't crash
        app.query_one("#pgp-gen-btn").press()
        await pilot.pause(0.1)

@pytest.mark.asyncio
async def test_tui_pgp_encrypt():
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        app.query_one("#pgp-crypto-input", TextArea).text = "Secret Data"
        app.query_one("#pgp-encrypt-recipients", Input).value = "test@example.com"
        app.query_one("#pgp-encrypt-btn").press()
        await pilot.pause(0.1)
        # Without a valid key, encryption should fail and show an error notification

@pytest.mark.asyncio
async def test_tui_pgp_sign():
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        app.query_one("#pgp-sign-input", TextArea).text = "Data to sign"
        app.query_one("#pgp-sign-keyid", Input).value = "test@example.com"
        app.query_one("#pgp-sign-passphrase", Input).value = "secret"
        app.query_one("#pgp-sign-btn").press()
        await pilot.pause(0.1)

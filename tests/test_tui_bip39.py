import unittest
import pytest
from unittest.mock import patch
from textual.app import App, ComposeResult
from shared.tui_bip39 import Bip39LabTab
from textual.widgets import TextArea, Select, Input

class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield Bip39LabTab()

@pytest.mark.asyncio
async def test_bip39_lab_tab_components():
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        # Check components
        tab = app.query_one(Bip39LabTab)
        assert tab is not None

        words_select = app.query_one("#bip39-words-select", Select)
        assert words_select is not None
        assert words_select.value == 12

        phrase_area = app.query_one("#bip39-phrase-area", TextArea)
        assert phrase_area is not None

        passphrase_input = app.query_one("#bip39-passphrase-input", Input)
        assert passphrase_input is not None

        output_area = app.query_one("#bip39-output-area", TextArea)
        assert output_area is not None

        # Test Generate
        await pilot.click("#btn-bip39-generate")
        await pilot.pause()

        phrase = phrase_area.text
        assert phrase != ""
        assert len(phrase.split()) == 12
        assert output_area.text == "Mnemonic generated successfully."

        # Test Validate
        await pilot.click("#btn-bip39-validate")
        await pilot.pause()
        assert output_area.text == "The mnemonic phrase is VALID."

        # Test Validate Invalid
        await pilot.click("#bip39-phrase-area")
        await pilot.press("ctrl+a", "backspace")
        await pilot.click("#bip39-phrase-area")
        phrase_area.load_text("invalid phrase")
        await pilot.pause()
        await pilot.click("#btn-bip39-validate")
        await pilot.pause()
        assert output_area.text == "The mnemonic phrase is INVALID."

        # Test Seed
        await pilot.click("#bip39-phrase-area")
        await pilot.press("ctrl+a", "backspace")
        await pilot.click("#bip39-phrase-area")
        phrase_area.load_text(phrase) # restore valid phrase
        await pilot.pause()
        passphrase_input.value = "test_passphrase"
        await pilot.click("#btn-bip39-seed")
        await pilot.pause()
        assert "Seed (Hex):" in output_area.text

        # Test Clear
        await pilot.click("#btn-bip39-clear")
        await pilot.pause()
        assert phrase_area.text == ""
        assert passphrase_input.value == ""
        assert output_area.text == ""

@pytest.mark.asyncio
@patch('shared.bip39_lab.Bip39LabManager.generate', return_value={"success": False, "error": "Mock Error"})
async def test_generate_error(mock_generate):
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        output_area = app.query_one("#bip39-output-area", TextArea)
        await pilot.click("#btn-bip39-generate")
        await pilot.pause()
        assert "Error: Mock Error" in output_area.text

@pytest.mark.asyncio
async def test_validate_empty():
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        output_area = app.query_one("#bip39-output-area", TextArea)
        await pilot.click("#btn-bip39-validate")
        await pilot.pause()
        assert "Please provide a mnemonic phrase to validate" in output_area.text

@pytest.mark.asyncio
@patch('shared.bip39_lab.Bip39LabManager.validate', return_value={"success": False, "error": "Mock Error"})
async def test_validate_error(mock_validate):
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        phrase_area = app.query_one("#bip39-phrase-area", TextArea)
        output_area = app.query_one("#bip39-output-area", TextArea)

        await pilot.click("#bip39-phrase-area")
        await pilot.press("ctrl+a", "backspace")
        phrase_area.load_text("test")
        await pilot.pause()

        await pilot.click("#btn-bip39-validate")
        await pilot.pause()
        assert "Error: Mock Error" in output_area.text

@pytest.mark.asyncio
async def test_seed_empty():
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        output_area = app.query_one("#bip39-output-area", TextArea)
        await pilot.click("#btn-bip39-seed")
        await pilot.pause()
        assert "Please provide a mnemonic phrase to convert" in output_area.text

@pytest.mark.asyncio
@patch('shared.bip39_lab.Bip39LabManager.to_seed', return_value={"success": False, "error": "Mock Error"})
async def test_seed_error(mock_seed):
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        phrase_area = app.query_one("#bip39-phrase-area", TextArea)
        output_area = app.query_one("#bip39-output-area", TextArea)

        await pilot.click("#bip39-phrase-area")
        await pilot.press("ctrl+a", "backspace")
        phrase_area.load_text("test")
        await pilot.pause()

        await pilot.click("#btn-bip39-seed")
        await pilot.pause()
        assert "Error: Mock Error" in output_area.text

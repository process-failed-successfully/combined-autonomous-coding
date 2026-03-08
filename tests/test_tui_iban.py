import pytest
from textual.widgets import Input, Label, Button
from shared.tui_iban import IbanLabTab

class DummyInput:
    def __init__(self, value=""):
        self.value = value

class DummyLabel:
    def __init__(self):
        self.text = ""
    def update(self, text):
        self.text = text

@pytest.mark.asyncio
async def test_iban_tui_validate(pytestconfig):
    tab = IbanLabTab()
    valid_iban = tab.manager.generate("GB")

    # Mock query_one with dummies instead of actual Textual widgets to avoid context errors
    def mock_query_one(selector, *args, **kwargs):
        if selector == "#iban-validate-input":
            return DummyInput(valid_iban)
        elif selector == "#iban-validate-output":
            return DummyLabel()

    tab.query_one = mock_query_one
    tab.validate_iban()

@pytest.mark.asyncio
async def test_iban_tui_generate(pytestconfig):
    tab = IbanLabTab()

    # Mock query_one
    def mock_query_one(selector, *args, **kwargs):
        if selector == "#iban-generate-country":
            return DummyInput("DE")
        elif selector == "#iban-generate-output":
            return DummyLabel()

    tab.query_one = mock_query_one
    tab.generate_iban()

@pytest.mark.asyncio
async def test_iban_tui_parse(pytestconfig):
    tab = IbanLabTab()
    valid_iban = tab.manager.generate("FR")

    # Mock query_one
    def mock_query_one(selector, *args, **kwargs):
        if selector == "#iban-parse-input":
            return DummyInput(valid_iban)
        elif selector == "#iban-parse-output":
            return DummyLabel()

    tab.query_one = mock_query_one
    tab.parse_iban()

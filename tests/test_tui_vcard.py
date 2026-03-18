import pytest
from textual.app import App
from typing import Any
from textual.widgets import Input, Button, TextArea, Static
from shared.tui_vcard import VCardLabTab

class DummyApp(App[Any]):
    def compose(self):
        yield VCardLabTab()

@pytest.mark.asyncio
async def test_vcard_generate_success():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Fill in generate inputs
        first_in = app.query_one("#vcard-in-first", Input)
        last_in = app.query_one("#vcard-in-last", Input)
        email_in = app.query_one("#vcard-in-email", Input)

        first_in.value = "John"
        last_in.value = "Doe"
        email_in.value = "john@example.com"

        btn = app.query_one("#btn-vcard-generate", Button)
        await pilot.click("#btn-vcard-generate")
        await pilot.pause()

        # Check output
        out_area = app.query_one("#vcard-out-generate", TextArea)
        error_static = app.query_one("#vcard-generate-error", Static)

        assert "BEGIN:VCARD" in out_area.text
        assert "N:Doe;John" in out_area.text
        assert "john@example.com" in out_area.text
        assert str(error_static.render()) == ""

@pytest.mark.asyncio
async def test_vcard_generate_error():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Don't provide names
        first_in = app.query_one("#vcard-in-first", Input)
        last_in = app.query_one("#vcard-in-last", Input)
        first_in.value = ""
        last_in.value = ""

        btn = app.query_one("#btn-vcard-generate", Button)
        await pilot.click("#btn-vcard-generate")
        await pilot.pause()

        # Check output
        out_area = app.query_one("#vcard-out-generate", TextArea)
        error_static = app.query_one("#vcard-generate-error", Static)

        assert out_area.text == ""
        assert "Provide First Name or Last Name" in str(error_static.render())

@pytest.mark.asyncio
async def test_vcard_parse_success():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Fill in parse input
        in_area = app.query_one("#vcard-in-parse", TextArea)
        vcard_text = "BEGIN:VCARD\nVERSION:3.0\nN:Smith;Will;;;\nEND:VCARD"
        in_area.text = vcard_text

        btn = app.query_one("#btn-vcard-parse", Button)
        await pilot.click("#btn-vcard-parse")
        await pilot.pause()

        # Check output
        out_area = app.query_one("#vcard-out-parse", TextArea)
        error_static = app.query_one("#vcard-parse-error", Static)

        assert '"first_name": "Will"' in out_area.text
        assert '"last_name": "Smith"' in out_area.text
        assert str(error_static.render()) == ""

@pytest.mark.asyncio
async def test_vcard_parse_empty():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Fill in parse input with empty
        in_area = app.query_one("#vcard-in-parse", TextArea)
        in_area.text = "   "

        btn = app.query_one("#btn-vcard-parse", Button)
        await pilot.click("#btn-vcard-parse")
        await pilot.pause()

        # Check output
        out_area = app.query_one("#vcard-out-parse", TextArea)
        error_static = app.query_one("#vcard-parse-error", Static)

        assert out_area.text == ""
        assert "Provide vCard text" in str(error_static.render())

@pytest.mark.asyncio
async def test_vcard_parse_error():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Fill in parse input with invalid vCard
        in_area = app.query_one("#vcard-in-parse", TextArea)
        in_area.text = "INVALID VCARD CONTENT"

        btn = app.query_one("#btn-vcard-parse", Button)
        await pilot.click("#btn-vcard-parse")
        await pilot.pause()

        # Check output
        out_area = app.query_one("#vcard-out-parse", TextArea)
        error_static = app.query_one("#vcard-parse-error", Static)

        assert out_area.text == ""
        assert "Error: Invalid vCard" in str(error_static.render())

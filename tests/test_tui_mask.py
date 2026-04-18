import pytest
pytest.importorskip("textual")
from textual.app import App
from textual.widgets import TabbedContent
from shared.tui_mask import MaskLabTab

class MaskApp(App):
    def compose(self):
        with TabbedContent():
            yield MaskLabTab()

@pytest.mark.asyncio
async def test_mask_lab_tui():
    app = MaskApp()
    async with app.run_test() as pilot:
        tab = app.query_one(MaskLabTab)

        # Set text and test
        tab.query_one("#mask-input").text = "My email is test@example.com."
        # Deselect others
        tab.query_one("#mask-chk-phone").value = False
        tab.query_one("#mask-chk-credit_card").value = False
        tab.query_one("#mask-chk-ssn").value = False
        tab.query_one("#mask-chk-ipv4").value = False

        # Invoke action directly as per memory instructions for robust testing
        tab.mask_data()
        await pilot.pause()

        output = tab.query_one("#mask-output").text
        assert "t**t@example.com" in output

@pytest.mark.asyncio
async def test_mask_lab_tui_empty():
    app = MaskApp()
    async with app.run_test() as pilot:
        tab = app.query_one(MaskLabTab)

        # Empty text
        tab.query_one("#mask-input").text = ""

        # Invoke action
        tab.mask_data()
        await pilot.pause()

        output = tab.query_one("#mask-output").text
        assert output == ""

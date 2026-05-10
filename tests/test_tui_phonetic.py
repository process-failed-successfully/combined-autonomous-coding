import pytest
from pathlib import Path

try:
    import textual
    TEXTUAL_AVAILABLE = True
    from textual.app import App
    from textual.widgets import TextArea, Button
    from shared.tui_phonetic import PhoneticLabTab
except ImportError:
    TEXTUAL_AVAILABLE = False
    App = object

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="textual is not installed")
@pytest.mark.asyncio
async def test_tui_phonetic_encode():
    class PhoneticApp(App):
        def compose(self):
            yield PhoneticLabTab(project_dir=Path("."))

    app = PhoneticApp()
    async with app.run_test(headless=True) as pilot:
        tab = app.query_one(PhoneticLabTab)

        input_area = tab.query_one("#phonetic-input", TextArea)
        output_area = tab.query_one("#phonetic-output", TextArea)
        encode_btn = tab.query_one("#btn-phonetic-soundex", Button)

        input_area.text = "Robert"
        await pilot.click("#btn-phonetic-soundex")
        assert output_area.text == "R163"

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="textual is not installed")
@pytest.mark.asyncio
async def test_tui_phonetic_clear():
    class PhoneticApp(App):
        def compose(self):
            yield PhoneticLabTab(project_dir=Path("."))

    app = PhoneticApp()
    async with app.run_test(headless=True) as pilot:
        tab = app.query_one(PhoneticLabTab)

        input_area = tab.query_one("#phonetic-input", TextArea)
        output_area = tab.query_one("#phonetic-output", TextArea)

        input_area.text = "Robert"
        await pilot.click("#btn-phonetic-soundex")
        assert output_area.text == "R163"

        await pilot.click("#btn-phonetic-clear")
        assert input_area.text == ""
        assert output_area.text == ""

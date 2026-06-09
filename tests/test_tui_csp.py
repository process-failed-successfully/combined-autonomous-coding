import pytest
from textual.app import App
from shared.tui_csp import CspLabTab
from textual.widgets import Button, TextArea

class DummyApp(App):
    def compose(self):
        yield CspLabTab(project_dir=".")

@pytest.mark.asyncio
async def test_csp_lab_tab_render():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Check if the tab rendered
        assert app.query_one(CspLabTab) is not None

        # Check inputs exist
        assert app.query_one("#csp-input") is not None
        assert app.query_one("#csp-output") is not None

        # Check buttons exist
        assert app.query_one("#btn-csp-parse") is not None
        assert app.query_one("#btn-csp-validate") is not None
        assert app.query_one("#btn-csp-clear") is not None

@pytest.mark.asyncio
async def test_csp_lab_interactions():
    app = DummyApp()
    async with app.run_test() as pilot:
        tab = app.query_one(CspLabTab)

        # Test clear
        app.query_one("#csp-input", TextArea).text = "test input"
        app.query_one("#csp-output", TextArea).text = "test output"
        await tab.on_button_pressed(Button.Pressed(app.query_one("#btn-csp-clear")))
        assert app.query_one("#csp-input", TextArea).text == ""
        assert app.query_one("#csp-output", TextArea).text == ""

        # Test parse
        app.query_one("#csp-input", TextArea).text = "default-src 'self'"
        await tab.on_button_pressed(Button.Pressed(app.query_one("#btn-csp-parse")))
        output = app.query_one("#csp-output", TextArea).text
        assert "default-src" in output
        assert "'self'" in output

        # Test validate valid
        await tab.on_button_pressed(Button.Pressed(app.query_one("#btn-csp-validate")))
        output = app.query_one("#csp-output", TextArea).text
        assert "✅ Policy is valid" in output

        # Test validate invalid
        app.query_one("#csp-input", TextArea).text = "default-src self"
        await tab.on_button_pressed(Button.Pressed(app.query_one("#btn-csp-validate")))
        output = app.query_one("#csp-output", TextArea).text
        assert "❌ Policy has warnings" in output
        assert "single quotes" in output

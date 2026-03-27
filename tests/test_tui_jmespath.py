import pytest
from pathlib import Path
from textual.app import App
from textual.widgets import Input, TextArea, RichLog
from shared.tui_jmespath import JmesPathLabTab


class DummyApp(App[None]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tab = JmesPathLabTab(project_dir=Path("."))

    def compose(self):
        yield self.tab


@pytest.mark.asyncio
async def test_jmespath_lab_tab_rendering():
    app = DummyApp()
    async with app.run_test(size=(120, 40)):
        assert app.query_one("#jmespath-input", Input) is not None
        assert app.query_one("#jmespath-input-json", TextArea) is not None
        assert app.query_one("#jmespath-results-log", RichLog) is not None


@pytest.mark.asyncio
async def test_jmespath_lab_tab_evaluation():
    app = DummyApp()
    async with app.run_test(size=(120, 40)) as pilot:
        # Initial render should populate empty results

        # Test valid evaluation
        app.query_one("#jmespath-input-json", TextArea).text = '{"key": "value", "list": [1, 2]}'
        app.query_one("#jmespath-input", Input).value = "list"
        await pilot.pause(0.1)  # Let events propagate

        log = app.query_one("#jmespath-results-log", RichLog)
        content = str(list(log.lines))
        assert "1" in content
        assert "2" in content


@pytest.mark.asyncio
async def test_jmespath_lab_tab_invalid_json():
    app = DummyApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#jmespath-input-json", TextArea).text = '{"key": "value"'  # Missing bracket
        app.query_one("#jmespath-input", Input).value = "key"
        await pilot.pause(0.1)

        log = app.query_one("#jmespath-results-log", RichLog)
        content = str(list(log.lines))
        assert "Invalid JSON:" in content


@pytest.mark.asyncio
async def test_jmespath_lab_tab_invalid_path():
    app = DummyApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#jmespath-input-json", TextArea).text = '{"key": "value"}'
        app.query_one("#jmespath-input", Input).value = "a..b"
        await pilot.pause(0.1)

        log = app.query_one("#jmespath-results-log", RichLog)
        content = str(list(log.lines))
        assert "Error evaluating JMESPath" in content

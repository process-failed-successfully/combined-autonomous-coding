import pytest
from textual.widgets import TextArea, Input, Button
from shared.tui_pipeline import PipelineLabTab
from textual.app import App, ComposeResult

class PipelineLabApp(App):
    def compose(self) -> ComposeResult:
        yield PipelineLabTab()

@pytest.mark.asyncio
async def test_pipeline_lab_tui():
    app = PipelineLabApp()
    async with app.run_test(size=(120, 40)) as pilot:
        # Initial state
        assert app.query_one("#pipeline-input", TextArea).text == ""
        assert app.query_one("#pipeline-ops", Input).value == ""
        assert app.query_one("#pipeline-output", TextArea).text == ""

        # Set input and operations
        app.query_one("#pipeline-input", TextArea).text = '{"items": [1, 2, 3]}'
        app.query_one("#pipeline-ops", Input).value = "json-parse | json-get items | count"

        app.query_one("#tab-pipeline", PipelineLabTab).process_pipeline()
        assert app.query_one("#pipeline-output", TextArea).text == "3"

        # Click Clear
        app.query_one("#tab-pipeline", PipelineLabTab).clear_content()
        assert app.query_one("#pipeline-input", TextArea).text == ""
        assert app.query_one("#pipeline-ops", Input).value == ""
        assert app.query_one("#pipeline-output", TextArea).text == ""

@pytest.mark.asyncio
async def test_pipeline_lab_tui_error():
    app = PipelineLabApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#pipeline-input", TextArea).text = "test"
        app.query_one("#pipeline-ops", Input).value = "unknown-op"

        app.query_one("#tab-pipeline", PipelineLabTab).process_pipeline()
        assert "Error: Unknown operation: unknown-op" in app.query_one("#pipeline-output", TextArea).text

@pytest.mark.asyncio
async def test_pipeline_lab_tui_empty_input():
    app = PipelineLabApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#pipeline-ops", Input).value = "upper"
        app.query_one("#tab-pipeline", PipelineLabTab).process_pipeline()
        assert app.query_one("#pipeline-output", TextArea).text == ""

@pytest.mark.asyncio
async def test_pipeline_lab_tui_empty_ops():
    app = PipelineLabApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#pipeline-input", TextArea).text = "test"
        app.query_one("#tab-pipeline", PipelineLabTab).process_pipeline()
        assert app.query_one("#pipeline-output", TextArea).text == ""

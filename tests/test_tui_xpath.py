import pytest
from textual.app import App, ComposeResult
from textual.widgets import Input, Button, TextArea
from typing import Any
import json

from shared.tui_xpath import XpathLabTab


class DummyApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield XpathLabTab()


@pytest.mark.asyncio
async def test_xpath_tui_layout():
    app = DummyApp()
    async with app.run_test():
        tab = app.query_one(XpathLabTab)
        assert tab is not None

        # Check inputs exist
        assert app.query_one("#xpath-expression", Input) is not None
        assert app.query_one("#xpath-input", TextArea) is not None
        assert app.query_one("#xpath-result", TextArea) is not None

        # Check buttons
        assert app.query_one("#btn-evaluate", Button) is not None
        assert app.query_one("#btn-clear", Button) is not None


@pytest.mark.asyncio
async def test_xpath_tui_evaluate_success():
    app = DummyApp()
    async with app.run_test() as pilot:
        xml_input = app.query_one("#xpath-input", TextArea)
        expression_input = app.query_one("#xpath-expression", Input)
        result_area = app.query_one("#xpath-result", TextArea)
        btn_eval = app.query_one("#btn-evaluate", Button)

        xml_input.text = "<root><item id='1'>Value</item></root>"
        expression_input.value = ".//item"

        btn_eval.press()
        await pilot.pause()

        # Result should be JSON containing matches
        result_data = json.loads(result_area.text)
        assert len(result_data) == 1
        assert result_data[0]["text"] == "Value"
        assert result_data[0]["attributes"]["id"] == "1"


@pytest.mark.asyncio
async def test_xpath_tui_evaluate_empty_input():
    app = DummyApp()
    async with app.run_test() as pilot:
        expression_input = app.query_one("#xpath-expression", Input)
        result_area = app.query_one("#xpath-result", TextArea)
        btn_eval = app.query_one("#btn-evaluate", Button)

        expression_input.value = ".//item"
        btn_eval.press()
        await pilot.pause()

        result_data = json.loads(result_area.text)
        assert "Empty XML input" in result_data["error"]


@pytest.mark.asyncio
async def test_xpath_tui_evaluate_empty_expression():
    app = DummyApp()
    async with app.run_test() as pilot:
        xml_input = app.query_one("#xpath-input", TextArea)
        result_area = app.query_one("#xpath-result", TextArea)
        btn_eval = app.query_one("#btn-evaluate", Button)

        xml_input.text = "<root><item id='1'>Value</item></root>"
        btn_eval.press()
        await pilot.pause()

        result_data = json.loads(result_area.text)
        assert "Empty XPath expression" in result_data["error"]


@pytest.mark.asyncio
async def test_xpath_tui_evaluate_error():
    app = DummyApp()
    async with app.run_test() as pilot:
        xml_input = app.query_one("#xpath-input", TextArea)
        expression_input = app.query_one("#xpath-expression", Input)
        result_area = app.query_one("#xpath-result", TextArea)
        btn_eval = app.query_one("#btn-evaluate", Button)

        xml_input.text = "<root><item id='1'>Value</item></root>"
        expression_input.value = "////"  # Invalid XPath

        btn_eval.press()
        await pilot.pause()

        result_data = json.loads(result_area.text)
        assert "error" in result_data
        assert "Invalid XPath expression" in result_data["error"]


@pytest.mark.asyncio
async def test_xpath_tui_clear():
    app = DummyApp()
    async with app.run_test() as pilot:
        xml_input = app.query_one("#xpath-input", TextArea)
        expression_input = app.query_one("#xpath-expression", Input)
        result_area = app.query_one("#xpath-result", TextArea)
        btn_clear = app.query_one("#btn-clear", Button)

        xml_input.text = "<root></root>"
        expression_input.value = ".//item"
        result_area.text = "Some result"

        btn_clear.press()
        await pilot.pause()

        assert xml_input.text == ""
        assert expression_input.value == ""
        assert result_area.text == ""

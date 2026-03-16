import pytest
from unittest.mock import patch, MagicMock
from shared.tui_base36 import Base36LabTab
from textual.widgets import TextArea

@pytest.fixture
def base36_tab():
    tab = Base36LabTab()
    # Mock query_one to return TextAreas
    input_area = MagicMock(spec=TextArea)
    input_area.text = ""
    output_area = MagicMock(spec=TextArea)
    output_area.text = ""

    def mock_query_one(selector, expect_type=None):
        if selector == "#b36-input":
            return input_area
        elif selector == "#b36-output":
            return output_area
        return MagicMock()

    tab.query_one = MagicMock(side_effect=mock_query_one)
    tab.notify = MagicMock()
    return tab, input_area, output_area

@pytest.mark.asyncio
async def test_base36_tab_encode(base36_tab):
    tab, input_area, output_area = base36_tab
    input_area.text = "hello"

    class MockButton:
        id = "btn-b36-encode"

    class MockEvent:
        button = MockButton()

    await tab.on_button_pressed(MockEvent())

    assert output_area.text == "5pzcszu7"
    tab.notify.assert_called_with("Done.")

@pytest.mark.asyncio
async def test_base36_tab_decode(base36_tab):
    tab, input_area, output_area = base36_tab
    input_area.text = "5pzcszu7"

    class MockButton:
        id = "btn-b36-decode"

    class MockEvent:
        button = MockButton()

    await tab.on_button_pressed(MockEvent())

    assert output_area.text == "hello"
    tab.notify.assert_called_with("Done.")

@pytest.mark.asyncio
async def test_base36_tab_swap(base36_tab):
    tab, input_area, output_area = base36_tab
    input_area.text = "hello"
    output_area.text = "world"

    class MockButton:
        id = "btn-b36-swap"

    class MockEvent:
        button = MockButton()

    await tab.on_button_pressed(MockEvent())

    assert input_area.text == "world"
    assert output_area.text == "hello"
    tab.notify.assert_called_with("Swapped Input and Output.")

@pytest.mark.asyncio
async def test_base36_tab_clear(base36_tab):
    tab, input_area, output_area = base36_tab
    input_area.text = "hello"
    output_area.text = "world"

    class MockButton:
        id = "btn-b36-clear"

    class MockEvent:
        button = MockButton()

    await tab.on_button_pressed(MockEvent())

    assert input_area.text == ""
    assert output_area.text == ""
    tab.notify.assert_called_with("Cleared.")

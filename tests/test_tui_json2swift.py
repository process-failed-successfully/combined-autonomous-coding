import pytest
from unittest.mock import MagicMock

pytestmark = pytest.mark.asyncio

try:
    import textual
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual not installed")
async def test_json2swift_tui_convert():
    from shared.tui_json2swift import Json2SwiftLabTab
    tab = Json2SwiftLabTab()

    input_ta = MagicMock()
    input_ta.text = '{"name": "Alice"}'

    output_ta = MagicMock()

    name_input = MagicMock()
    name_input.value = "RootStruct"

    status_static = MagicMock()

    def mock_query_one(selector, *args, **kwargs):
        if selector == "#json2swift-input-ta": return input_ta
        if selector == "#json2swift-output-ta": return output_ta
        if selector == "#json2swift-name-input": return name_input
        if selector == "#json2swift-status": return status_static
        raise ValueError(f"Unknown selector: {selector}")

    tab.query_one = mock_query_one

    await tab.action_convert()

    assert "struct RootStruct: Codable {" in output_ta.text
    status_static.update.assert_called_with("[green]Conversion successful.[/green]")

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual not installed")
async def test_json2swift_tui_empty_input():
    from shared.tui_json2swift import Json2SwiftLabTab
    tab = Json2SwiftLabTab()

    input_ta = MagicMock()
    input_ta.text = ''

    output_ta = MagicMock()

    name_input = MagicMock()
    name_input.value = "RootStruct"

    status_static = MagicMock()

    def mock_query_one(selector, *args, **kwargs):
        if selector == "#json2swift-input-ta": return input_ta
        if selector == "#json2swift-output-ta": return output_ta
        if selector == "#json2swift-name-input": return name_input
        if selector == "#json2swift-status": return status_static
        raise ValueError(f"Unknown selector: {selector}")

    tab.query_one = mock_query_one

    await tab.action_convert()

    assert output_ta.text == ""
    status_static.update.assert_called_with("[yellow]Input JSON is empty.[/yellow]")

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual not installed")
async def test_json2swift_tui_invalid_json():
    from shared.tui_json2swift import Json2SwiftLabTab
    tab = Json2SwiftLabTab()

    input_ta = MagicMock()
    input_ta.text = '{invalid}'

    output_ta = MagicMock()

    name_input = MagicMock()
    name_input.value = "RootStruct"

    status_static = MagicMock()

    def mock_query_one(selector, *args, **kwargs):
        if selector == "#json2swift-input-ta": return input_ta
        if selector == "#json2swift-output-ta": return output_ta
        if selector == "#json2swift-name-input": return name_input
        if selector == "#json2swift-status": return status_static
        raise ValueError(f"Unknown selector: {selector}")

    tab.query_one = mock_query_one

    await tab.action_convert()

    assert output_ta.text == ""
    assert "Invalid JSON:" in status_static.update.call_args[0][0]

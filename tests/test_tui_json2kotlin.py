import pytest

try:
    import textual
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

pytestmark = pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual is not available")

if TEXTUAL_AVAILABLE:
    from unittest.mock import MagicMock, patch
    from shared.tui_json2kotlin import Json2KotlinTab
    from textual.widgets import TextArea, Input

@pytest.mark.asyncio
async def test_json2kotlin_tab_compose():
    if not TEXTUAL_AVAILABLE:
        return
    tab = Json2KotlinTab()
    assert tab.id == "tab-json2kotlin"

@pytest.mark.asyncio
async def test_json2kotlin_action_convert():
    if not TEXTUAL_AVAILABLE:
        return
    tab = Json2KotlinTab()

    # Mock inputs
    mock_input_area = MagicMock()
    mock_input_area.text = '{"test": "val"}'

    mock_output_area = MagicMock()

    mock_root_name = MagicMock()
    mock_root_name.value = "TestClass"

    mock_package_name = MagicMock()
    mock_package_name.value = "org.test"

    def mock_query_one(selector, *args, **kwargs):
        if selector == "#j2k-input":
            return mock_input_area
        elif selector == "#j2k-output":
            return mock_output_area
        elif selector == "#j2k-root-name":
            return mock_root_name
        elif selector == "#j2k-package-name":
            return mock_package_name
        return MagicMock()

    tab.query_one = mock_query_one

    # Run convert action
    tab.action_convert()

    # Assert
    assert "data class TestClass(" in mock_output_area.text
    assert "package org.test" in mock_output_area.text
    assert "val test: String" in mock_output_area.text

@pytest.mark.asyncio
async def test_json2kotlin_action_clear():
    if not TEXTUAL_AVAILABLE:
        return
    tab = Json2KotlinTab()

    mock_input_area = MagicMock()
    mock_output_area = MagicMock()

    def mock_query_one(selector, *args, **kwargs):
        if selector == "#j2k-input":
            return mock_input_area
        elif selector == "#j2k-output":
            return mock_output_area
        return MagicMock()

    tab.query_one = mock_query_one

    tab.action_clear()

    assert mock_input_area.text == ""
    assert mock_output_area.text == ""

import pytest
from unittest.mock import MagicMock
import sys

class MockWidget:
    def __init__(self, *args, **kwargs):
        pass

class MockButton(MockWidget):
    class Pressed:
        pass

class MockLabel(MockWidget):
    pass

class MockTextArea(MockWidget):
    pass

class MockVertical(MockWidget):
    pass

class MockHorizontal(MockWidget):
    pass

def get_mock_widgets():
    m = MagicMock()
    m.Button = MockButton
    m.Label = MockLabel
    m.TextArea = MockTextArea
    return m

def get_mock_containers():
    m = MagicMock()
    m.Container = MockWidget
    m.Vertical = MockVertical
    m.Horizontal = MockHorizontal
    return m

def test_tui_html2md_convert(monkeypatch):
    monkeypatch.setitem(sys.modules, 'textual', MagicMock())
    monkeypatch.setitem(sys.modules, 'textual.app', MagicMock(ComposeResult=list))
    monkeypatch.setitem(sys.modules, 'textual.containers', get_mock_containers())
    monkeypatch.setitem(sys.modules, 'textual.widgets', get_mock_widgets())
    monkeypatch.setitem(sys.modules, 'textual.binding', MagicMock())

    from shared.tui_html2md import Html2MdTab

    tab = Html2MdTab()

    mock_input = MagicMock()
    mock_input.text = "<p>Hello <b>World</b>!</p>"
    mock_output = MagicMock()
    mock_output.text = ""

    def mock_query_one(selector, widget_type=None):
        if selector == "#input-html":
            return mock_input
        elif selector == "#output-md":
            return mock_output
        return MagicMock()

    tab.query_one = mock_query_one  # type: ignore
    tab.action_convert()

    assert "Hello **World**!" in mock_output.text
    # Call error branch for full coverage
    mock_input.text = "invalid"
    tab.manager.convert = MagicMock(side_effect=Exception("Test Error"))  # type: ignore
    tab.action_convert()
    assert "Error converting HTML: Test Error" in mock_output.text

def test_tui_html2md_clear(monkeypatch):
    monkeypatch.setitem(sys.modules, 'textual', MagicMock())
    monkeypatch.setitem(sys.modules, 'textual.app', MagicMock(ComposeResult=list))
    monkeypatch.setitem(sys.modules, 'textual.containers', get_mock_containers())
    monkeypatch.setitem(sys.modules, 'textual.widgets', get_mock_widgets())
    monkeypatch.setitem(sys.modules, 'textual.binding', MagicMock())

    from shared.tui_html2md import Html2MdTab

    tab = Html2MdTab()

    mock_input = MagicMock()
    mock_input.text = "<p>Hello</p>"
    mock_output = MagicMock()
    mock_output.text = "Hello"

    def mock_query_one(selector, widget_type=None):
        if selector == "#input-html":
            return mock_input
        elif selector == "#output-md":
            return mock_output
        return MagicMock()

    tab.query_one = mock_query_one  # type: ignore
    tab.action_clear()

    assert mock_input.text == ""
    assert mock_output.text == ""

def test_tui_html2md_compose(monkeypatch):
    monkeypatch.setitem(sys.modules, 'textual', MagicMock())
    monkeypatch.setitem(sys.modules, 'textual.app', MagicMock(ComposeResult=list))
    monkeypatch.setitem(sys.modules, 'textual.containers', get_mock_containers())
    monkeypatch.setitem(sys.modules, 'textual.widgets', get_mock_widgets())
    monkeypatch.setitem(sys.modules, 'textual.binding', MagicMock())

    from shared.tui_html2md import Html2MdTab

    tab = Html2MdTab()
    res = list(tab.compose())
    assert len(res) > 0

def test_tui_html2md_on_button_pressed(monkeypatch):
    monkeypatch.setitem(sys.modules, 'textual', MagicMock())
    monkeypatch.setitem(sys.modules, 'textual.app', MagicMock(ComposeResult=list))
    monkeypatch.setitem(sys.modules, 'textual.containers', get_mock_containers())
    monkeypatch.setitem(sys.modules, 'textual.widgets', get_mock_widgets())
    monkeypatch.setitem(sys.modules, 'textual.binding', MagicMock())

    from shared.tui_html2md import Html2MdTab

    tab = Html2MdTab()

    mock_convert = MagicMock()
    mock_clear = MagicMock()
    tab.action_convert = mock_convert
    tab.action_clear = mock_clear

    class MButton:
        id = "btn-convert"
    class MockEvent:
        button = MButton()

    tab.on_button_pressed(MockEvent())
    mock_convert.assert_called_once()

    MockEvent.button.id = "btn-clear"
    tab.on_button_pressed(MockEvent())
    mock_clear.assert_called_once()

    MockEvent.button.id = "other"
    tab.on_button_pressed(MockEvent())

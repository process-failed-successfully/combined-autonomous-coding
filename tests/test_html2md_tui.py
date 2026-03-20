from unittest.mock import MagicMock
import sys


class _MockButton:
    class Pressed:
        pass


class _MockTextualWidgetsModule:
    Header = object
    Footer = object
    Input = object
    Button = _MockButton
    Static = object
    Label = object
    TextArea = object


def test_tui_html2md_convert(monkeypatch):
    monkeypatch.setitem(sys.modules, 'textual', MagicMock())
    monkeypatch.setitem(sys.modules, 'textual.app', MagicMock(ComposeResult=list))
    monkeypatch.setitem(sys.modules, 'textual.containers', MagicMock(Container=object, Horizontal=object, Vertical=object))
    monkeypatch.setitem(sys.modules, 'textual.widgets', _MockTextualWidgetsModule())
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
    monkeypatch.setitem(sys.modules, 'textual.containers', MagicMock(Container=object, Horizontal=object, Vertical=object))
    monkeypatch.setitem(sys.modules, 'textual.widgets', _MockTextualWidgetsModule())
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

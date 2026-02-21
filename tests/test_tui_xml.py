import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add shared to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui_xml import XmlLabTab  # noqa: E402


class TestXmlLabTab:
    @pytest.fixture
    def tab(self):
        # Mock project_dir
        with patch("shared.tui_xml.XmlLabManager") as MockManager:
            tab = XmlLabTab(Path("/tmp"))
            tab.manager = MockManager.return_value
            return tab

    def test_on_format(self, tab):
        original_xml = "<root>  <child/></root>"
        # Mock widgets
        mock_input = MagicMock()
        mock_input.text = original_xml
        mock_log = MagicMock()

        # Mock query_one
        def query_one_side_effect(selector, type=None):
            if selector == "#xml-input":
                return mock_input
            if selector == "#xml-output":
                return mock_log
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Mock manager
        tab.manager.parse.return_value = "root_element"
        tab.manager.format.return_value = "<root><child/></root>"

        # Run
        tab.on_format()

        # Verify
        tab.manager.parse.assert_called_with(original_xml)
        tab.manager.format.assert_called_with("root_element")
        assert mock_input.text == "<root><child/></root>"
        mock_log.write.assert_called_with("[green]Formatted XML.[/green]")

    def test_on_validate_valid(self, tab):
        mock_input = MagicMock()
        mock_input.text = "<root/>"
        mock_log = MagicMock()

        tab.query_one = MagicMock(side_effect=lambda s, t=None: mock_input if s == "#xml-input" else mock_log)

        tab.manager.validate.return_value = None

        tab.on_validate()

        tab.manager.validate.assert_called_with("<root/>")
        mock_log.write.assert_called_with("[green]Valid XML.[/green]")

    def test_on_validate_invalid(self, tab):
        mock_input = MagicMock()
        mock_input.text = "<root>"
        mock_log = MagicMock()

        tab.query_one = MagicMock(side_effect=lambda s, t=None: mock_input if s == "#xml-input" else mock_log)

        tab.manager.validate.return_value = "Error"

        tab.on_validate()

        mock_log.write.assert_called_with("[red]Invalid XML: Error[/red]")

    def test_on_to_json(self, tab):
        mock_input = MagicMock()
        mock_input.text = "<root>val</root>"
        mock_log = MagicMock()

        tab.query_one = MagicMock(side_effect=lambda s, t=None: mock_input if s == "#xml-input" else mock_log)

        tab.manager.parse.return_value = "root"
        tab.manager.to_json.return_value = {"root": "val"}

        tab.on_to_json()

        tab.manager.to_json.assert_called_with("root")
        # Check if log.write was called with json string
        args, _ = mock_log.write.call_args
        assert '"root": "val"' in args[0]

    def test_on_xpath(self, tab):
        mock_input = MagicMock()
        mock_input.text = "<root><c/></root>"
        mock_xpath_input = MagicMock()
        mock_xpath_input.value = "//c"
        mock_log = MagicMock()

        def query_one(selector, type=None):
            if selector == "#xml-input":
                return mock_input
            if selector == "#xml-xpath-input":
                return mock_xpath_input
            if selector == "#xml-output":
                return mock_log
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one)

        tab.manager.parse.return_value = "root"
        tab.manager.xpath.return_value = ["match1", "match2"]
        tab.manager.format.side_effect = lambda x: f"formatted_{x}"

        tab.on_xpath()

        tab.manager.xpath.assert_called_with("root", "//c")
        mock_log.write.assert_any_call("Found 2 matches:")
        # Check if formatted matches are logged
        # Since write is called multiple times, we need to inspect calls
        calls = mock_log.write.call_args_list
        assert any("formatted_match1" in str(c) for c in calls)
        assert any("formatted_match2" in str(c) for c in calls)

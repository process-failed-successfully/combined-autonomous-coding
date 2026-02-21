import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import xml.etree.ElementTree as ET
import sys
import tempfile
import os
from typing import Any, cast

# Add parent dir to path to find shared modules
sys.path.append(str(Path(__file__).parent.parent))

# Import AFTER sys.path.append
from shared.tui_xml import XmlLabTab  # noqa: E402


class TestXmlLabTab(unittest.TestCase):
    def setUp(self) -> None:
        self.project_dir = Path("/tmp/test_project")
        self.tab = XmlLabTab(self.project_dir)
        # We DO NOT mock self.tab.manager, we let it be the real one
        # self.tab.manager = MagicMock()

        # Mock internal DOM methods
        self.tab.query_one = MagicMock()  # type: ignore
        self.tab.notify = MagicMock()  # type: ignore

    def test_load_file_integration(self) -> None:
        # Create a real temporary XML file
        content = "<root><child>Test</child></root>"
        with tempfile.NamedTemporaryFile(mode='w', suffix=".xml", delete=False) as f:
            f.write(content)
            path = Path(f.name)

        try:
            # Patch build_tree to avoid DOM issues (Textual widgets)
            with patch.object(self.tab, 'build_tree') as mock_build:
                self.tab.load_file(path)

                # Verify root was loaded correctly using real manager
                self.assertIsNotNone(self.tab.root)
                # Need to check not None for mypy
                if self.tab.root is not None:
                    self.assertEqual(self.tab.root.tag, "root")
                    child = self.tab.root.find("child")
                    if child is not None:
                        self.assertEqual(child.text, "Test")

                mock_build.assert_called_once()
                # Check buttons enabled (query_one called)
                cast(MagicMock, self.tab.query_one).assert_called()
        finally:
            os.remove(path)

    def test_format_integration(self) -> None:
        self.tab.root = ET.fromstring("<root><child>Text</child></root>")

        # Mock rich log
        rich_log = MagicMock()
        cast(MagicMock, self.tab.query_one).return_value = rich_log

        self.tab.on_format()

        # Check that rich_log.write was called with formatted string
        # We can't assert exact string easily due to whitespace, but we can check content
        args = rich_log.write.call_args[0]
        self.assertTrue(len(args) > 0)
        self.assertIn("<root>", args[0])
        self.assertIn("  <child>Text</child>", args[0])  # indent check if manager does indent

    def test_xpath_integration(self) -> None:
        self.tab.root = ET.fromstring("<root><child id='1'>Match</child><child id='2'>No</child></root>")

        # Mock inputs
        inputs = {
            "#xml-xpath-input": MagicMock(value="./child[@id='1']")
        }
        cast(MagicMock, self.tab.query_one).side_effect = lambda selector, *args: inputs.get(selector, MagicMock())

        # Capture log
        rich_log = MagicMock()
        # We need query_one("#xml-log") to return rich_log
        # Update side_effect

        def side_effect(selector: str, *args: Any) -> Any:
            if selector == "#xml-log":
                return rich_log
            return inputs.get(selector, MagicMock())
        cast(MagicMock, self.tab.query_one).side_effect = side_effect

        self.tab.on_xpath()

        # Check output
        # Log calls:
        # 1. header
        # 2. result item
        calls = rich_log.write.call_args_list
        self.assertTrue(len(calls) >= 2)
        result_str = calls[1][0][0]  # first arg of second call
        self.assertIn("Match", result_str)

    def test_edit_integration(self) -> None:
        self.tab.root = ET.fromstring("<root><tag>Old</tag></root>")

        inputs = {
            "#xml-xpath-input": MagicMock(value=".//tag"),
            "#xml-value-input": MagicMock(value="New"),
            "#xml-attr-input": MagicMock(value="")
        }

        def side_effect(selector: str, *args: Any) -> Any:
            if selector == "#xml-log":
                return MagicMock()
            return inputs.get(selector, MagicMock())
        cast(MagicMock, self.tab.query_one).side_effect = side_effect

        with patch.object(self.tab, 'build_tree'):
            self.tab.on_edit()

            if self.tab.root is not None:
                tag = self.tab.root.find("tag")
                if tag is not None:
                    self.assertEqual(tag.text, "New")


if __name__ == '__main__':
    unittest.main()

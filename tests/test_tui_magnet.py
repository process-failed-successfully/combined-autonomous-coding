import unittest
from textual.widgets import TextArea, Button
from shared.tui_magnet import MagnetLabTab
from unittest.mock import patch


class TestMagnetLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_magnet_lab_tab_initialization(self):
        self.tab = MagnetLabTab()
        self.assertIsInstance(self.tab, MagnetLabTab)

    async def test_magnet_lab_parse(self):
        self.tab = MagnetLabTab()
        # Create a mock environment
        class MockApp:
            pass

        input_area = TextArea(id="magnet-input")
        output_area = TextArea(id="magnet-output")

        # Set up a mock query_one
        def mock_query_one(selector, expect_type=None):
            if selector == "#magnet-input":
                return input_area
            if selector == "#magnet-output":
                return output_area
            return None
        self.tab.query_one = mock_query_one

        # Test Parse
        input_area.text = "magnet:?xt=urn:btih:b9968411c52112e4f0ddfc9a1e04e4c27b08dd97"

        event = Button.Pressed(Button(id="btn-parse"))
        self.tab.on_button_pressed(event)

        self.assertIn("urn:btih:b9968411c52112e4f0ddfc9a1e04e4c27b08dd97", output_area.text)

    async def test_magnet_lab_build(self):
        self.tab = MagnetLabTab()
        input_area = TextArea(id="magnet-input")
        output_area = TextArea(id="magnet-output")

        def mock_query_one(selector, expect_type=None):
            if selector == "#magnet-input": return input_area
            if selector == "#magnet-output": return output_area
            return None
        self.tab.query_one = mock_query_one

        input_area.text = '{"xt": "urn:btih:b9968411c52112e4f0ddfc9a1e04e4c27b08dd97"}'
        event = Button.Pressed(Button(id="btn-build"))
        self.tab.on_button_pressed(event)

        self.assertEqual(output_area.text, "magnet:?xt=urn:btih:b9968411c52112e4f0ddfc9a1e04e4c27b08dd97")

if __name__ == '__main__':
    unittest.main()

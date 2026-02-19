import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock Textual components to avoid App context errors
mock_vertical = MagicMock()
mock_horizontal = MagicMock()
mock_static = MagicMock()

# Context manager support for Vertical/Horizontal
mock_vertical.__enter__ = MagicMock(return_value=mock_vertical)
mock_vertical.__exit__ = MagicMock(return_value=None)
mock_horizontal.__enter__ = MagicMock(return_value=mock_horizontal)
mock_horizontal.__exit__ = MagicMock(return_value=None)

# We need to patch these before importing ColorLabTab if possible,
# or patch where they are used. Since they are imported in tui_color.py,
# we should patch shared.tui_color.Vertical, etc.

from shared.tui_color import ColorLabTab

class TestColorLabTab(unittest.TestCase):
    def setUp(self):
        self.tab = ColorLabTab()
        self.tab.notify = MagicMock()

        # Mock query_one mechanism
        self.mock_widgets = {}
        def get_widget(selector, type=None):
            if selector not in self.mock_widgets:
                m = MagicMock()
                self.mock_widgets[selector] = m
            return self.mock_widgets[selector]
        self.tab.query_one = MagicMock(side_effect=get_widget)

    @patch('shared.tui_color.Vertical')
    @patch('shared.tui_color.Horizontal')
    @patch('shared.tui_color.Static')
    @patch('shared.tui_color.Color')
    def test_on_analyze_valid(self, MockColor, MockStatic, MockHorizontal, MockVertical):
        # Setup context managers
        MockVertical.return_value.__enter__.return_value = MagicMock()
        MockVertical.return_value.__exit__.return_value = None

        mock_color_instance = MockColor.return_value
        mock_color_instance.hex = "#FF0000"
        mock_color_instance.rgb = (255, 0, 0)
        mock_color_instance.hsl = (0, 100, 50)
        mock_color_instance.cmyk = (0, 100, 100, 0)
        mock_color_instance.luminance = 0.2126
        mock_color_instance.contrast_ratio.return_value = 1.0
        mock_color_instance.simulate_blindness.return_value = mock_color_instance

        self.tab.query_one("#color-input").value = "#FF0000"

        # Action
        self.tab.on_analyze()

        # Assert
        MockColor.assert_called_with("#FF0000")
        self.assertEqual(self.tab.current_color, mock_color_instance)

        self.tab.query_one("#color-swatch").update.assert_called()
        table = self.tab.query_one("#color-conversion-table")
        table.clear.assert_called()
        self.assertTrue(table.add_row.called)

    @patch('shared.tui_color.Color')
    def test_on_analyze_invalid(self, MockColor):
        MockColor.side_effect = ValueError("Invalid")
        self.tab.query_one("#color-input").value = "invalid"

        self.tab.on_analyze()

        self.tab.notify.assert_called_with("Invalid color format.", severity="error")

    @patch('shared.tui_color.Color')
    def test_on_update_bg(self, MockColor):
        mock_bg = MagicMock()
        mock_bg.hex = "#000000"
        MockColor.return_value = mock_bg

        self.tab.current_color = MagicMock()
        self.tab.current_color.contrast_ratio.return_value = 21.0

        self.tab.query_one("#bg-color-input").value = "#000000"

        self.tab.on_update_bg()

        self.assertEqual(self.tab.bg_color, mock_bg)
        self.tab.current_color.contrast_ratio.assert_called_with(mock_bg)
        self.tab.query_one("#contrast-ratio-lbl").update.assert_called()

    @patch('shared.tui_color.Horizontal')
    @patch('shared.tui_color.Static')
    def test_on_palette_btn(self, MockStatic, MockHorizontal):
        self.tab.current_color = MagicMock()
        palette_mock = [MagicMock(hex="#111111", luminance=0.1), MagicMock(hex="#222222", luminance=0.1)]
        self.tab.current_color.palette.return_value = palette_mock

        event = MagicMock()
        event.button.id = "btn-pal-comp"

        # Mock container
        container = self.tab.query_one("#palette-container")

        # Action
        self.tab.on_palette_btn(event)

        # Assert
        self.tab.current_color.palette.assert_called_with("complementary")
        container.remove_children.assert_called()
        # mount is called on container
        container.mount.assert_called()

if __name__ == "__main__":
    unittest.main()

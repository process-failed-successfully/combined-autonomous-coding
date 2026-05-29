import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.color_lab import Color


class TestColorLab(unittest.TestCase):
    def test_parsing(self):
        c = Color("#ffffff")
        self.assertEqual(c.rgb, (255, 255, 255))

        c = Color("ff0000")
        self.assertEqual(c.rgb, (255, 0, 0))

        c = Color("rgb(0, 255, 0)")
        self.assertEqual(c.rgb, (0, 255, 0))

    def test_luminance(self):
        black = Color("#000000")
        white = Color("#ffffff")
        self.assertAlmostEqual(black.luminance, 0.0)
        self.assertAlmostEqual(white.luminance, 1.0)

    def test_contrast_ratio(self):
        black = Color("#000000")
        white = Color("#ffffff")
        ratio = black.contrast_ratio(white)
        self.assertAlmostEqual(ratio, 21.0)

        ratio = white.contrast_ratio(white)
        self.assertAlmostEqual(ratio, 1.0)

    def test_palette(self):
        c = Color("#ff0000")
        p = c.palette("complementary")
        self.assertEqual(len(p), 2)

        p = c.palette("triadic")
        self.assertEqual(len(p), 3)

    def test_simulation(self):
        c = Color("#ff0000")
        sim = c.simulate_blindness("protanopia")
        self.assertIsInstance(sim, Color)
        # In protanopia, red (#ff0000) becomes much darker/brownish
        self.assertNotEqual(c.hex, sim.hex)

    def test_mix(self):
        c1 = Color("#000000")
        c2 = Color("#ffffff")

        # 50% mix
        mixed = c1.mix(c2, 0.5)
        self.assertEqual(mixed.rgb, (127, 127, 127))
        self.assertEqual(mixed.hex, "#7f7f7f")

        # 0% mix (should be c1)
        mixed = c1.mix(c2, 0.0)
        self.assertEqual(mixed.rgb, (0, 0, 0))

        # 100% mix (should be c2)
        mixed = c1.mix(c2, 1.0)
        self.assertEqual(mixed.rgb, (255, 255, 255))

    def test_cmyk(self):
        c = Color("#ff0000")  # Red
        # Cyan=0, Magenta=1, Yellow=1, Black=0
        self.assertEqual(c.cmyk, (0, 100, 100, 0))

        c = Color("#00ffff")  # Cyan
        # C=1, M=0, Y=0, K=0
        self.assertEqual(c.cmyk, (100, 0, 0, 0))

        c = Color("#000000")  # Black
        self.assertEqual(c.cmyk, (0, 0, 0, 100))

        c = Color("#ffffff")  # White
        self.assertEqual(c.cmyk, (0, 0, 0, 0))

    @patch("shared.color_lab.HAS_PIL", True)
    @patch("shared.color_lab.Image")
    def test_extract_palette(self, mock_image):
        from shared.color_lab import extract_palette_from_image

        mock_img_instance = MagicMock()
        mock_image.open.return_value.__enter__.return_value = mock_img_instance

        # Mock mode and convert
        mock_img_instance.mode = "RGB"
        mock_img_instance.convert.return_value = mock_img_instance

        # Mock quantize
        mock_q_img = MagicMock()
        mock_img_instance.quantize.return_value = mock_q_img

        # Mock getcolors (count, index)
        # Let's say we have 3 prominent colors
        mock_q_img.getcolors.return_value = [
            (100, 0),  # Most frequent, index 0
            (50, 1),   # Index 1
            (10, 2)    # Index 2
        ]

        # Mock getpalette (flat list of r,g,b)
        # Index 0: Red (255, 0, 0)
        # Index 1: Green (0, 255, 0)
        # Index 2: Blue (0, 0, 255)
        # Palette needs to be 768 items
        palette = [0] * 768
        palette[0:3] = [255, 0, 0]
        palette[3:6] = [0, 255, 0]
        palette[6:9] = [0, 0, 255]
        mock_q_img.getpalette.return_value = palette

        with patch.object(Path, "exists", return_value=True):
            colors = extract_palette_from_image("test.jpg", limit=2)

            self.assertEqual(len(colors), 2)
            self.assertEqual(colors[0].rgb, (255, 0, 0))
            self.assertEqual(colors[1].rgb, (0, 255, 0))


class TestColorLabCLI(unittest.TestCase):
    @patch("shared.tui.AgentTUI")
    @patch("main.sys.exit")
    def test_run_color_lab_tui(self, mock_exit, mock_agent_tui):
        from main import run_color_lab
        mock_exit.side_effect = SystemExit

        # Setup mock args
        args = MagicMock()
        args.action = "tui"
        args.project_dir = Path("/tmp/dummy")

        # Setup mock TUI app instance
        mock_app_instance = MagicMock()
        mock_agent_tui.return_value = mock_app_instance

        # Call the function
        with self.assertRaises(SystemExit):
            run_color_lab(args)

        # Assertions
        mock_agent_tui.assert_called_once_with(project_dir=Path("/tmp/dummy"), start_tab="tab-color")
        mock_app_instance.run.assert_called_once()
        mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()

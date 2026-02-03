import unittest
from shared.color_lab import ColorLabManager

class TestColorLab(unittest.TestCase):
    def setUp(self):
        self.manager = ColorLabManager()

    def test_parse_color_hex(self):
        self.assertEqual(self.manager.parse_color("#ff0000"), (255, 0, 0))
        self.assertEqual(self.manager.parse_color("#00FF00"), (0, 255, 0))
        self.assertEqual(self.manager.parse_color("#00f"), (0, 0, 255))
        self.assertEqual(self.manager.parse_color("ffffff"), (255, 255, 255))

    def test_parse_color_rgb(self):
        self.assertEqual(self.manager.parse_color("rgb(255, 0, 0)"), (255, 0, 0))
        self.assertEqual(self.manager.parse_color("255,0,0"), (255, 0, 0))
        self.assertEqual(self.manager.parse_color("255, 0, 0"), (255, 0, 0))

    def test_parse_color_hsl(self):
        # Red: hsl(0, 100%, 50%) -> rgb(255, 0, 0)
        self.assertEqual(self.manager.parse_color("hsl(0, 100%, 50%)"), (255, 0, 0))
        # White: hsl(0, 0%, 100%) -> rgb(255, 255, 255)
        self.assertEqual(self.manager.parse_color("hsl(0, 0%, 100%)"), (255, 255, 255))

    def test_parse_color_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.parse_color("invalid")
        with self.assertRaises(ValueError):
            self.manager.parse_color("#zzzzzz")

    def test_convert_format(self):
        res = self.manager.convert_format((255, 0, 0))
        self.assertEqual(res["hex"], "#ff0000")
        self.assertEqual(res["rgb"], "rgb(255, 0, 0)")
        self.assertEqual(res["hsl"], "hsl(0, 100%, 50%)")

    def test_calculate_contrast(self):
        # Black vs White = 21:1
        res = self.manager.calculate_contrast("#000000", "#ffffff")
        self.assertEqual(res["ratio"], 21.0)
        self.assertEqual(res["AA"], "Pass")
        self.assertEqual(res["AAA"], "Pass")

        # Red vs White = ~4.0:1 (Fail AA normal, Pass AA Large)
        # L(Red) ~ 0.2126
        # (1.05) / (0.2126 + 0.05) = 1.05 / 0.2626 = ~3.99
        res = self.manager.calculate_contrast("#ff0000", "#ffffff")
        self.assertTrue(3.9 <= res["ratio"] <= 4.1)
        self.assertEqual(res["AA"], "Pass (Large Text)")
        self.assertEqual(res["AAA"], "Fail")

    def test_simulate_blindness_protanopia(self):
        # Red should lose its redness
        res = self.manager.simulate_blindness("#ff0000", "protanopia")
        # 0.567 * 255 = ~144
        # 0.558 * 255 = ~142
        # 0.0 * 255 = 0
        r, g, b = self.manager.parse_color(res["hex"])
        self.assertAlmostEqual(r, 144, delta=2)
        self.assertAlmostEqual(g, 142, delta=2)
        self.assertAlmostEqual(b, 0, delta=2)

    def test_generate_palette_complementary(self):
        # Red -> Green (Cyan-ish)
        palette = self.manager.generate_palette("#ff0000", "complementary")
        self.assertEqual(len(palette), 2)
        self.assertEqual(palette[0]["hex"], "#ff0000")
        # 180 deg from 0 is 180 (Cyan) -> #00ffff
        self.assertEqual(palette[1]["hex"], "#00ffff")

    def test_generate_palette_analogous(self):
        palette = self.manager.generate_palette("#ff0000", "analogous")
        self.assertEqual(len(palette), 3)
        # Center is red
        self.assertEqual(palette[1]["hex"], "#ff0000")

    def test_generate_palette_triadic(self):
        palette = self.manager.generate_palette("#ff0000", "triadic")
        self.assertEqual(len(palette), 3)
        self.assertEqual(palette[0]["hex"], "#ff0000")
        # 0, 120 (Green), 240 (Blue)
        self.assertEqual(palette[1]["hex"], "#00ff00")
        self.assertEqual(palette[2]["hex"], "#0000ff")

if __name__ == "__main__":
    unittest.main()

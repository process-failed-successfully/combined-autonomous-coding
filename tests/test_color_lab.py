import unittest
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

if __name__ == '__main__':
    unittest.main()

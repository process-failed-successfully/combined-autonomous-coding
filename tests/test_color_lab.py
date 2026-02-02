import unittest
from shared.color_lab import Color, ColorLabManager

class TestColor(unittest.TestCase):
    def test_hex_parsing(self):
        c = Color("#ff0000")
        self.assertEqual(c.r, 255)
        self.assertEqual(c.g, 0)
        self.assertEqual(c.b, 0)

        c2 = Color("00ff00")
        self.assertEqual(c2.r, 0)
        self.assertEqual(c2.g, 255)
        self.assertEqual(c2.b, 0)

        c3 = Color("#00f")
        self.assertEqual(c3.r, 0)
        self.assertEqual(c3.g, 0)
        self.assertEqual(c3.b, 255)

    def test_luminance(self):
        # Black
        self.assertEqual(Color("#000000").luminance, 0.0)
        # White
        self.assertEqual(Color("#ffffff").luminance, 1.0)
        # Red (approx)
        self.assertAlmostEqual(Color("#ff0000").luminance, 0.2126, places=4)

    def test_invalid_hex(self):
        with self.assertRaises(ValueError):
            Color("zzzzzz")
        with self.assertRaises(ValueError):
            Color("12345")

class TestColorLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = ColorLabManager()

    def test_check_contrast(self):
        # Black vs White = 21:1
        res = self.manager.check_contrast("#000000", "#ffffff")
        self.assertEqual(res["ratio"], 21.0)
        self.assertEqual(res["aa"], "PASS")
        self.assertEqual(res["aaa"], "PASS")

        # White vs White = 1:1
        res = self.manager.check_contrast("#ffffff", "#ffffff")
        self.assertEqual(res["ratio"], 1.0)
        self.assertEqual(res["aa"], "FAIL")

    def test_generate_palette(self):
        pal = self.manager.generate_palette("#ff0000", "complementary")
        self.assertEqual(len(pal), 2)
        # Complement of red is cyan (#00ffff)
        self.assertEqual(pal[0], "#ff0000")
        self.assertEqual(pal[1], "#00ffff")

    def test_simulate_blindness(self):
        # Red in Protanopia (Red-blind) should look dark/yellowish
        sim = self.manager.simulate_blindness("#ff0000", "protanopia")
        # Exact values depend on matrix, but R component should drop significantly
        c = Color(sim)
        self.assertTrue(c.r < 150)

    def test_convert(self):
        res = self.manager.convert("#ff0000")
        self.assertEqual(res["hex"], "#ff0000")
        self.assertEqual(res["rgb"], "rgb(255, 0, 0)")
        self.assertEqual(res["hsl"], "hsl(0, 100%, 50%)")

if __name__ == "__main__":
    unittest.main()

import unittest
from shared.unit_lab import UnitLabManager

class TestUnitLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = UnitLabManager()

    def test_convert_storage(self):
        # 1 kb -> 1024 b
        self.assertEqual(self.manager.convert(1, "kb", "b"), "1024")
        # 1 mb -> 1024 kb
        self.assertEqual(self.manager.convert(1, "mb", "kb"), "1024")

    def test_convert_time(self):
        # 1 m -> 60 s
        self.assertEqual(self.manager.convert(1, "m", "s"), "60")
        # 1 h -> 60 m
        self.assertEqual(self.manager.convert(1, "h", "m"), "60")

    def test_convert_temperature(self):
        # 0 C -> 32 F
        self.assertEqual(self.manager.convert(0, "c", "f"), "32")
        # 100 C -> 212 F
        self.assertEqual(self.manager.convert(100, "c", "f"), "212")
        # 0 K -> -273.15 C
        self.assertEqual(self.manager.convert(0, "k", "c"), "-273.15")

    def test_convert_speed(self):
        # 1 m/s -> 3.6 km/h
        # m/s factor 1. km/h factor 0.277778
        # 1 * 1 / 0.277778 = 3.59999... -> 3.6
        res = float(self.manager.convert(1, "m/s", "km/h"))
        self.assertAlmostEqual(res, 3.6, places=1)

    def test_ambiguity_resolution(self):
        # 'm' can be meter or minute
        # m -> km (should be meter)
        self.assertEqual(self.manager.convert(1000, "m", "km"), "1")
        # m -> h (should be minute)
        self.assertEqual(self.manager.convert(60, "m", "h"), "1")

    def test_error_handling(self):
        self.assertTrue(self.manager.convert(1, "unknown", "b").startswith("Error"))
        self.assertTrue(self.manager.convert(1, "b", "unknown").startswith("Error"))
        self.assertTrue(self.manager.convert(1, "b", "c").startswith("Error")) # Storage to Temp

    def test_currency(self):
        # 1 USD -> 1 USD
        self.assertEqual(self.manager.convert(1, "usd", "usd"), "1")
        # Just check it returns a valid number string
        res = self.manager.convert(100, "usd", "eur")
        self.assertFalse(res.startswith("Error"))

    def test_get_categories(self):
        cats = self.manager.get_categories()
        self.assertIn("storage", cats)
        self.assertIn("temperature", cats)
        self.assertIn("speed", cats)

    def test_get_units_in_category(self):
        units = self.manager.get_units_in_category("temperature")
        self.assertIn("c", units)
        self.assertIn("fahrenheit", units)

    def test_list_units(self):
        # All units
        all_u = self.manager.list_units()
        self.assertIn("m", all_u)
        self.assertIn("c", all_u)
        self.assertIn("usd", all_u)

        # Specific category
        len_u = self.manager.list_units("length")
        self.assertIn("m", len_u)
        self.assertNotIn("c", len_u)

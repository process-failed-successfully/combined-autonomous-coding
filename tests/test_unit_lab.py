import unittest
from shared.unit_lab import UnitLabManager


class TestUnitLab(unittest.TestCase):
    def setUp(self):
        self.manager = UnitLabManager()

    def test_storage(self):
        # 1 KB = 1024 Bytes
        self.assertEqual(self.manager.convert(1, "kb", "bytes"), "1024")
        # 1 MB = 1024 KB
        self.assertEqual(self.manager.convert(1, "mb", "kb"), "1024")
        # 1 GB = 1024 MB
        self.assertEqual(self.manager.convert(1, "gb", "mb"), "1024")
        # 1024 Bytes = 1 KB
        self.assertEqual(self.manager.convert(1024, "bytes", "kb"), "1")

    def test_time(self):
        self.assertEqual(self.manager.convert(1, "min", "sec"), "60")
        self.assertEqual(self.manager.convert(60, "sec", "min"), "1")
        self.assertEqual(self.manager.convert(1, "h", "min"), "60")
        self.assertEqual(self.manager.convert(24, "h", "d"), "1")

    def test_length(self):
        self.assertEqual(self.manager.convert(1, "km", "m"), "1000")
        self.assertEqual(self.manager.convert(100, "cm", "m"), "1")
        # 1 inch = 2.54 cm
        res = self.manager.convert(1, "in", "cm")
        self.assertEqual(res, "2.54")

    def test_weight(self):
        self.assertEqual(self.manager.convert(1, "kg", "g"), "1000")
        # 1 lb approx 453.592
        res = self.manager.convert(1, "lb", "g")
        # Using startswith to handle slight precision variations if needed
        # In implementation: 453.59237 -> .4f -> 453.5924
        self.assertEqual(res, "453.5924")

    def test_temperature(self):
        # 0 C = 32 F
        self.assertEqual(self.manager.convert(0, "c", "f"), "32")
        # 100 C = 212 F
        self.assertEqual(self.manager.convert(100, "c", "f"), "212")
        # 0 K = -273.15 C
        self.assertEqual(self.manager.convert(0, "k", "c"), "-273.15")
        # 32 F = 0 C
        self.assertEqual(self.manager.convert(32, "f", "c"), "0")

    def test_ambiguity(self):
        # 'm' -> meter (Length) vs minute (Time)

        # 'm' to 'km' (Length context)
        self.assertEqual(self.manager.convert(1000, "m", "km"), "1")

        # 'm' to 'h' (Time context)
        self.assertEqual(self.manager.convert(60, "m", "h"), "1")

        # 'm' to 'm' (Same unit)
        self.assertEqual(self.manager.convert(1, "m", "m"), "1")

        # Explicit failure
        self.assertTrue(self.manager.convert(1, "kg", "m").startswith("Error"))

    def test_errors(self):
        self.assertTrue(self.manager.convert(1, "foo", "bar").startswith("Error"))
        self.assertTrue(self.manager.convert(1, "kg", "s").startswith("Error"))

    def test_list_units(self):
        all_units = self.manager.list_units()
        self.assertIn("kb", all_units)
        self.assertIn("min", all_units)

        storage = self.manager.list_units("storage")
        self.assertIn("mb", storage)
        self.assertNotIn("min", storage)


if __name__ == "__main__":
    unittest.main()

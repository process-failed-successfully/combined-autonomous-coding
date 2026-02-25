
import unittest
import sys
import os
from datetime import datetime, timezone

# Add repo root to path
sys.path.append(os.getcwd())

from shared.time_lab import TimeLabManager
from shared.tui_time import TimeLabTab

class TestTimeLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = TimeLabManager()

    def test_get_current_time(self):
        # Test UTC
        utc_time = self.manager.get_current_time("UTC")
        self.assertIn("T", utc_time)
        self.assertIn("+00:00", utc_time)

        # Test Invalid Zone
        invalid = self.manager.get_current_time("Invalid/Zone")
        self.assertTrue(invalid.startswith("Error"))

    def test_convert_time(self):
        # 2023-01-01 12:00:00 UTC -> EST (New_York)
        # EST is -5 hours from UTC
        src = "2023-01-01T12:00:00+00:00"
        dst_zone = "America/New_York"
        result = self.manager.convert_time(src, dst_zone)

        # Expect 07:00:00
        self.assertIn("07:00:00", result)
        self.assertIn("-05:00", result)

    def test_diff_time(self):
        t1 = "2023-01-01T10:00:00+00:00"
        t2 = "2023-01-01T12:30:00+00:00"
        diff = self.manager.diff_time(t1, t2)
        # 2 hours 30 mins
        self.assertEqual(diff, "2:30:00")

    def test_get_epoch(self):
        # 2023-01-01 00:00:00 UTC = 1672531200
        t = "2023-01-01T00:00:00+00:00"
        epoch = self.manager.get_epoch(t)
        self.assertEqual(float(epoch), 1672531200.0)

    def test_list_zones(self):
        zones = self.manager.list_zones("UTC")
        self.assertIn("UTC", zones)

    def test_get_common_timezones(self):
        common = self.manager.get_common_timezones()
        self.assertIsInstance(common, list)
        self.assertIn("UTC", common)
        self.assertIn("America/Los_Angeles", common)

    def test_parse_duration(self):
        # Seconds
        self.assertEqual(self.manager.parse_duration("30s"), 30)
        self.assertEqual(self.manager.parse_duration("10"), 10)

        # Minutes
        self.assertEqual(self.manager.parse_duration("5m"), 300)

        # Hours
        self.assertEqual(self.manager.parse_duration("1h"), 3600)

        # Combinations
        self.assertEqual(self.manager.parse_duration("1h 30m"), 5400)
        self.assertEqual(self.manager.parse_duration("1m 30s"), 90)
        self.assertEqual(self.manager.parse_duration("1h 1m 1s"), 3661)

        # Colon format
        self.assertEqual(self.manager.parse_duration("1:30"), 90) # 1m 30s
        self.assertEqual(self.manager.parse_duration("01:01:01"), 3661) # 1h 1m 1s

        # Invalid
        self.assertEqual(self.manager.parse_duration("invalid"), 0)
        self.assertEqual(self.manager.parse_duration(""), 0)

class TestTimeLabTab(unittest.TestCase):
    def test_instantiation(self):
        # Just check if we can create the widget without error
        try:
            tab = TimeLabTab()
            self.assertIsNotNone(tab)
        except Exception as e:
            self.fail(f"TimeLabTab instantiation failed: {e}")

if __name__ == '__main__':
    unittest.main()

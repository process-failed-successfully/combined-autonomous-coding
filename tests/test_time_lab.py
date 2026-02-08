import unittest
from datetime import datetime, timezone, timedelta
import zoneinfo
from shared.time_lab import TimeLabManager

class TestTimeLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = TimeLabManager()

    def test_get_current_time_utc(self):
        # We can't predict exact time, but we can check format and timezone
        time_str = self.manager.get_current_time("UTC")
        self.assertIn("T", time_str)
        # Should be parseable
        dt = datetime.fromisoformat(time_str)
        # Check offset is 0
        self.assertEqual(dt.tzinfo.utcoffset(dt), timedelta(0))

    def test_get_current_time_invalid_zone(self):
        result = self.manager.get_current_time("Invalid/Zone")
        self.assertTrue(result.startswith("Error: Timezone"))

    def test_convert_time_epoch_to_zone(self):
        # 1609459200 is 2021-01-01 00:00:00 UTC
        epoch = "1609459200"
        target_zone = "America/New_York"
        # NY is UTC-5 in Jan (Standard Time)
        expected_sub = "2020-12-31T19:00:00"

        result = self.manager.convert_time(epoch, target_zone)
        self.assertIn(expected_sub, result)
        self.assertIn("-05:00", result)

    def test_convert_time_iso_to_zone(self):
        # 2021-01-01 12:00:00 UTC
        iso_time = "2021-01-01T12:00:00+00:00"
        target_zone = "Europe/London"
        # London is UTC+0 in Jan

        result = self.manager.convert_time(iso_time, target_zone)
        # Should match time, offset might be Z or +00:00 depending on impl details of astimezone
        # but 12:00:00 should be preserved as it is same zone effectively
        self.assertIn("12:00:00", result)

    def test_diff_time(self):
        t1 = "2021-01-01T12:00:00+00:00"
        t2 = "2021-01-01T14:30:00+00:00"

        diff = self.manager.diff_time(t1, t2)
        self.assertEqual(diff, "2:30:00")

    def test_get_epoch(self):
        t1 = "2021-01-01T00:00:00+00:00"
        epoch = self.manager.get_epoch(t1)
        self.assertEqual(float(epoch), 1609459200.0)

    def test_list_zones(self):
        zones = self.manager.list_zones("New_York")
        self.assertIn("America/New_York", zones)

        all_zones = self.manager.list_zones()
        self.assertTrue(len(all_zones) > 100)

if __name__ == '__main__':
    unittest.main()

import unittest
import sys
import os
from pathlib import Path

# Add repo root to path
sys.path.append(os.getcwd())

from shared.snowflake_lab import SnowflakeManager
from shared.tui_snowflake import SnowflakeLabTab

class TestSnowflakeManager(unittest.TestCase):
    def setUp(self):
        self.manager = SnowflakeManager()

    def test_generate_and_parse(self):
        # Generate with specific worker ID and datacenter ID
        worker_id = 5
        datacenter_id = 10
        count = 3

        ids = self.manager.generate(count=count, worker_id=worker_id, datacenter_id=datacenter_id)

        self.assertEqual(len(ids), count)

        # We cannot assert exact sequence numbers (0, 1, 2) because if the clock
        # ticks to the next millisecond during generation, the sequence resets to 0.
        # Instead, we just verify they are all valid and have the correct machine IDs.
        for i, snowflake in enumerate(ids):
            parsed = self.manager.parse(snowflake)

            self.assertTrue(parsed["valid"])
            self.assertEqual(parsed["worker_id"], worker_id)
            self.assertEqual(parsed["datacenter_id"], datacenter_id)
            self.assertTrue(0 <= parsed["sequence"] <= 4095)
            self.assertEqual(parsed["epoch_used"], SnowflakeManager.DEFAULT_EPOCH)
            # Timestamp should be relatively recent relative to epoch, positive
            self.assertGreater(parsed["timestamp"], SnowflakeManager.DEFAULT_EPOCH)

        # Verify all IDs are strictly increasing and unique
        self.assertEqual(len(set(ids)), count)
        self.assertEqual(ids, sorted(ids))

    def test_invalid_parse(self):
        parsed = self.manager.parse(-1)
        self.assertFalse(parsed["valid"])
        self.assertEqual(parsed["error"], "Snowflake ID cannot be negative")

    def test_invalid_generate(self):
        with self.assertRaises(ValueError):
            self.manager.generate_one(worker_id=32)  # max is 31

        with self.assertRaises(ValueError):
            self.manager.generate_one(datacenter_id=-1)

    def test_custom_epoch(self):
        custom_epoch = 1577836800000  # 2020-01-01
        custom_manager = SnowflakeManager(epoch=custom_epoch)

        snowflake = custom_manager.generate_one()
        parsed = custom_manager.parse(snowflake)

        self.assertTrue(parsed["valid"])
        self.assertEqual(parsed["epoch_used"], custom_epoch)

class TestSnowflakeLabTab(unittest.TestCase):
    def test_instantiation(self):
        try:
            tab = SnowflakeLabTab()
            self.assertIsNotNone(tab)
        except Exception as e:
            self.fail(f"SnowflakeLabTab instantiation failed: {e}")

if __name__ == '__main__':
    unittest.main()

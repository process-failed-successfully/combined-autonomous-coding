import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import argparse
import sys
from collections import namedtuple

from shared.bandwidth_lab import BandwidthManager, run_bandwidth_lab_logic, _bytes_to_human

# Mock namedtuple for psutil.net_io_counters result
SNetIO = namedtuple('SNetIO', ['bytes_sent', 'bytes_recv', 'packets_sent', 'packets_recv', 'errin', 'errout', 'dropin', 'dropout'])

class TestBandwidthManager(unittest.TestCase):

    @patch('shared.bandwidth_lab.psutil')
    def test_get_io_counters_success(self, mock_psutil):
        mock_psutil.net_io_counters.return_value = {
            "eth0": SNetIO(100, 200, 10, 20, 0, 0, 0, 0)
        }
        manager = BandwidthManager()
        result = manager.get_io_counters()
        self.assertIn("eth0", result)
        self.assertEqual(result["eth0"].bytes_sent, 100)

    @patch('shared.bandwidth_lab.psutil')
    def test_get_io_counters_error(self, mock_psutil):
        mock_psutil.net_io_counters.side_effect = Exception("Permission denied")
        manager = BandwidthManager()
        result = manager.get_io_counters()
        self.assertIn("error", result)
        self.assertIn("Permission denied", result["error"])

    @patch('shared.bandwidth_lab.psutil')
    def test_get_interfaces(self, mock_psutil):
        mock_psutil.net_io_counters.return_value = {
            "eth0": SNetIO(0, 0, 0, 0, 0, 0, 0, 0),
            "lo": SNetIO(0, 0, 0, 0, 0, 0, 0, 0)
        }
        manager = BandwidthManager()
        ifaces = manager.get_interfaces()
        self.assertEqual(sorted(ifaces), ["eth0", "lo"])

    @patch('shared.bandwidth_lab.time')
    @patch('shared.bandwidth_lab.psutil')
    def test_monitor(self, mock_psutil, mock_time):
        # Mock time.sleep to do nothing
        mock_time.sleep.return_value = None
        # Mock time.time to increment by 1
        mock_time.time.side_effect = [1000, 1001, 1002]

        # First call (init), second call (loop 1)
        mock_psutil.net_io_counters.side_effect = [
            {"eth0": SNetIO(100, 200, 10, 20, 0, 0, 0, 0)},
            {"eth0": SNetIO(200, 400, 20, 40, 0, 0, 0, 0)}
        ]

        manager = BandwidthManager()
        # We need to manually break the generator loop, so we run it once manually
        gen = manager.monitor(interval=1)

        sample = next(gen)

        self.assertIn("timestamp", sample)
        self.assertIn("interfaces", sample)
        stats = sample["interfaces"]["eth0"]

        # Diff is 100 bytes sent, 200 recv over 1 sec (mocked)
        # Note: monitor logic divides by interval passed to function, not actual time diff
        self.assertEqual(stats["bytes_sent_sec"], 100.0)
        self.assertEqual(stats["bytes_recv_sec"], 200.0)
        self.assertEqual(stats["total_bytes_sent"], 200)

class TestBandwidthCLI(unittest.TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    @patch('shared.bandwidth_lab.BandwidthManager')
    def test_list_action(self, mock_manager_cls, mock_stdout):
        mock_instance = mock_manager_cls.return_value
        mock_instance.get_io_counters.return_value = {
            "eth0": SNetIO(1048576, 2097152, 0, 0, 0, 0, 0, 0)
        }

        args = argparse.Namespace(action="list")

        with self.assertRaises(SystemExit) as cm:
            run_bandwidth_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("eth0", output)
        self.assertIn("1.00 MB", output) # Sent
        self.assertIn("2.00 MB", output) # Recv

    @patch('sys.stdout', new_callable=StringIO)
    @patch('shared.bandwidth_lab.BandwidthManager')
    def test_monitor_action(self, mock_manager_cls, mock_stdout):
        mock_instance = mock_manager_cls.return_value
        # Mock monitor to yield one sample then raise StopIteration (simulate loop end)
        # But monitor is infinite loop, so we should raise KeyboardInterrupt or similar to break
        # OR just yield one item and have the loop logic handle it?
        # The loop in CLI is `for sample in manager.monitor...`
        # So we can just make it yield one item

        mock_instance.monitor.return_value = iter([
            {
                "timestamp": 1234567890,
                "interfaces": {
                    "eth0": {"bytes_sent_sec": 1024, "bytes_recv_sec": 2048}
                }
            }
        ])

        args = argparse.Namespace(action="monitor", interface=None, interval=1.0)

        # We need to simulate KeyboardInterrupt to exit loop gracefully?
        # No, the loop terminates when generator is exhausted.
        # But CLI loop `for sample in ...` will finish.
        # However, run_bandwidth_lab_logic doesn't exit explicitly after loop unless error.
        # Wait, looking at code: `except KeyboardInterrupt: sys.exit(0)`.
        # If loop finishes normally (which shouldn't happen in real monitor, but in test yes), it falls through.
        # But `run_bandwidth_lab_logic` does not have sys.exit(0) after loop?
        # Let's check code.
        # It just ends function if loop finishes.

        run_bandwidth_lab_logic(args)

        output = mock_stdout.getvalue()
        self.assertIn("Bandwidth Monitor", output)
        self.assertIn("eth0", output)
        self.assertIn("1.00 KB/s", output)

    def test_bytes_to_human(self):
        self.assertEqual(_bytes_to_human(500), "500.00 B/s")
        self.assertEqual(_bytes_to_human(1024), "1.00 KB/s")
        self.assertEqual(_bytes_to_human(1024*1024), "1.00 MB/s")

if __name__ == '__main__':
    unittest.main()

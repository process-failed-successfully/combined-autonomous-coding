import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import io

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.measure import BenchmarkRunner, run_measure_logic
from main import run_measure

class TestBenchmarkRunner(unittest.TestCase):
    def setUp(self):
        self.console_mock = MagicMock()
        self.runner = BenchmarkRunner(console=self.console_mock)

    @patch('shared.measure.Progress')
    @patch('subprocess.run')
    @patch('time.perf_counter')
    def test_run_single_command(self, mock_time, mock_subprocess, mock_progress):
        # Setup Progress mock to behave as context manager
        mock_progress_instance = mock_progress.return_value
        mock_progress_instance.__enter__.return_value = mock_progress_instance

        # Simulate time passing: 0, 0.1, 0.2, 0.35
        # We need to make sure we provide enough values if BenchmarkRunner calls it extra times,
        # but with mocked Progress, it should only call it inside the loop.
        mock_time.side_effect = [0.0, 0.1, 0.2, 0.35]

        results = self.runner.run(["echo test"], iterations=2, warmup=0)

        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.command, "echo test")
        self.assertEqual(len(res.runs), 2)
        self.assertAlmostEqual(res.runs[0], 0.1)
        self.assertAlmostEqual(res.runs[1], 0.15)
        self.assertAlmostEqual(res.mean, 0.125)

        self.assertEqual(mock_subprocess.call_count, 2)

    @patch('shared.measure.Progress')
    @patch('subprocess.run')
    def test_run_warmup(self, mock_subprocess, mock_progress):
        # Setup Progress mock
        mock_progress_instance = mock_progress.return_value
        mock_progress_instance.__enter__.return_value = mock_progress_instance

        self.runner.run(["echo test"], iterations=1, warmup=2)
        # 2 warmups + 1 run = 3 calls
        self.assertEqual(mock_subprocess.call_count, 3)

    @patch('shared.measure.Progress')
    @patch('subprocess.run')
    @patch('time.perf_counter')
    def test_compare_commands(self, mock_time, mock_subprocess, mock_progress):
        # Setup Progress mock
        mock_progress_instance = mock_progress.return_value
        mock_progress_instance.__enter__.return_value = mock_progress_instance

        # 2 commands, 1 iteration each
        # cmd1: 0.0 -> 0.1 (0.1s)
        # cmd2: 0.2 -> 0.4 (0.2s)
        mock_time.side_effect = [0.0, 0.1, 0.2, 0.4]

        results = self.runner.run(["cmd1", "cmd2"], iterations=1)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].command, "cmd1")
        self.assertAlmostEqual(results[0].mean, 0.1)
        self.assertEqual(results[1].command, "cmd2")
        self.assertAlmostEqual(results[1].mean, 0.2)

    def test_print_report(self):
        # Create dummy results
        from shared.measure import BenchmarkResult
        results = [
            BenchmarkResult("fast", 0.1, 0.1, 0.0, 0.1, 0.1, [0.1]),
            BenchmarkResult("slow", 0.2, 0.2, 0.0, 0.2, 0.2, [0.2])
        ]

        self.runner.print_report(results)

        # Verify console calls - specifically looking for table printing
        self.console_mock.print.assert_called()

class TestMeasureCLI(unittest.TestCase):
    @patch('shared.measure.BenchmarkRunner.run')
    @patch('shared.measure.BenchmarkRunner.print_report')
    def test_run_measure_logic(self, mock_print, mock_run):
        mock_run.return_value = []

        success = run_measure_logic(["echo test"], iterations=5, warmup=1)

        self.assertTrue(success)
        mock_run.assert_called_with(["echo test"], 5, 1)
        mock_print.assert_called()

    @patch('shared.measure.run_measure_logic')
    def test_main_run_measure(self, mock_logic):
        mock_logic.return_value = True
        args = MagicMock()
        args.commands = ["ls"]
        args.iterations = 10
        args.warmup = 0

        with self.assertRaises(SystemExit) as cm:
            run_measure(args)

        self.assertEqual(cm.exception.code, 0)
        mock_logic.assert_called_with(commands=["ls"], iterations=10, warmup=0)

if __name__ == '__main__':
    unittest.main()

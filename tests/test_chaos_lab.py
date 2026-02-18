import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.chaos import ChaosManager, NetworkLatencyExperiment, NetworkLossExperiment, NetworkResetExperiment

class TestChaosLab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.printer = MagicMock()
        self.manager = ChaosManager(self.project_dir, printer=self.printer)

    def test_manager_registration(self):
        """Test that new experiments are registered."""
        self.assertIn("network-latency", self.manager.experiments)
        self.assertIn("network-loss", self.manager.experiments)
        self.assertIn("network-reset", self.manager.experiments)

    @patch("shared.chaos.shutil.which")
    @patch("shared.chaos.subprocess.run")
    @patch("shared.chaos.time.sleep")
    def test_network_latency_run(self, mock_sleep, mock_run, mock_which):
        """Test NetworkLatency run."""
        mock_which.return_value = "/usr/sbin/tc"
        experiment = NetworkLatencyExperiment(self.project_dir, printer=self.printer)

        # Run
        result = experiment.run()

        self.assertTrue(result)

        # Verify tc calls
        # 1. Add latency (now using replace)
        mock_run.assert_any_call(
            ["sudo", "tc", "qdisc", "replace", "dev", "eth0", "root", "netem", "delay", "500ms", "50ms", "distribution", "normal"],
            check=True, capture_output=True, text=True
        )

        # 2. Cleanup (in finally)
        mock_run.assert_called_with(
            ["sudo", "tc", "qdisc", "del", "dev", "eth0", "root"],
            check=True, capture_output=True, text=True
        )

        # Verify sleep called
        mock_sleep.assert_called_with(30)

    @patch("shared.chaos.shutil.which")
    @patch("shared.chaos.subprocess.run")
    @patch("shared.chaos.time.sleep")
    def test_network_loss_run(self, mock_sleep, mock_run, mock_which):
        """Test NetworkLoss run."""
        mock_which.return_value = "/usr/sbin/tc"
        experiment = NetworkLossExperiment(self.project_dir, printer=self.printer)

        result = experiment.run()

        self.assertTrue(result)

        # Verify tc replace
        mock_run.assert_any_call(
            ["sudo", "tc", "qdisc", "replace", "dev", "eth0", "root", "netem", "loss", "10%"],
            check=True, capture_output=True, text=True
        )

        # Verify cleanup
        mock_run.assert_called_with(
            ["sudo", "tc", "qdisc", "del", "dev", "eth0", "root"],
            check=True, capture_output=True, text=True
        )

    @patch("shared.chaos.shutil.which")
    def test_tc_missing(self, mock_which):
        """Test that experiment fails gracefully if tc is missing."""
        mock_which.return_value = None
        experiment = NetworkLatencyExperiment(self.project_dir, printer=self.printer)

        result = experiment.run()

        self.assertFalse(result)
        self.printer.assert_any_call("❌ 'tc' command not found. Please install iproute2.")

    @patch("shared.chaos.shutil.which")
    @patch("shared.chaos.subprocess.run")
    def test_network_reset_run(self, mock_run, mock_which):
        """Test NetworkReset run."""
        mock_which.return_value = "/usr/sbin/tc"
        experiment = NetworkResetExperiment(self.project_dir, printer=self.printer)

        result = experiment.run()

        self.assertTrue(result)

        # Verify cleanup call only
        mock_run.assert_called_once_with(
            ["sudo", "tc", "qdisc", "del", "dev", "eth0", "root"],
            check=True, capture_output=True, text=True
        )

    @patch("shared.chaos.shutil.which")
    @patch("shared.chaos.subprocess.run")
    @patch("shared.chaos.time.sleep")
    def test_custom_interface(self, mock_sleep, mock_run, mock_which):
        """Test custom interface support."""
        mock_which.return_value = "/usr/sbin/tc"
        experiment = NetworkLatencyExperiment(self.project_dir, printer=self.printer, interface="wlan0")

        result = experiment.run()

        self.assertTrue(result)

        # Verify calls use wlan0
        mock_run.assert_any_call(
            ["sudo", "tc", "qdisc", "replace", "dev", "wlan0", "root", "netem", "delay", "500ms", "50ms", "distribution", "normal"],
            check=True, capture_output=True, text=True
        )

        mock_run.assert_called_with(
            ["sudo", "tc", "qdisc", "del", "dev", "wlan0", "root"],
            check=True, capture_output=True, text=True
        )

    @patch("shared.chaos.NetworkLatencyExperiment")
    def test_manager_run_with_interface(self, MockExperiment):
        mock_instance = MockExperiment.return_value
        mock_instance.name = "network-latency"
        mock_instance.description = "desc"

        # Instantiate manager here so it picks up the patched class
        manager = ChaosManager(self.project_dir, printer=self.printer)
        manager.run("network-latency", yes=True, interface="wlan0")

        # Verify instantiation
        MockExperiment.assert_called_with(
            self.project_dir, False, printer=self.printer, interface="wlan0"
        )

if __name__ == "__main__":
    unittest.main()

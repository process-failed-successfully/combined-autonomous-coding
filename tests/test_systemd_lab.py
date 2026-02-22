import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.systemd_lab import SystemdManager

class TestSystemdLab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/project")
        self.manager = SystemdManager(self.project_dir)

    def test_generate_unit_file(self):
        content = self.manager.generate_unit_file(
            name="myservice",
            command="/usr/bin/python3 main.py",
            user="appuser",
            working_dir="/app",
            description="My Test Service",
            environment={"ENV_VAR": "value"},
            restart_policy="on-failure"
        )

        expected_parts = [
            "[Unit]",
            "Description=My Test Service",
            "After=network.target",
            "[Service]",
            "Type=simple",
            "User=appuser",
            "WorkingDirectory=/app",
            "ExecStart=/usr/bin/python3 main.py",
            "Restart=on-failure",
            "Environment=ENV_VAR=value",
            "[Install]",
            "WantedBy=multi-user.target"
        ]

        for part in expected_parts:
            self.assertIn(part, content)

    @patch("subprocess.run")
    def test_list_units(self, mock_run):
        # Override path for consistent testing
        self.manager.systemctl_path = "/bin/systemctl"

        mock_output = """
service1.service loaded active running My Service 1
service2.service loaded active exited My Service 2
        """.strip()

        mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)

        units = self.manager.list_units()

        self.assertEqual(len(units), 2)
        self.assertEqual(units[0]["unit"], "service1.service")
        self.assertEqual(units[0]["active"], "active")
        self.assertEqual(units[1]["description"], "My Service 2")

    @patch("subprocess.run")
    def test_control_service_success(self, mock_run):
        # Override path for consistent testing
        self.manager.systemctl_path = "/bin/systemctl"

        mock_run.return_value = MagicMock(returncode=0, stdout="Success")

        success, msg = self.manager.control_service("myservice", "restart")

        self.assertTrue(success)
        self.assertIn("restarted successfully", msg)
        mock_run.assert_called_with(["/bin/systemctl", "restart", "myservice"], check=True, capture_output=True, text=True)

    @patch("subprocess.run")
    def test_control_service_failure(self, mock_run):
        self.manager.systemctl_path = "/bin/systemctl"

        # Simulate subprocess.CalledProcessError
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, ["cmd"], stderr="Access denied")

        success, msg = self.manager.control_service("myservice", "restart")

        self.assertFalse(success)
        self.assertIn("Failed to restart", msg)
        self.assertIn("Access denied", msg)

    @patch("subprocess.run")
    def test_get_logs(self, mock_run):
        self.manager.journalctl_path = "/bin/journalctl"

        mock_run.return_value = MagicMock(stdout="Log line 1\nLog line 2", returncode=0)

        logs = self.manager.get_logs("myservice", lines=10)

        self.assertEqual(logs, "Log line 1\nLog line 2")
        mock_run.assert_called()
        args = mock_run.call_args[0][0]
        self.assertIn("-n", args)
        self.assertIn("10", args)

if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch
from shared.cron2systemd_lab import Cron2SystemdManager, run_cron2systemd_lab_logic
import sys
from io import StringIO
from pathlib import Path

class TestCron2SystemdManager(unittest.TestCase):
    def setUp(self):
        self.manager = Cron2SystemdManager()

    def test_parse_cron_basic(self):
        parsed = self.manager.parse_cron("*/5 * * * * root /opt/backup.sh")
        self.assertEqual(parsed['on_calendar'], "*-*-* *:*/5:00")
        self.assertEqual(parsed['user'], "root")
        self.assertEqual(parsed['command'], "/opt/backup.sh")

    def test_parse_cron_no_user(self):
        parsed = self.manager.parse_cron("0 5 * * * /opt/backup.sh")
        self.assertEqual(parsed['on_calendar'], "*-*-* 5:0:00")
        self.assertEqual(parsed['user'], "root")
        self.assertEqual(parsed['command'], "/opt/backup.sh")

    def test_parse_cron_dow(self):
        parsed = self.manager.parse_cron("0 0 * * 1-5 root /bin/echo hello")
        self.assertEqual(parsed['on_calendar'], "Mon-Fri *-*-* 0:0:00")
        self.assertEqual(parsed['user'], "root")
        self.assertEqual(parsed['command'], "/bin/echo hello")

    def test_parse_cron_no_user_with_flags(self):
        parsed = self.manager.parse_cron("0 0 * * * /usr/bin/find /tmp -type f")
        self.assertEqual(parsed['on_calendar'], "*-*-* 0:0:00")
        self.assertEqual(parsed['user'], "root")
        self.assertEqual(parsed['command'], "/usr/bin/find /tmp -type f")

    def test_generate_files(self):
        service, timer = self.manager.generate_files("testjob", "0 0 1 1 * root /bin/test")

        self.assertIn("User=root", service)
        self.assertIn("ExecStart=/bin/test", service)

        self.assertIn("OnCalendar=*-1-1 0:0:00", timer)

class TestCron2SystemdCLI(unittest.TestCase):
    def test_convert_cli_stdout(self):
        args = MagicMock()
        args.action = "convert"
        args.cron_line = "0 5 * * * root /opt/backup.sh"
        args.name = "backup"
        args.description = ""
        args.out_dir = None
        args.tui = False

        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            result = run_cron2systemd_lab_logic(args)
            output = out.getvalue().strip()
            self.assertTrue(result)
            self.assertIn("--- backup.service ---", output)
            self.assertIn("ExecStart=/opt/backup.sh", output)
            self.assertIn("OnCalendar=*-*-* 5:0:00", output)
        finally:
            sys.stdout = saved_stdout

    @patch("shared.tui.AgentTUI")
    @patch("main.sys.exit")
    def test_tui_cli(self, mock_exit, mock_agent_tui):
        args = MagicMock()
        args.action = "tui"
        args.tui = True
        args._in_event_loop = False
        args.project_dir = Path("/tmp/dummy")

        mock_exit.side_effect = SystemExit

        mock_app_instance = MagicMock()
        mock_agent_tui.return_value = mock_app_instance

        with self.assertRaises(SystemExit):
            run_cron2systemd_lab_logic(args)

        mock_agent_tui.assert_called_once_with(project_dir=Path("/tmp/dummy"), start_tab="tab-cron2systemd")
        mock_app_instance.run.assert_called_once()

if __name__ == '__main__':
    unittest.main()

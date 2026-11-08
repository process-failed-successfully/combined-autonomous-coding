import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.syslog_lab import SyslogLabManager, run_syslog_lab_logic

class TestSyslogLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = SyslogLabManager()

    def test_parse_rfc3164(self):
        msg = "<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8"
        result = self.manager.parse(msg)
        self.assertEqual(result["type"], "RFC 3164")
        self.assertEqual(result["prival"], 34)
        self.assertEqual(result["facility"], 4)
        self.assertEqual(result["severity"], 2)
        self.assertEqual(result["timestamp"], "Oct 11 22:14:15")
        self.assertEqual(result["hostname"], "mymachine")
        self.assertEqual(result["tag"], "su")
        self.assertEqual(result["message"], "'su root' failed for lonvick on /dev/pts/8")

    def test_parse_rfc3164_with_pid(self):
        msg = "<13>Feb  5 17:32:18 10.0.0.99 Use the BFG[123]: this is a message"
        result = self.manager.parse(msg)
        self.assertEqual(result["type"], "RFC 3164")
        self.assertEqual(result["prival"], 13)
        self.assertEqual(result["timestamp"], "Feb  5 17:32:18")
        self.assertEqual(result["hostname"], "10.0.0.99")
        self.assertEqual(result["tag"], "Use the BFG")
        self.assertEqual(result["pid"], "123")
        self.assertEqual(result["message"], "this is a message")

    def test_parse_rfc5424(self):
        msg = '<165>1 2003-10-11T22:14:15.003Z mymachine.example.com evntslog - ID47 [exampleSDID@32473 iut="3" eventSource="Application" eventID="1011"] BOMAn application event log entry...'
        result = self.manager.parse(msg)
        self.assertEqual(result["type"], "RFC 5424")
        self.assertEqual(result["prival"], 165)
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["timestamp"], "2003-10-11T22:14:15.003Z")
        self.assertEqual(result["hostname"], "mymachine.example.com")
        self.assertEqual(result["appname"], "evntslog")
        self.assertEqual(result["procid"], "-")
        self.assertEqual(result["msgid"], "ID47")
        self.assertEqual(result["structured_data"], '[exampleSDID@32473 iut="3" eventSource="Application" eventID="1011"]')
        self.assertEqual(result["message"], "BOMAn application event log entry...")

    def test_parse_invalid(self):
        msg = "This is not a syslog message"
        result = self.manager.parse(msg)
        self.assertIn("error", result)

    @patch("sys.stdout")
    def test_cli_parse_message(self, mock_stdout):
        args = MagicMock()
        args.action = "parse"
        args.message = "<34>Oct 11 22:14:15 mymachine su: 'su root' failed"

        self.assertTrue(run_syslog_lab_logic(args))

    @patch("sys.stdin.isatty", return_value=True)
    @patch("sys.stderr")
    def test_cli_no_input(self, mock_stderr, mock_isatty):
        args = MagicMock()
        args.action = "parse"
        args.message = None
        self.assertFalse(run_syslog_lab_logic(args))

if __name__ == '__main__':
    unittest.main()

import unittest
import json
from unittest.mock import MagicMock
from shared.tui_syslog import SyslogLabTab

class TestSyslogLabTab(unittest.TestCase):
    def setUp(self):
        self.tab = SyslogLabTab()
        self.tab.manager = MagicMock()
        self.mock_input = MagicMock()
        self.mock_log = MagicMock()

        # Mock query_one
        def query_one_mock(selector, widget_type=None):
            if selector == "#syslog-input":
                return self.mock_input
            if selector == "#syslog-output":
                return self.mock_log
            raise ValueError(f"Unknown selector {selector}")

        self.tab.query_one = query_one_mock

    def test_on_parse_empty(self):
        self.mock_input.text = "   "
        event = MagicMock()
        self.tab.on_parse(event)

        self.mock_log.clear.assert_called_once()
        self.mock_log.write.assert_called_with("[red]Please enter a syslog message[/red]")

    def test_on_parse_valid(self):
        self.mock_input.text = "<34>Oct 11 22:14:15 mymachine su: 'su root' failed"
        self.tab.manager.parse.return_value = {"format": "RFC3164", "message": "hello"}

        event = MagicMock()
        self.tab.on_parse(event)

        self.tab.manager.parse.assert_called_with(self.mock_input.text)
        self.mock_log.write.assert_called_with(json.dumps({"format": "RFC3164", "message": "hello"}, indent=2))

    def test_on_parse_error(self):
        self.mock_input.text = "invalid"
        self.tab.manager.parse.side_effect = ValueError("Not a valid syslog message (missing <PRIVAL>)")

        event = MagicMock()
        self.tab.on_parse(event)

        from rich.markup import escape
        self.mock_log.write.assert_called_with(f"[red]Error:[/red] {escape('Not a valid syslog message (missing <PRIVAL>)')}")

if __name__ == "__main__":
    unittest.main()

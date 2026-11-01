import unittest
from shared.syslog_lab import SyslogLabManager

class TestSyslogLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = SyslogLabManager()

    def test_parse_priority(self):
        pri_data = self.manager.parse_priority(34)
        self.assertEqual(pri_data["prival"], 34)
        self.assertEqual(pri_data["facility_value"], 4)
        self.assertEqual(pri_data["facility"], "security/authorization messages")
        self.assertEqual(pri_data["severity_value"], 2)
        self.assertEqual(pri_data["severity"], "Critical: critical conditions")

    def test_parse_rfc5424(self):
        msg = "<34>1 2003-10-11T22:14:15.003Z mymachine.example.com su - ID47 - 'su root' failed for lonvick on /dev/pts/8"
        result = self.manager.parse(msg)
        self.assertEqual(result["format"], "RFC5424")
        self.assertEqual(result["version"], "1")
        self.assertEqual(result["timestamp"], "2003-10-11T22:14:15.003Z")
        self.assertEqual(result["hostname"], "mymachine.example.com")
        self.assertEqual(result["app_name"], "su")
        self.assertEqual(result["procid"], "-")
        self.assertEqual(result["msgid"], "ID47")
        self.assertEqual(result["structured_data"], "-")
        self.assertEqual(result["message"], "'su root' failed for lonvick on /dev/pts/8")

        pri = result["priority"]
        self.assertEqual(pri["prival"], 34)

    def test_parse_rfc3164_with_procid(self):
        msg = "<34>Oct 11 22:14:15 mymachine su[123]: 'su root' failed for lonvick on /dev/pts/8"
        result = self.manager.parse(msg)
        self.assertEqual(result["format"], "RFC3164")
        self.assertEqual(result["timestamp"], "Oct 11 22:14:15")
        self.assertEqual(result["hostname"], "mymachine")
        self.assertEqual(result["app_name"], "su")
        self.assertEqual(result["procid"], "123")
        self.assertEqual(result["message"], "'su root' failed for lonvick on /dev/pts/8")

    def test_parse_rfc3164_without_procid(self):
        msg = "<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8"
        result = self.manager.parse(msg)
        self.assertEqual(result["format"], "RFC3164")
        self.assertEqual(result["app_name"], "su")
        self.assertEqual(result["procid"], "-")

    def test_parse_unknown_format(self):
        msg = "<13>Something else entirely"
        result = self.manager.parse(msg)
        self.assertEqual(result["format"], "Unknown (Has Priority)")
        self.assertEqual(result["message"], "Something else entirely")

    def test_parse_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.parse("No priority string")

if __name__ == "__main__":
    unittest.main()

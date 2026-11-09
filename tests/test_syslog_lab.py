import unittest
from shared.syslog_lab import SyslogLabManager

class TestSyslogLab(unittest.TestCase):
    def setUp(self):
        self.manager = SyslogLabManager()

    def test_parse_rfc3164(self):
        message = "<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8"
        res = self.manager.parse(message)
        self.assertEqual(res["type"], "RFC 3164")
        self.assertEqual(res["pri"], 34)
        self.assertEqual(res["facility"], "security/authorization messages")
        self.assertEqual(res["severity"], "Critical")
        self.assertEqual(res["timestamp"], "Oct 11 22:14:15")
        self.assertEqual(res["hostname"], "mymachine")
        self.assertEqual(res["tag"], "su")
        self.assertEqual(res["pid"], None)
        self.assertEqual(res["message"], "'su root' failed for lonvick on /dev/pts/8")

    def test_parse_rfc3164_with_pid(self):
        message = "<34>Oct 11 22:14:15 mymachine su[123]: 'su root' failed for lonvick on /dev/pts/8"
        res = self.manager.parse(message)
        self.assertEqual(res["type"], "RFC 3164")
        self.assertEqual(res["pri"], 34)
        self.assertEqual(res["tag"], "su")
        self.assertEqual(res["pid"], "123")
        self.assertEqual(res["message"], "'su root' failed for lonvick on /dev/pts/8")

    def test_parse_rfc5424(self):
        message = '<165>1 2003-10-11T22:14:15.003Z mymachine.example.com evntslog - ID47 [exampleSDID@32473 iut="3" eventSource="Application" eventID="1011"] BOMAn application event log entry...'
        res = self.manager.parse(message)
        self.assertEqual(res["type"], "RFC 5424")
        self.assertEqual(res["pri"], 165)
        self.assertEqual(res["facility"], "local use 4")
        self.assertEqual(res["severity"], "Notice")
        self.assertEqual(res["version"], 1)
        self.assertEqual(res["timestamp"], "2003-10-11T22:14:15.003Z")
        self.assertEqual(res["hostname"], "mymachine.example.com")
        self.assertEqual(res["app_name"], "evntslog")
        self.assertEqual(res["procid"], None)
        self.assertEqual(res["msgid"], "ID47")
        self.assertEqual(res["structured_data"], '[exampleSDID@32473 iut="3" eventSource="Application" eventID="1011"]')
        self.assertEqual(res["message"], "BOMAn application event log entry...")

    def test_parse_rfc5424_no_structured_data(self):
        message = '<165>1 2003-10-11T22:14:15.003Z mymachine.example.com evntslog - ID47 - BOMAn application event log entry...'
        res = self.manager.parse(message)
        self.assertEqual(res["type"], "RFC 5424")
        self.assertEqual(res["structured_data"], None)

    def test_parse_unknown(self):
        message = '<13>Something else that does not match RFC 3164 or 5424.'
        res = self.manager.parse(message)
        self.assertEqual(res["type"], "Unknown")
        self.assertEqual(res["pri"], 13)
        self.assertEqual(res["message"], "Something else that does not match RFC 3164 or 5424.")

    def test_invalid_syslog(self):
        with self.assertRaises(ValueError):
            self.manager.parse("invalid message")

        with self.assertRaises(ValueError):
            self.manager.parse("<invalid>message")

        with self.assertRaises(ValueError):
            self.manager.parse("<>message")

if __name__ == '__main__':
    unittest.main()

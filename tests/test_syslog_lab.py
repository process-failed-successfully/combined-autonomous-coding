import unittest
from shared.syslog_lab import SyslogLabManager

class TestSyslogLab(unittest.TestCase):
    def setUp(self):
        self.manager = SyslogLabManager()

    def test_rfc3164_parse(self):
        msg = "<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8"
        parsed = self.manager.parse_syslog(msg)
        self.assertEqual(parsed["format"], "RFC3164")
        self.assertEqual(parsed["pri"], "34")
        self.assertEqual(parsed["timestamp"], "Oct 11 22:14:15")
        self.assertEqual(parsed["hostname"], "mymachine")
        self.assertEqual(parsed["appname"], "su")
        self.assertEqual(parsed["msg"], "'su root' failed for lonvick on /dev/pts/8")
        self.assertEqual(parsed["facility"], 4)
        self.assertEqual(parsed["severity"], 2)

    def test_rfc5424_parse(self):
        msg = "<165>1 2003-10-11T22:14:15.003Z mymachine.example.com evntslog - ID47 [exampleSDID@32473 iut=\"3\" eventSource=\"Application\" eventID=\"1011\"] BOMAn application event log entry..."
        parsed = self.manager.parse_syslog(msg)
        self.assertEqual(parsed["format"], "RFC5424")
        self.assertEqual(parsed["pri"], "165")
        self.assertEqual(parsed["version"], "1")
        self.assertEqual(parsed["timestamp"], "2003-10-11T22:14:15.003Z")
        self.assertEqual(parsed["hostname"], "mymachine.example.com")
        self.assertEqual(parsed["appname"], "evntslog")
        self.assertEqual(parsed["procid"], None)
        self.assertEqual(parsed["msgid"], "ID47")
        self.assertTrue(parsed["structured_data"].startswith("[exampleSDID@32473"))
        self.assertEqual(parsed["msg"], "BOMAn application event log entry...")
        self.assertEqual(parsed["facility"], 20)
        self.assertEqual(parsed["severity"], 5)

if __name__ == '__main__':
    unittest.main()

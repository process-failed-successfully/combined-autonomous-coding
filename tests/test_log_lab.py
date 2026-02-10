import unittest
import json
from shared.log_lab import LogParser, LogAnalyzer

class TestLogLab(unittest.TestCase):
    def setUp(self):
        self.parser = LogParser()
        self.analyzer = LogAnalyzer()

    def test_parse_json(self):
        line = '{"level": "INFO", "message": "test", "timestamp": "2023-01-01"}'
        parsed = self.parser.parse(line, "json")
        self.assertEqual(parsed['level'], "INFO")
        self.assertEqual(parsed['message'], "test")

    def test_parse_clf(self):
        line = '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326'
        parsed = self.parser.parse(line, "clf")
        self.assertEqual(parsed['ip'], "127.0.0.1")
        self.assertEqual(parsed['user'], "frank")
        self.assertEqual(parsed['method'], "GET")
        self.assertEqual(parsed['status'], 200)
        self.assertEqual(parsed['size'], 2326)

    def test_parse_syslog(self):
        line = 'Oct 11 22:14:15 mymachine su: \'su root\' failed for lonvick on /dev/pts/8'
        parsed = self.parser.parse(line, "syslog")
        self.assertEqual(parsed['timestamp'], "Oct 11 22:14:15")
        self.assertEqual(parsed['hostname'], "mymachine")
        self.assertEqual(parsed['process'], "su")
        self.assertIn("failed for lonvick", parsed['message'])

    def test_parse_kv(self):
        line = 'level=info msg="something happened" user=123'
        parsed = self.parser.parse(line, "kv")
        self.assertEqual(parsed['level'], "info")
        self.assertEqual(parsed['msg'], "something happened")
        self.assertEqual(parsed['user'], "123")

    def test_parse_auto(self):
        # JSON
        self.assertTrue(self.parser.parse('{"a":1}', "auto") is not None)
        # CLF
        self.assertTrue(self.parser.parse('127.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "GET / HTTP/1.0" 200 123', "auto") is not None)
        # KV
        parsed = self.parser.parse('key=value', "auto")
        self.assertEqual(parsed['key'], 'value')

    def test_filter_logs(self):
        logs = [
            {"level": "INFO", "msg": "hello"},
            {"level": "ERROR", "msg": "oops"},
            {"level": "WARN", "msg": "careful"}
        ]

        # Filter by level
        filtered = list(self.analyzer.filter_logs((l for l in logs), level="ERROR"))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['level'], "ERROR")

        # Filter by keyword
        filtered = list(self.analyzer.filter_logs((l for l in logs), keyword="careful"))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['level'], "WARN")

    def test_stats(self):
        logs = [
            {"status": 200},
            {"status": 200},
            {"status": 404},
            {"status": 500}
        ]
        stats = self.analyzer.get_stats((l for l in logs), group_by="status")
        # Should be [('200', 2), ('404', 1), ('500', 1)]
        self.assertEqual(stats[0], ('200', 2))
        self.assertEqual(len(stats), 3)

if __name__ == '__main__':
    unittest.main()

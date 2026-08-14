import unittest
from unittest.mock import patch, MagicMock
import io
import json
from pathlib import Path
import tempfile
import os
from shared.extract_lab import ExtractLabManager, run_extract_lab_logic

class TestExtractLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = ExtractLabManager()

    def test_extract_ipv4(self):
        text = "My local IP is 192.168.0.1 and DNS is 8.8.8.8, invalid is 256.0.0.1."
        matches = self.manager.extract(text, "ipv4")
        self.assertEqual(matches, ["192.168.0.1", "8.8.8.8"])

    def test_extract_ipv6(self):
        text = "Loopback is ::1 and another is 2001:0db8:85a3:0000:0000:8a2e:0370:7334."
        matches = self.manager.extract(text, "ipv6")
        self.assertIn("::1", matches)
        self.assertIn("2001:0db8:85a3:0000:0000:8a2e:0370:7334", matches)

    def test_extract_email(self):
        text = "Contact us at support@example.com or sales-info@company.co.uk."
        matches = self.manager.extract(text, "email")
        self.assertEqual(matches, ["support@example.com", "sales-info@company.co.uk"])

    def test_extract_url(self):
        text = "Visit https://www.google.com or http://localhost:8080/api/v1?query=test."
        matches = self.manager.extract(text, "url")
        self.assertEqual(matches, ["https://www.google.com", "http://localhost:8080/api/v1?query=test"])

    def test_extract_mac(self):
        text = "MACs: 00:1A:2B:3C:4D:5E and aa-bb-cc-dd-ee-ff."
        matches = self.manager.extract(text, "mac")
        # Depending on regex boundaries, they should be exact
        self.assertEqual(len(matches), 2)
        self.assertIn("00:1A:2B:3C:4D:5E", matches)
        self.assertIn("aa-bb-cc-dd-ee-ff", matches)

    def test_extract_hashes(self):
        text = "MD5: d41d8cd98f00b204e9800998ecf8427e, SHA1: da39a3ee5e6b4b0d3255bfef95601890afd80709"
        md5s = self.manager.extract(text, "md5")
        sha1s = self.manager.extract(text, "sha1")
        self.assertEqual(md5s, ["d41d8cd98f00b204e9800998ecf8427e"])
        self.assertEqual(sha1s, ["da39a3ee5e6b4b0d3255bfef95601890afd80709"])

    def test_extract_uuid(self):
        text = "ID: 123e4567-e89b-12d3-a456-426614174000"
        matches = self.manager.extract(text, "uuid")
        self.assertEqual(matches, ["123e4567-e89b-12d3-a456-426614174000"])

    def test_extract_creditcard(self):
        text = "Card: 1234-5678-9012-3456 and 4111 1111 1111 1111."
        matches = self.manager.extract(text, "creditcard")
        self.assertEqual(matches, ["1234567890123456", "4111111111111111"])

    def test_extract_all(self):
        text = "IP: 10.0.0.1, Email: test@test.com"
        results = self.manager.extract_all(text)
        self.assertIn("ipv4", results)
        self.assertEqual(results["ipv4"], ["10.0.0.1"])
        self.assertIn("email", results)
        self.assertEqual(results["email"], ["test@test.com"])
        self.assertIn("domain", results) # test.com will match as domain too

    def test_extract_unknown_type(self):
        with self.assertRaises(ValueError):
            self.manager.extract("test", "unknown_type")

class TestExtractLabCLI(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_extract_type(self, mock_stdout):
        args = MagicMock()
        args.text = "IP: 1.1.1.1 and 1.1.1.1"
        args.type = "ipv4"
        args.unique = True
        args.json = False
        args.file = None
        args.tui = False

        with self.assertRaises(SystemExit) as cm:
            run_extract_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("1.1.1.1", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_extract_all_json(self, mock_stdout):
        args = MagicMock()
        args.text = "IP: 1.1.1.1, Email: a@b.com"
        args.type = "all"
        args.unique = True
        args.json = True
        args.file = None
        args.tui = False

        with self.assertRaises(SystemExit) as cm:
            run_extract_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        parsed = json.loads(output)
        self.assertIn("ipv4", parsed)
        self.assertEqual(parsed["ipv4"], ["1.1.1.1"])
        self.assertIn("email", parsed)
        self.assertEqual(parsed["email"], ["a@b.com"])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_extract_file(self, mock_stdout):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Contact abc@def.com")
            temp_name = f.name

        try:
            args = MagicMock()
            args.text = None
            args.file = temp_name
            args.type = "email"
            args.unique = True
            args.json = False
            args.tui = False

            with self.assertRaises(SystemExit) as cm:
                run_extract_lab_logic(args)

            self.assertEqual(cm.exception.code, 0)
            self.assertIn("abc@def.com", mock_stdout.getvalue())
        finally:
            os.remove(temp_name)

if __name__ == '__main__':
    unittest.main()

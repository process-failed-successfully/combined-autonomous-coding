import unittest
from shared.extract_lab import ExtractLabManager

class TestExtractLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = ExtractLabManager()

    def test_extract_ips(self):
        text = "Here is an IP 192.168.1.1 and another 10.0.0.1, plus a duplicate 192.168.1.1."
        results = self.manager.extract_iocs(text)

        self.assertEqual(len(results["ips"]), 2)
        self.assertIn("192.168.1.1", results["ips"])
        self.assertIn("10.0.0.1", results["ips"])

    def test_extract_urls(self):
        text = "Check out https://github.com and http://example.com/page?query=1. Invalid url htp://bad."
        results = self.manager.extract_iocs(text)

        self.assertEqual(len(results["urls"]), 2)
        self.assertIn("https://github.com", results["urls"])
        self.assertIn("http://example.com/page?query=1.", results["urls"]) # Note regex includes trailing punctuation optionally depending on what matches

    def test_extract_emails(self):
        text = "Contact me at user@example.com or admin@test.org."
        results = self.manager.extract_iocs(text)

        self.assertEqual(len(results["emails"]), 2)
        self.assertIn("user@example.com", results["emails"])
        self.assertIn("admin@test.org", results["emails"])

    def test_extract_hashes(self):
        text = "MD5: d41d8cd98f00b204e9800998ecf8427e\nSHA1: da39a3ee5e6b4b0d3255bfef95601890afd80709\nSHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        results = self.manager.extract_iocs(text)

        self.assertEqual(len(results["hashes"]), 3)
        self.assertIn("d41d8cd98f00b204e9800998ecf8427e", results["hashes"])
        self.assertIn("da39a3ee5e6b4b0d3255bfef95601890afd80709", results["hashes"])
        self.assertIn("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", results["hashes"])

    def test_empty_or_no_iocs(self):
        text = "Just some plain text without any indicators."
        results = self.manager.extract_iocs(text)
        self.assertEqual(len(results["ips"]), 0)
        self.assertEqual(len(results["urls"]), 0)
        self.assertEqual(len(results["emails"]), 0)
        self.assertEqual(len(results["hashes"]), 0)

if __name__ == '__main__':
    unittest.main()

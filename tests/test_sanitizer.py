import unittest
import tempfile
import shutil
from pathlib import Path
from shared.sanitizer import Sanitizer

class TestSanitizer(unittest.TestCase):
    def setUp(self):
        self.sanitizer = Sanitizer(salt="test_salt")
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_sanitize_email(self):
        text = "Contact alice@example.com for more info."
        sanitized = self.sanitizer.sanitize_text(text)
        self.assertNotEqual(text, sanitized)
        self.assertIn("@sanitized.com", sanitized)
        self.assertNotIn("alice@example.com", sanitized)

        # Test consistency
        text2 = "Contact alice@example.com again."
        sanitized2 = self.sanitizer.sanitize_text(text2)
        # Extract email from both
        email1 = sanitized.split(" ")[1]
        email2 = sanitized2.split(" ")[1]
        self.assertEqual(email1, email2)

    def test_sanitize_ipv4(self):
        text = "Server at 192.168.1.1 is down."
        sanitized = self.sanitizer.sanitize_text(text)
        self.assertNotEqual(text, sanitized)
        self.assertRegex(sanitized, r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}")

    def test_sanitize_phone(self):
        text = "Call 123-456-7890 now."
        sanitized = self.sanitizer.sanitize_text(text)
        self.assertNotEqual(text, sanitized)
        self.assertRegex(sanitized, r"555-01\d{2}")

    def test_sanitize_ssn(self):
        text = "SSN: 123-45-6789."
        sanitized = self.sanitizer.sanitize_text(text)
        self.assertNotEqual(text, sanitized)
        self.assertRegex(sanitized, r"000-00-\d{4}")

    def test_sanitize_cc(self):
        text = "CC: 1234-5678-9012-3456"
        sanitized = self.sanitizer.sanitize_text(text)
        self.assertNotEqual(text, sanitized)
        self.assertRegex(sanitized, r"4000 0000 0000 \d{4}")

    def test_check_text(self):
        text = "alice@example.com and 192.168.1.1"
        detected = self.sanitizer.check_text(text)
        self.assertIn("EMAIL", detected)
        self.assertIn("IPV4", detected)
        self.assertNotIn("SSN", detected)

    def test_sanitize_file(self):
        f = self.test_dir / "data.txt"
        f.write_text("User: bob@example.com\nIP: 10.0.0.1")

        changed, msg = self.sanitizer.sanitize_file(f)
        self.assertTrue(changed)

        content = f.read_text()
        self.assertNotIn("bob@example.com", content)
        self.assertNotIn("10.0.0.1", content)
        self.assertIn("@sanitized.com", content)

    def test_sanitize_file_dry_run(self):
        f = self.test_dir / "data.txt"
        original = "User: bob@example.com"
        f.write_text(original)

        changed, msg = self.sanitizer.sanitize_file(f, dry_run=True)
        self.assertTrue(changed)
        self.assertEqual(f.read_text(), original)

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch
import io
import time
from shared.otp_lab import OtpLabManager, run_otp_lab_logic
import argparse


class TestOtpLab(unittest.TestCase):
    def setUp(self):
        self.manager = OtpLabManager()

    def test_generate_secret(self):
        secret = self.manager.generate_secret(length=16)
        self.assertEqual(len(secret), 16)
        # Check if base32 characters
        valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
        self.assertTrue(all(c in valid_chars for c in secret))

    def test_generate_totp_consistency(self):
        secret = "JBSWY3DPEHPK3PXP"  # Base32 for "Hello!"
        # Fixed timestamp
        timestamp = 1000000000
        code1 = self.manager.generate_totp(secret, timestamp=timestamp)
        code2 = self.manager.generate_totp(secret, timestamp=timestamp)
        self.assertEqual(code1, code2)
        self.assertTrue(code1.isdigit())
        self.assertEqual(len(code1), 6)

    def test_verify_totp(self):
        secret = self.manager.generate_secret()
        code = self.manager.generate_totp(secret)
        self.assertTrue(self.manager.verify_totp(secret, code))

    def test_verify_totp_window(self):
        secret = self.manager.generate_secret()
        # Generate code for 30 seconds ago (previous interval)
        past_timestamp = time.time() - 30
        code = self.manager.generate_totp(secret, timestamp=past_timestamp)

        # Should verify with window=1
        self.assertTrue(self.manager.verify_totp(secret, code, window=1))

    def test_generate_url(self):
        secret = "JBSWY3DPEHPK3PXP"
        label = "user@example.com"
        issuer = "MyApp"
        url = self.manager.generate_url(secret, label, issuer)
        self.assertIn("otpauth://totp/", url)
        self.assertIn("secret=JBSWY3DPEHPK3PXP", url)
        self.assertIn("issuer=MyApp", url)
        self.assertIn("MyApp%3Auser%40example.com", url)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_generate(self, mock_stdout):
        args = argparse.Namespace(action="generate", length=16)
        run_otp_lab_logic(args)
        output = mock_stdout.getvalue()
        self.assertIn("Secret:", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_code(self, mock_stdout):
        secret = "JBSWY3DPEHPK3PXP"
        args = argparse.Namespace(action="code", secret=secret, interval=30, digits=6)
        run_otp_lab_logic(args)
        output = mock_stdout.getvalue().strip()
        self.assertTrue(output.isdigit())
        self.assertEqual(len(output), 6)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_verify_valid(self, mock_stdout):
        secret = "JBSWY3DPEHPK3PXP"
        code = self.manager.generate_totp(secret)
        args = argparse.Namespace(action="verify", secret=secret, code=code, window=1)

        with self.assertRaises(SystemExit) as cm:
            run_otp_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("VALID", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_verify_invalid(self, mock_stdout):
        secret = "JBSWY3DPEHPK3PXP"
        code = "000000"
        args = argparse.Namespace(action="verify", secret=secret, code=code, window=1)

        with self.assertRaises(SystemExit) as cm:
            run_otp_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("INVALID", mock_stdout.getvalue())

    def test_generate_secret_exact_length(self):
        # Test non-standard lengths to ensure exact output
        # Length 10 -> 7 bytes (56 bits) -> 11.2 chars -> 10 chars sliced
        secret_10 = self.manager.generate_secret(length=10)
        self.assertEqual(len(secret_10), 10)

        # Length 20 -> 13 bytes (104 bits) -> 20.8 chars -> 20 chars sliced
        secret_20 = self.manager.generate_secret(length=20)
        self.assertEqual(len(secret_20), 20)


if __name__ == '__main__':
    unittest.main()

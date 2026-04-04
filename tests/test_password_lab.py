import unittest
import string
from shared.password_lab import PasswordLabManager, run_password_lab_logic
import io
import sys
from unittest.mock import patch

class TestPasswordLab(unittest.TestCase):
    def setUp(self):
        self.manager = PasswordLabManager()

    def test_generate_length(self):
        pwd = self.manager.generate(length=20)
        self.assertEqual(len(pwd), 20)

    def test_generate_charset(self):
        # Only digits
        pwd = self.manager.generate(length=50, use_upper=False, use_lower=False, use_digits=True, use_symbols=False)
        self.assertTrue(all(c in string.digits for c in pwd))
        self.assertTrue(any(c in string.digits for c in pwd)) # Should ensure at least one

        # Only upper
        pwd = self.manager.generate(length=50, use_upper=True, use_lower=False, use_digits=False, use_symbols=False)
        self.assertTrue(all(c in string.ascii_uppercase for c in pwd))

    def test_generate_constraints(self):
        # Default should include all
        pwd = self.manager.generate(length=100)
        has_upper = any(c.isupper() for c in pwd)
        has_lower = any(c.islower() for c in pwd)
        has_digit = any(c.isdigit() for c in pwd)
        has_symbol = any(c in string.punctuation for c in pwd)

        self.assertTrue(has_upper)
        self.assertTrue(has_lower)
        self.assertTrue(has_digit)
        self.assertTrue(has_symbol)

    def test_generate_passphrase_length_and_separator(self):
        # Default generator
        pwd = self.manager.generate_passphrase()
        # Default is 4 words separated by hyphen -> 3 hyphens
        self.assertEqual(pwd.count("-"), 3)
        self.assertEqual(len(pwd.split("-")), 4)

        # Custom words and separator
        pwd2 = self.manager.generate_passphrase(words=6, separator=" ")
        self.assertEqual(pwd2.count(" "), 5)
        self.assertEqual(len(pwd2.split(" ")), 6)

    def test_generate_passphrase_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.generate_passphrase(words=0)

    def test_check_strength(self):
        # Weak
        res = self.manager.check_strength("12345")
        self.assertLess(res['score'], 2)
        self.assertIn("Password is too short.", res['feedback'])

        # Common
        res = self.manager.check_strength("password")
        self.assertEqual(res['score'], 0)

        # Strong
        res = self.manager.check_strength("Correct-Horse-Battery-Staple-123!")
        self.assertGreaterEqual(res['score'], 3)

    def test_hash_pbkdf2(self):
        hashed = self.manager.hash_password("mysecret", algo="pbkdf2", salt="somesalt")
        self.assertTrue(hashed.startswith("$pbkdf2-sha256$somesalt$"))

    def test_hash_scrypt(self):
        try:
            import cryptography
            hashed = self.manager.hash_password("mysecret", algo="scrypt", salt="somesalt")
            self.assertTrue(hashed.startswith("$scrypt$somesalt$"))
        except ImportError:
            print("Skipping scrypt test: cryptography not installed")

    def test_hash_bcrypt(self):
        try:
            import bcrypt
            hashed = self.manager.hash_password("mysecret", algo="bcrypt")
            self.assertTrue(hashed.startswith("$2") or hashed.startswith("$2a$") or hashed.startswith("$2b$") or hashed.startswith("$2y$"))
        except ImportError:
            print("Skipping bcrypt test: bcrypt not installed")

    def test_verify_password(self):
        pwd = "supersecretpassword123!"

        # test pbkdf2
        hashed_pbkdf2 = self.manager.hash_password(pwd, algo="pbkdf2")
        self.assertTrue(self.manager.verify_password(pwd, hashed_pbkdf2))
        self.assertFalse(self.manager.verify_password("wrong", hashed_pbkdf2))

        # test scrypt
        try:
            import cryptography
            hashed_scrypt = self.manager.hash_password(pwd, algo="scrypt")
            self.assertTrue(self.manager.verify_password(pwd, hashed_scrypt))
            self.assertFalse(self.manager.verify_password("wrong", hashed_scrypt))
        except ImportError:
            pass

        # test bcrypt
        try:
            import bcrypt
            hashed_bcrypt = self.manager.hash_password(pwd, algo="bcrypt")
            self.assertTrue(self.manager.verify_password(pwd, hashed_bcrypt))
            self.assertFalse(self.manager.verify_password("wrong", hashed_bcrypt))
        except ImportError:
            pass


    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_password_lab_logic_passphrase(self, mock_stdout):
        class Args:
            action = "passphrase"
            words = 5
            separator = "_"

        run_password_lab_logic(Args())

        output = mock_stdout.getvalue().strip()
        self.assertEqual(output.count("_"), 4)

import unittest
import string
from shared.password_lab import PasswordLabManager

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

if __name__ == '__main__':
    unittest.main()

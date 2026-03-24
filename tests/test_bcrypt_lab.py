import unittest
import argparse
from shared.bcrypt_lab import BcryptLabManager, run_bcrypt_lab_logic

class TestBcryptLab(unittest.TestCase):
    def setUp(self):
        self.manager = BcryptLabManager()

    def test_hash_password(self):
        password = "mysecretpassword"
        hashed = self.manager.hash_password(password, rounds=4)
        self.assertTrue(hashed.startswith("$2b$04$"))

    def test_verify_password(self):
        password = "mysecretpassword"
        hashed = self.manager.hash_password(password, rounds=4)
        self.assertTrue(self.manager.verify_password(password, hashed))
        self.assertFalse(self.manager.verify_password("wrongpassword", hashed))

    def test_cli_logic_hash(self):
        import sys
        import io

        args = argparse.Namespace(hash="testpass", verify=None, rounds=4)

        output = io.StringIO()
        sys.stdout = output

        try:
            success = run_bcrypt_lab_logic(args)
            self.assertTrue(success)
            printed_hash = output.getvalue().strip()
            self.assertTrue(printed_hash.startswith("$2b$04$"))
        finally:
            sys.stdout = sys.__stdout__

if __name__ == "__main__":
    unittest.main()

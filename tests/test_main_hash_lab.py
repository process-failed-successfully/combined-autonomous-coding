import unittest
from unittest.mock import patch, MagicMock
import sys
import io
from shared.hash_lab import run_hash_lab_logic

class TestHashLabCLI(unittest.TestCase):

    def test_run_hash_string(self):
        args = MagicMock()
        args.action = "string"
        args.text = "hello"
        args.algo = "sha256"

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = run_hash_lab_logic(args)
            self.assertTrue(result)
            self.assertIn("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824", mock_stdout.getvalue())

    def test_run_hash_string_stdin(self):
        args = MagicMock()
        args.action = "string"
        args.text = None
        args.algo = "sha256"

        with patch('sys.stdin', io.StringIO("hello")):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                # We need to mock isatty to return False
                with patch('sys.stdin.isatty', return_value=False):
                    result = run_hash_lab_logic(args)
                    self.assertTrue(result)
                    self.assertIn("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824", mock_stdout.getvalue())

    def test_run_hash_file(self):
        # We need a real file or mock open
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
            tf.write("hello")
            tf.close()
            try:
                args = MagicMock()
                args.action = "file"
                args.path = tf.name
                args.algo = "sha256"

                with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                    result = run_hash_lab_logic(args)
                    self.assertTrue(result)
                    self.assertIn("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824", mock_stdout.getvalue())
            finally:
                os.remove(tf.name)

if __name__ == '__main__':
    unittest.main()

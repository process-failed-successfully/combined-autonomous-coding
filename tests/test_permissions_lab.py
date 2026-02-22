import unittest
import sys
import os
import shutil
import tempfile
from io import StringIO
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module to test.
# Assuming PYTHONPATH is set correctly or we append to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from shared.permissions_lab import PermissionsManager, run_permissions_lab_logic

class TestPermissionsLab(unittest.TestCase):
    def setUp(self):
        self.manager = PermissionsManager()
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "test_file.txt"
        self.test_file.write_text("content")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_manager_conversions(self):
        # Octal -> Symbolic
        # 7 -> rwx
        r, w, x = self.manager.from_octal(7)
        self.assertTrue(r)
        self.assertTrue(w)
        self.assertTrue(x)
        self.assertEqual(self.manager.to_symbolic(r, w, x), "rwx")

        # 5 -> r-x
        r, w, x = self.manager.from_octal(5)
        self.assertTrue(r)
        self.assertFalse(w)
        self.assertTrue(x)
        self.assertEqual(self.manager.to_symbolic(r, w, x), "r-x")

    def test_manager_get_permissions(self):
        # Set permissions to 755
        os.chmod(self.test_file, 0o755)
        res = self.manager.get_permissions(str(self.test_file))

        self.assertNotIn("error", res)
        self.assertEqual(res["octal"], "755")
        self.assertEqual(res["symbolic"], "rwxr-xr-x")

    def test_manager_set_permissions(self):
        # Set to 644
        success = self.manager.set_permissions(str(self.test_file), "644")
        self.assertTrue(success)

        # Verify
        st = self.test_file.stat()
        mode = oct(st.st_mode)[-3:]
        self.assertEqual(mode, "644")

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_calc_octal(self, mock_stdout):
        args = MagicMock()
        args.action = "calc"
        args.value = "755"

        with self.assertRaises(SystemExit) as cm:
            run_permissions_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Octal: 755", output)
        self.assertIn("Symbolic: rwxr-xr-x", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_calc_symbolic(self, mock_stdout):
        args = MagicMock()
        args.action = "calc"
        args.value = "rwxr-xr-x"

        with self.assertRaises(SystemExit) as cm:
            run_permissions_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Symbolic: rwxr-xr-x", output)
        self.assertIn("Octal: 755", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_explain(self, mock_stdout):
        args = MagicMock()
        args.action = "explain"
        args.value = "755"

        with self.assertRaises(SystemExit) as cm:
            run_permissions_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Owner: Read, Write, Execute", output)
        self.assertIn("Group: Read, Execute", output)
        self.assertIn("Other: Read, Execute", output)

if __name__ == '__main__':
    unittest.main()

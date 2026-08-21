import unittest
import sys
from unittest.mock import patch, MagicMock
from shared.ulid_lab import UlidLabManager, run_ulid_lab_logic

class TestUlidLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = UlidLabManager()

    def test_generate(self):
        results = self.manager.generate(count=2)
        self.assertEqual(len(results), 2)
        for u in results:
            self.assertTrue(self.manager.validate(u))

    def test_inspect_valid(self):
        valid_ulid = self.manager.generate()[0]
        info = self.manager.inspect(valid_ulid)
        self.assertTrue(info["valid"])
        self.assertEqual(info["ulid"], valid_ulid)
        self.assertIn("timestamp", info)
        self.assertIn("randomness", info)

    def test_inspect_invalid(self):
        info = self.manager.inspect("invalid_ulid_string")
        self.assertFalse(info["valid"])
        self.assertEqual(info["error"], "Invalid ULID format")

    def test_validate(self):
        valid_ulid = self.manager.generate()[0]
        self.assertTrue(self.manager.validate(valid_ulid))
        self.assertFalse(self.manager.validate("invalid"))

    def test_extract(self):
        u1 = self.manager.generate()[0]
        u2 = self.manager.generate()[0]
        u3 = self.manager.generate()[0].lower() # ensure it handles lowercase

        text = f"Here is {u1}, and {u2}, also {u3}. Oh and {u1} again! Plus an invalid UUUUUUUUUUUUUUUUUUUUUUUUUU"

        ulids = self.manager.extract(text)
        self.assertEqual(len(ulids), 4)
        self.assertEqual(ulids[0], u1.upper())
        self.assertEqual(ulids[1], u2.upper())
        self.assertEqual(ulids[2], u3.upper())
        self.assertEqual(ulids[3], u1.upper())

        unique_ulids = self.manager.extract(text, unique=True)
        self.assertEqual(len(unique_ulids), 3)
        self.assertEqual(unique_ulids, [u1.upper(), u2.upper(), u3.upper()])

class TestUlidLabCli(unittest.TestCase):
    @patch('builtins.print')
    def test_run_logic_generate(self, mock_print):
        args = MagicMock()
        args.action = "generate"
        args.count = 3

        run_ulid_lab_logic(args)
        self.assertEqual(mock_print.call_count, 3)

    @patch('builtins.print')
    @patch('sys.exit')
    def test_run_logic_inspect_valid(self, mock_exit, mock_print):
        manager = UlidLabManager()
        valid_ulid = manager.generate()[0]

        args = MagicMock()
        args.action = "inspect"
        args.ulid = valid_ulid

        run_ulid_lab_logic(args)

        self.assertTrue(mock_print.call_count > 5)
        mock_exit.assert_not_called()

    @patch('builtins.print')
    @patch('sys.exit')
    def test_run_logic_validate_valid(self, mock_exit, mock_print):
        manager = UlidLabManager()
        valid_ulid = manager.generate()[0]

        args = MagicMock()
        args.action = "validate"
        args.ulid = valid_ulid

        run_ulid_lab_logic(args)
        mock_print.assert_called_with(f"✅ Valid ULID: {valid_ulid}")
        mock_exit.assert_called_with(0)

if __name__ == '__main__':
    unittest.main()

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

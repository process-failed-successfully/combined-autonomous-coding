import unittest
from unittest.mock import patch, MagicMock
import sys
import io

from shared.luhn_lab import LuhnManager, run_luhn_lab_logic

class TestLuhnManager(unittest.TestCase):
    def setUp(self):
        self.manager = LuhnManager()

    def test_validate_valid_numbers(self):
        # Known valid Luhn numbers
        self.assertTrue(self.manager.validate("79927398713"))
        self.assertTrue(self.manager.validate("49927398716"))
        self.assertTrue(self.manager.validate("1234567812345670"))

    def test_validate_invalid_numbers(self):
        # Known invalid Luhn numbers
        self.assertFalse(self.manager.validate("79927398714"))
        self.assertFalse(self.manager.validate("1234567812345671"))
        self.assertFalse(self.manager.validate("1")) # Too short/single digit often invalid, depends on sum

    def test_validate_with_formatting(self):
        # Should ignore non-digit characters
        self.assertTrue(self.manager.validate("7992-7398-713"))
        self.assertTrue(self.manager.validate("4992 7398 716"))
        self.assertFalse(self.manager.validate("7992-7398-714"))

    def test_validate_empty_or_no_digits(self):
        self.assertFalse(self.manager.validate(""))
        self.assertFalse(self.manager.validate("abc-def"))

    def test_generate_length(self):
        generated = self.manager.generate(length=16)
        self.assertEqual(len(generated), 16)
        self.assertTrue(generated.isdigit())
        self.assertTrue(self.manager.validate(generated))

    def test_generate_with_prefix(self):
        prefix = "40001234"
        generated = self.manager.generate(length=16, prefix=prefix)
        self.assertEqual(len(generated), 16)
        self.assertTrue(generated.startswith(prefix))
        self.assertTrue(self.manager.validate(generated))

    def test_generate_invalid_length(self):
        with self.assertRaises(ValueError):
            self.manager.generate(length=5, prefix="123456")

class TestLuhnLabCLI(unittest.TestCase):
    @patch("sys.exit")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_validate_valid(self, mock_stdout, mock_exit):
        args = MagicMock()
        args.action = "validate"
        args.number = "79927398713"

        run_luhn_lab_logic(args)

        mock_exit.assert_called_once_with(0)
        self.assertIn("valid Luhn sequence", mock_stdout.getvalue())

    @patch("sys.exit")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_validate_invalid(self, mock_stdout, mock_exit):
        args = MagicMock()
        args.action = "validate"
        args.number = "79927398714"

        run_luhn_lab_logic(args)

        mock_exit.assert_called_once_with(1)
        self.assertIn("INVALID", mock_stdout.getvalue())

    @patch("sys.exit")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_generate(self, mock_stdout, mock_exit):
        args = MagicMock()
        args.action = "generate"
        args.length = 16
        args.prefix = "4556"

        run_luhn_lab_logic(args)

        mock_exit.assert_called_once_with(0)
        output = mock_stdout.getvalue()
        self.assertIn("Generated valid Luhn sequence", output)

        # Extract the generated number from the output and validate it
        parts = output.strip().split()
        generated_num = parts[-1]
        self.assertTrue(generated_num.startswith("4556"))
        self.assertEqual(len(generated_num), 16)
        self.assertTrue(LuhnManager().validate(generated_num))

if __name__ == '__main__':
    unittest.main()

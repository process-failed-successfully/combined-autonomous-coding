import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.text_lab import run_text_lab_logic

class TestTextLabCLI(unittest.TestCase):
    def setUp(self):
        self.mock_args = MagicMock()

    @patch("shared.text_lab.TextLabManager")
    @patch("sys.stdin")
    def test_sort_lines(self, mock_stdin, MockManager):
        manager_instance = MockManager.return_value
        manager_instance.sort_lines.return_value = "sorted\nlines"

        self.mock_args.action = "sort-lines"
        self.mock_args.text = "lines\nsorted"
        self.mock_args.reverse = False

        with patch("builtins.print") as mock_print:
            run_text_lab_logic(self.mock_args)

        manager_instance.sort_lines.assert_called_with("lines\nsorted", reverse=False)
        mock_print.assert_called_with("sorted\nlines")

    @patch("shared.text_lab.TextLabManager")
    def test_unique_lines(self, MockManager):
        manager_instance = MockManager.return_value
        manager_instance.unique_lines.return_value = "unique\nlines"

        self.mock_args.action = "unique-lines"
        self.mock_args.text = "lines\nlines"

        with patch("builtins.print") as mock_print:
            run_text_lab_logic(self.mock_args)

        manager_instance.unique_lines.assert_called_with("lines\nlines")
        mock_print.assert_called_with("unique\nlines")

    @patch("shared.text_lab.TextLabManager")
    def test_reverse_lines(self, MockManager):
        manager_instance = MockManager.return_value
        manager_instance.reverse_lines.return_value = "reversed"

        self.mock_args.action = "reverse-lines"
        self.mock_args.text = "input"

        with patch("builtins.print") as mock_print:
            run_text_lab_logic(self.mock_args)

        manager_instance.reverse_lines.assert_called_with("input")
        mock_print.assert_called_with("reversed")

    @patch("shared.text_lab.TextLabManager")
    def test_shuffle_lines(self, MockManager):
        manager_instance = MockManager.return_value
        manager_instance.shuffle_lines.return_value = "shuffled"

        self.mock_args.action = "shuffle-lines"
        self.mock_args.text = "input"

        with patch("builtins.print") as mock_print:
            run_text_lab_logic(self.mock_args)

        manager_instance.shuffle_lines.assert_called_with("input")
        mock_print.assert_called_with("shuffled")

    @patch("shared.text_lab.TextLabManager")
    def test_number_lines(self, MockManager):
        manager_instance = MockManager.return_value
        manager_instance.number_lines.return_value = "numbered"

        self.mock_args.action = "number-lines"
        self.mock_args.text = "input"

        with patch("builtins.print") as mock_print:
            run_text_lab_logic(self.mock_args)

        manager_instance.number_lines.assert_called_with("input")
        mock_print.assert_called_with("numbered")

    @patch("shared.text_lab.TextLabManager")
    def test_trim_lines(self, MockManager):
        manager_instance = MockManager.return_value
        manager_instance.trim_lines.return_value = "trimmed"

        self.mock_args.action = "trim-lines"
        self.mock_args.text = "input"

        with patch("builtins.print") as mock_print:
            run_text_lab_logic(self.mock_args)

        manager_instance.trim_lines.assert_called_with("input")
        mock_print.assert_called_with("trimmed")

    @patch("shared.text_lab.TextLabManager")
    def test_filter_lines(self, MockManager):
        manager_instance = MockManager.return_value
        manager_instance.filter_lines.return_value = "filtered"

        self.mock_args.action = "filter-lines"
        self.mock_args.text = "input"
        self.mock_args.pattern = "regex"
        self.mock_args.exclude = True

        with patch("builtins.print") as mock_print:
            run_text_lab_logic(self.mock_args)

        manager_instance.filter_lines.assert_called_with("input", "regex", exclude=True)
        mock_print.assert_called_with("filtered")

    @patch("shared.text_lab.TextLabManager")
    def test_lorem(self, MockManager):
        manager_instance = MockManager.return_value
        manager_instance.lorem_ipsum.return_value = "lorem ipsum"

        self.mock_args.action = "lorem"
        self.mock_args.words = 2

        with patch("builtins.print") as mock_print:
            run_text_lab_logic(self.mock_args)

        manager_instance.lorem_ipsum.assert_called_with(2)
        mock_print.assert_called_with("lorem ipsum")

if __name__ == "__main__":
    unittest.main()

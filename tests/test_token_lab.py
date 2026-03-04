import unittest
from unittest.mock import patch
import io

from shared.token_lab import TokenLabManager, run_token_lab_logic


class TestTokenLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = TokenLabManager()
        self.sample_text = "Hello, world!"
        # "Hello, world!" in cl100k_base is typically 4 tokens: ["Hello", ",", " world", "!"]

    def test_count_tokens_valid_model(self):
        count = self.manager.count_tokens(self.sample_text, "gpt-4o")
        self.assertGreater(count, 0)
        self.assertEqual(count, 4)

    def test_count_tokens_invalid_model_fallback(self):
        # Should fallback to cl100k_base
        count = self.manager.count_tokens(self.sample_text, "invalid-model-123")
        self.assertGreater(count, 0)

    def test_count_tokens_empty_text(self):
        count = self.manager.count_tokens("", "gpt-4o")
        self.assertEqual(count, 0)

    def test_count_tokens_by_encoding(self):
        count = self.manager.count_tokens_by_encoding(self.sample_text, "cl100k_base")
        self.assertEqual(count, 4)

    def test_count_tokens_by_invalid_encoding(self):
        count = self.manager.count_tokens_by_encoding(self.sample_text, "invalid-encoding-123")
        self.assertEqual(count, 0)

    def test_get_tokens(self):
        tokens = self.manager.get_tokens(self.sample_text, "gpt-4o")
        self.assertIsInstance(tokens, list)
        self.assertEqual(len(tokens), 4)

    def test_decode_tokens(self):
        tokens = self.manager.get_tokens(self.sample_text, "gpt-4o")
        decoded = self.manager.decode_tokens(tokens, "gpt-4o")
        self.assertEqual(decoded, self.sample_text)


class TestTokenLabCLI(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_token_lab_count(self, mock_stdout):
        class Args:
            action = "count"
            text = "Hello, world!"
            model = "gpt-4o"

        run_token_lab_logic(Args())
        output = mock_stdout.getvalue()
        self.assertIn("Tokens (gpt-4o): 4", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_token_lab_count_encoding(self, mock_stdout):
        class Args:
            action = "count"
            text = "Hello, world!"
            encoding = "cl100k_base"
            model = "gpt-4o"

        run_token_lab_logic(Args())
        output = mock_stdout.getvalue()
        self.assertIn("Tokens (cl100k_base): 4", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_token_lab_tokenize(self, mock_stdout):
        class Args:
            action = "tokenize"
            text = "Hello, world!"
            model = "gpt-4o"
            encoding = None

        run_token_lab_logic(Args())
        output = mock_stdout.getvalue()
        self.assertIn("Tokens: [", output)

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_run_token_lab_no_input(self, mock_stderr):
        class Args:
            action = "count"
            text = ""
            file = ""
            model = "gpt-4o"
            encoding = None

        # Mock sys.stdin.isatty to True to simulate no stdin pipe
        with patch('sys.stdin.isatty', return_value=True):
            with self.assertRaises(SystemExit) as cm:
                run_token_lab_logic(Args())
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("No text provided", mock_stderr.getvalue())

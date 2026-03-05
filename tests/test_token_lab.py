import unittest
import argparse
from unittest.mock import patch
from shared.token_lab import TokenLabManager, run_token_lab_logic


class TestTokenLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = TokenLabManager()

    def test_count_tokens(self):
        result = self.manager.count_tokens("hello world")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["tokens"], [15339, 1917])

    def test_encode(self):
        result = self.manager.encode("hello world")
        self.assertTrue(result["success"])
        self.assertEqual(result["tokens"], [15339, 1917])

    def test_decode(self):
        result = self.manager.decode([15339, 1917])
        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "hello world")

    def test_invalid_model(self):
        manager = TokenLabManager(model="invalid_model_123")
        self.assertFalse(manager.count_tokens("test")["success"])
        self.assertFalse(manager.encode("test")["success"])
        self.assertFalse(manager.decode([1, 2, 3])["success"])


class TestTokenLabCLI(unittest.TestCase):
    @patch('sys.stdout')
    def test_cli_count(self, mock_stdout):
        args = argparse.Namespace(action='count', text='hello world', encoding='cl100k_base', verbose=False)
        self.assertTrue(run_token_lab_logic(args))

    @patch('sys.stdout')
    def test_cli_encode(self, mock_stdout):
        args = argparse.Namespace(action='encode', text='hello world', encoding='cl100k_base')
        self.assertTrue(run_token_lab_logic(args))

    @patch('sys.stdout')
    def test_cli_decode(self, mock_stdout):
        args = argparse.Namespace(action='decode', tokens='15339, 1917', encoding='cl100k_base')
        self.assertTrue(run_token_lab_logic(args))

    @patch('sys.stderr')
    def test_cli_invalid_args(self, mock_stderr):
        args = argparse.Namespace(action='count', text=None, encoding='cl100k_base')
        self.assertFalse(run_token_lab_logic(args))
        args = argparse.Namespace(action='decode', tokens='invalid,string', encoding='cl100k_base')
        self.assertFalse(run_token_lab_logic(args))


if __name__ == '__main__':
    unittest.main()

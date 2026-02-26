import unittest
from unittest.mock import MagicMock, patch
from shared.transpiler_lab import TranspilerManager
from pathlib import Path

class TestTranspilerManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = TranspilerManager(Path("."))

    @patch("shared.transpiler_lab.run_ask_logic")
    async def test_transpile_success(self, mock_ask):
        # Setup mock to write to stdout as run_ask_logic does
        async def mock_run_ask(*args, **kwargs):
            print("fmt.Println('Hello World')")
            return True

        mock_ask.side_effect = mock_run_ask

        source_code = "print('Hello World')"
        result = await self.manager.transpile(source_code, "Python", "Go")

        self.assertEqual(result, "fmt.Println('Hello World')")
        mock_ask.assert_called_once()

    @patch("shared.transpiler_lab.run_ask_logic")
    async def test_transpile_empty_source(self, mock_ask):
        result = await self.manager.transpile("", "Python", "Go")
        self.assertEqual(result, "")
        mock_ask.assert_not_called()

    @patch("shared.transpiler_lab.run_ask_logic")
    async def test_transpile_failure(self, mock_ask):
        # Setup mock to fail
        async def mock_run_ask(*args, **kwargs):
            return False

        mock_ask.side_effect = mock_run_ask

        result = await self.manager.transpile("code", "Python", "Go")
        self.assertIn("Error", result)

    @patch("shared.transpiler_lab.run_ask_logic")
    async def test_transpile_strips_markdown(self, mock_ask):
        async def mock_run_ask(*args, **kwargs):
            print("```go\nfmt.Println('Hello')\n```")
            return True

        mock_ask.side_effect = mock_run_ask

        result = await self.manager.transpile("print('Hello')", "Python", "Go")
        self.assertEqual(result, "fmt.Println('Hello')")

if __name__ == "__main__":
    unittest.main()

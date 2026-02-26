import unittest
import sys
import asyncio
from unittest.mock import MagicMock, patch
from pathlib import Path

# Fix path to import shared modules
sys.path.append(str(Path(__file__).parent.parent))

from shared.transpiler_lab import TranspilerManager

class TestTranspilerManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = TranspilerManager(self.project_dir)

    @patch("shared.transpiler_lab.run_ask_logic")
    async def test_transpile_success(self, mock_ask):
        # Setup mock return value for run_ask_logic via capturing stdout logic in manager
        # Since manager captures stdout, we need mock_ask to print something?
        # Actually, run_ask_logic is async.
        # But wait, TranspilerManager captures stdout of run_ask_logic.
        # So we need mock_ask to be a coroutine that prints to stdout.

        async def side_effect(*args, **kwargs):
            print("```go\nfunc main() {}\n```")
            return True

        mock_ask.side_effect = side_effect

        content = "def main(): pass"
        result = await self.manager.transpile(content, "python", "go")

        self.assertIn("func main() {}", result)
        self.assertNotIn("```", result) # Should strip blocks

    @patch("shared.transpiler_lab.run_ask_logic")
    async def test_transpile_empty_content(self, mock_ask):
        result = await self.manager.transpile("", "python", "go")
        self.assertEqual(result, "")
        mock_ask.assert_not_called()

    @patch("shared.transpiler_lab.run_ask_logic")
    async def test_transpile_error(self, mock_ask):
        mock_ask.side_effect = Exception("API Error")

        content = "print('hello')"
        result = await self.manager.transpile(content, "python", "javascript")

        self.assertIn("Error during transpilation", result)
        self.assertIn("API Error", result)

if __name__ == "__main__":
    unittest.main()

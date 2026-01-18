import unittest
from unittest.mock import patch, AsyncMock
import argparse
from pathlib import Path
from main import run_docstring


class TestMainDocstring(unittest.IsolatedAsyncioTestCase):
    @patch("shared.docstring.DocstringManager")
    async def test_check_command_found_items(self, MockManager):
        # Setup
        mock_instance = MockManager.return_value
        # Ensure file path is absolute relative to project dir
        project_dir = Path(".").resolve()
        mock_instance.scan.return_value = [
            {"file": project_dir / "test.py", "name": "func", "type": "FunctionDef", "lineno": 1}
        ]

        args = argparse.Namespace(
            action="check",
            project_dir=Path("."),
        )

        # Expect SystemExit(1)
        with self.assertRaises(SystemExit) as cm:
            await run_docstring(args)
        self.assertEqual(cm.exception.code, 1)

    @patch("shared.docstring.DocstringManager")
    async def test_check_command_no_items(self, MockManager):
        # Setup
        mock_instance = MockManager.return_value
        mock_instance.scan.return_value = []

        args = argparse.Namespace(
            action="check",
            project_dir=Path("."),
        )

        # Expect SystemExit(0)
        with self.assertRaises(SystemExit) as cm:
            await run_docstring(args)
        self.assertEqual(cm.exception.code, 0)

    @patch("shared.docstring.DocstringManager")
    async def test_generate_command(self, MockManager):
        # Setup
        mock_instance = MockManager.return_value
        mock_instance.scan.return_value = [
            {"file": Path("test.py"), "name": "func", "type": "FunctionDef", "lineno": 1}
        ]
        mock_instance.generate_and_apply = AsyncMock(return_value=1)

        args = argparse.Namespace(
            action="generate",
            project_dir=Path("."),
            agent="gemini",
            model=None,
            yes=True  # Skip confirmation
        )

        # Expect SystemExit(0)
        with self.assertRaises(SystemExit) as cm:
            await run_docstring(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify call
        mock_instance.generate_and_apply.assert_called_once()
        call_args = mock_instance.generate_and_apply.call_args
        self.assertEqual(call_args.kwargs["agent_type"], "gemini")


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
import io
import sys
from contextlib import redirect_stdout, redirect_stderr

# It's better to import the module or specific functions you need to test
import main

class TestMainModelsCommand(unittest.TestCase):

    def test_run_models_all_agents(self):
        """Test the 'models' command without any agent filter."""
        # Mock the arguments that parse_args would create
        args = MagicMock()
        args.agent = None

        # Redirect stdout to capture the output
        f = io.StringIO()
        with redirect_stdout(f):
            # The function calls sys.exit(), so we need to catch it
            with self.assertRaises(SystemExit) as cm:
                main.run_models(args)

        # Check that the exit code is 0 (success)
        self.assertEqual(cm.exception.code, 0)

        # Get the output and check for expected content
        output = f.getvalue()
        self.assertIn("--- Recommended Models ---", output)
        self.assertIn("# Gemini Agent", output)
        self.assertIn("gemini-1.5-pro-latest", output)
        self.assertIn("# Cursor Agent", output)
        self.assertIn("claude-3.5-sonnet", output)
        self.assertIn("# Openrouter Agent", output)
        self.assertIn("anthropic/claude-3.5-sonnet", output)
        self.assertIn("# Local Agent", output)
        self.assertIn("ollama/llama3", output)

    def test_run_models_with_agent_filter(self):
        """Test the 'models' command with a specific agent filter."""
        args = MagicMock()
        args.agent = "gemini"

        f = io.StringIO()
        with redirect_stdout(f):
            with self.assertRaises(SystemExit) as cm:
                main.run_models(args)

        self.assertEqual(cm.exception.code, 0)

        output = f.getvalue()
        self.assertIn("--- Recommended Models ---", output)
        self.assertIn("# Gemini Agent", output)
        self.assertIn("gemini-1.5-pro-latest", output)
        # Ensure other agents are NOT in the output
        self.assertNotIn("# Cursor Agent", output)
        self.assertNotIn("# Openrouter Agent", output)

    def test_run_models_invalid_agent(self):
        """Test the 'models' command with an invalid agent filter."""
        args = MagicMock()
        args.agent = "invalid_agent"

        # Redirect stderr to capture the error message
        f_err = io.StringIO()
        with redirect_stderr(f_err):
            with self.assertRaises(SystemExit) as cm:
                main.run_models(args)

        # Check for non-zero exit code
        self.assertEqual(cm.exception.code, 1)

        # Check for the correct error message
        error_output = f_err.getvalue()
        self.assertIn("Error: Agent 'invalid_agent' not found.", error_output)

if __name__ == '__main__':
    unittest.main()

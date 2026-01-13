import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import argparse
from pathlib import Path
import asyncio

# Add project root to path to allow direct imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_ask, get_parser

class TestMainAskCommand(unittest.IsolatedAsyncioTestCase):

    @patch('agents.gemini.agent.get_gemini_client')
    async def test_run_ask_successful(self, mock_get_gemini_client):
        """
        Tests the run_ask command with a successful response from the Gemini client.
        """
        # --- Setup Mocks ---
        # Mock the Gemini client and its streaming response
        mock_client = MagicMock()
        mock_stream = [MagicMock(text="This is a test response.")]
        mock_client.generate_content = MagicMock(return_value=mock_stream)
        mock_get_gemini_client.return_value = mock_client

        # --- Setup Arguments ---
        # Get the real parser to ensure all commands are populated
        parser = get_parser()
        args = argparse.Namespace(question=["how", "do", "I", "run", "tests"])

        # --- Execute ---
        # The function calls sys.exit(0) on success, so we catch it
        with self.assertRaises(SystemExit) as cm:
            await run_ask(args, parser)

        # --- Assertions ---
        self.assertEqual(cm.exception.code, 0)
        # Verify that the client was called
        mock_get_gemini_client.assert_called_once()
        mock_client.generate_content.assert_called_once()

        # Verify the prompt contains key elements
        call_args, call_kwargs = mock_client.generate_content.call_args
        prompt = call_args[0]
        self.assertIn("You are an expert assistant for a command-line tool", prompt)
        self.assertIn("USER'S QUESTION:\n\"how do I run tests\"", prompt)
        self.assertIn("Command: test", prompt) # Check that command info was extracted
        self.assertEqual(call_kwargs, {'stream': True})


    async def test_run_ask_no_question(self):
        """
        Tests that the command exits gracefully if no question is provided.
        """
        parser = get_parser()
        args = argparse.Namespace(question=[])

        with self.assertRaises(SystemExit) as cm:
            await run_ask(args, parser)

        self.assertEqual(cm.exception.code, 1)

    @patch('agents.gemini.agent.get_gemini_client')
    async def test_run_ask_client_exception(self, mock_get_gemini_client):
        """
        Tests that the command handles exceptions from the Gemini client.
        """
        # --- Setup Mocks ---
        # Configure the mock to raise an exception
        mock_get_gemini_client.side_effect = Exception("API connection failed")

        # --- Setup Arguments ---
        parser = get_parser()
        args = argparse.Namespace(question=["some", "question"])

        # --- Execute ---
        with self.assertRaises(SystemExit) as cm:
            await run_ask(args, parser)

        # --- Assertions ---
        self.assertEqual(cm.exception.code, 1)
        mock_get_gemini_client.assert_called_once()

if __name__ == '__main__':
    unittest.main()

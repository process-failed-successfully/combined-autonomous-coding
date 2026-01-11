import unittest
from unittest.mock import patch
import io
import sys
from main import run_commands
import argparse

class TestMainCommands(unittest.TestCase):
    def test_run_commands_prints_expected_sections(self):
        """
        Tests that the run_commands command prints the expected section headers.
        """
        expected_sections = [
            "Getting Started",
            "Core Commands",
            "Inspection & History",
            "Git & Workflow",
            "Artifact & Sprint Management",
            "Utilities",
        ]

        # Redirect stdout to capture the output of the help command
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            # The function now exits, so we need to catch the SystemExit exception
            with self.assertRaises(SystemExit) as cm:
                run_commands(argparse.Namespace())
            self.assertEqual(cm.exception.code, 0)
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()

        # Check that each expected section is in the output
        for section in expected_sections:
            self.assertIn(f"--- {section} ---", output)

        # Check for a few specific commands to ensure content is being printed
        self.assertIn("init", output)
        self.assertIn("status", output)
        self.assertIn("commit", output)
        self.assertIn("artifacts", output)
        self.assertIn("why", output)

    def test_run_commands_exits_with_zero(self):
        """
        Tests that the run_commands function exits with a status code of 0.
        """
        with self.assertRaises(SystemExit) as cm:
            run_commands(argparse.Namespace())
        self.assertEqual(cm.exception.code, 0)


if __name__ == '__main__':
    unittest.main()

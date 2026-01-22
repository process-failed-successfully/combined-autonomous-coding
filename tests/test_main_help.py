import unittest
import io
import sys
from main import run_help
import argparse


class TestMainHelp(unittest.TestCase):
    def test_run_help_prints_expected_sections(self):
        """
        Tests that the run_help command prints the expected section headers.
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
                run_help(argparse.Namespace())
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


if __name__ == '__main__':
    unittest.main()

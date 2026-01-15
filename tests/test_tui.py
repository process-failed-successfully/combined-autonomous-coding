import sys
from pathlib import Path
import unittest
from unittest.mock import patch

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from textual.pilot import Pilot
from shared.tui import AgentTUI

class TestInteractiveTUI(unittest.IsolatedAsyncioTestCase):
    """Test suite for the interactive TUI command runner."""

    async def test_command_execution_in_tui(self):
        """
        Tests if a user can type a command into the Input widget, press Enter,
        and see the output in the command output RichLog.
        """
        app = AgentTUI(project_dir=Path("."))

        async with app.run_test() as pilot:
            # 1. Get the input and output widgets
            command_input = pilot.app.screen.query_one("Input")
            command_output = pilot.app.screen.query_one("#command-output")

            # 2. Simulate typing a command and pressing Enter
            await pilot.click("Input")
            await pilot.press(*"status")
            await pilot.press("enter")

            # 3. Wait for the output to appear
            # The command runs in a thread, so we need to wait for it to finish
            # and for the UI to update.
            await pilot.pause(1.0) # Give it a second to run

            # 4. Assert that the output log contains the expected text
            # The 'status' command should output a summary. We'll check for a known string.
            output_lines = []
            for strip in command_output.lines:
                output_lines.append("".join(segment.text for segment in strip._segments))
            output_content = "\n".join(output_lines)

            self.assertIn("$ status", output_content)
            self.assertIn("--- Project Status:", output_content)
            self.assertIn("[ Workflow:", output_content)

    async def test_unsupported_command(self):
        """
        Tests if an unsupported command shows an appropriate error message.
        """
        app = AgentTUI(project_dir=Path("."))

        async with app.run_test() as pilot:
            command_input = pilot.app.screen.query_one("Input")
            command_output = pilot.app.screen.query_one("#command-output")

            await pilot.click("Input")
            await pilot.press(*"foobar")
            await pilot.press("enter")

            await pilot.pause(0.5)

            output_lines = []
            for strip in command_output.lines:
                output_lines.append("".join(segment.text for segment in strip._segments))
            output_content = "\n".join(output_lines)

            # The argparse error message for an invalid choice goes to stderr
            self.assertIn("$ foobar", output_content)
            self.assertIn("invalid choice: 'foobar'", output_content)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import AsyncMock, patch
from pathlib import Path
from shared.utils import execute_bash_block


class TestSecurityFailOpen(unittest.IsolatedAsyncioTestCase):
    async def test_bash_execution_blocked_on_parsing_error(self):
        """
        Verify that execute_bash_block does NOT execute the command if shlex.split fails.
        Current behavior (vulnerable): It swallows ValueError and executes.
        Desired behavior (secure): It catches ValueError and returns an error message.
        """
        project_dir = Path("/tmp/test_project")
        malformed_command = 'echo "hello'  # Unclosed quote, causes ValueError in shlex

        with patch("shared.utils.asyncio.create_subprocess_shell", new_callable=AsyncMock) as mock_subprocess:
            # Note: execute_bash_block calls shlex.split(command).
            # If it raises ValueError, control flow goes to except ValueError: pass
            # Then it proceeds to create_subprocess_shell.

            result = await execute_bash_block(malformed_command, project_dir)

            # Vulnerability Check: If called, we are failing open.
            # We assert that it is NOT called.
            if mock_subprocess.called:
                self.fail("SECURITY VULNERABILITY: execute_bash_block executed command despite parsing error!")

            self.assertIn("Error", result)

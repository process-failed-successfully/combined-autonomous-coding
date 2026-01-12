import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import argparse
from pathlib import Path
import main
import sys
import tempfile
import shutil

class TestDevelopCommand(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "project"
        self.project_dir.mkdir()
        self.spec_file = self.project_dir / "spec.txt"
        self.spec_file.write_text("This is the spec.")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main.Observer')
    @patch('main.run_agent_task', new_callable=AsyncMock)
    @patch('main.run_test')
    async def test_develop_command_triggers_agent_and_tests(self, mock_run_test, mock_run_agent_task, mock_observer):
        """Verify that the develop command correctly triggers the agent and tests on file modification."""
        args = argparse.Namespace(
            command='develop',
            spec=self.spec_file,
            project_dir=self.project_dir,
            max_iterations=3,
            # --- Add all other necessary args for run_agent_task ---
            profile=None,
            agent='gemini',
            model=None,
            verbose=False,
            no_stream=True,
            verify_creation=False,
            manager_frequency=10,
            manager_model=None,
            manager_first=False,
            login=False,
            timeout=None,
            max_error_wait=None,
            sprint=False,
            max_agents=1,
            jira_ticket=None,
            jira_label=None,
            dind=False,
            no_dashboard=True,
            dashboard_url="http://localhost:7654",
            dry_run=False
        )

        # Mock the observer to control the event handler
        mock_observer_instance = mock_observer.return_value
        event_handler = None

        def schedule_capture(handler, path, recursive):
            nonlocal event_handler
            event_handler = handler

        mock_observer_instance.schedule.side_effect = schedule_capture

        # The develop command runs an infinite loop, so we'll patch sleep to break out of it
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = [asyncio.CancelledError] # Break the loop on first await

            with self.assertRaises(asyncio.CancelledError):
                await main.run_develop(args)

        self.assertIsNotNone(event_handler)

        # Simulate a file modification event
        event = MagicMock()
        event.is_directory = False
        event.src_path = str(self.spec_file)

        # In the actual implementation, watchdog calls this from a separate thread.
        # We simulate this by calling the method directly.
        event_handler.on_modified(event)

        # Allow the event loop to process the triggered task
        await asyncio.sleep(0)

        # Wait for the debounced task to complete
        # In test, the coroutine is not actually running in a separate thread, so we can await it
        if event_handler._debounce_task:
             # In test, run_coroutine_threadsafe returns a future-like object
             # that we can't directly await. So we call trigger_run directly for test validation.
            await event_handler.trigger_run()

        # Assertions
        mock_run_agent_task.assert_called_once()
        agent_args = mock_run_agent_task.call_args[0][0]
        self.assertEqual(agent_args.max_iterations, 3)

        mock_run_test.assert_called_once()
        test_args = mock_run_test.call_args[0][0]
        self.assertEqual(test_args.project_dir, args.project_dir)

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock, AsyncMock, call
import asyncio
from pathlib import Path
import tempfile
import shutil
import argparse

# Make sure the main script can be imported
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import run_develop

class TestDevelopCommand(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)
        self.spec_file = self.project_dir / "app_spec.txt"
        self.spec_file.write_text("Initial spec")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('main.Observer')
    @patch('main.run_agent_task', new_callable=AsyncMock)
    @patch('main.run_test')
    @patch('main.setup_logger')
    async def test_develop_runs_agent_and_tests_on_start(self, mock_setup_logger, mock_run_test, mock_run_agent_task, mock_observer):
        """
        Tests that the develop command performs an initial agent run and then runs tests.
        The command should exit gracefully after the initial run for this test.
        """
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        args = argparse.Namespace(
            spec=self.spec_file,
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            no_tests=False,
            verbose=False,
        )

        # Mock SystemExit to prevent the test from exiting
        with patch('sys.exit') as mock_exit:
            # We'll use a short timeout to simulate a quick run and then stop.
            async def limited_run():
                try:
                    await asyncio.wait_for(run_develop(args), timeout=0.5)
                except asyncio.TimeoutError:
                    pass # Expected timeout

            await limited_run()

            # Verify that the agent task was called on startup
            mock_run_agent_task.assert_called_once()

            # Verify that run_test was called after the agent run
            mock_run_test.assert_called_once()

            # Verify the observer was started
            mock_observer.return_value.start.assert_called_once()
            mock_observer.return_value.stop.assert_called_once()

    @patch('main.Observer')
    @patch('main.run_agent_task', new_callable=AsyncMock)
    @patch('main.run_test')
    @patch('main.setup_logger')
    async def test_develop_skips_tests_with_no_tests_flag(self, mock_setup_logger, mock_run_test, mock_run_agent_task, mock_observer):
        """
        Tests that the --no-tests flag correctly skips the test run.
        """
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        args = argparse.Namespace(
            spec=self.spec_file,
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            no_tests=True, # Flag to skip tests
            verbose=False,
        )

        with patch('sys.exit'):
            async def limited_run():
                try:
                    await asyncio.wait_for(run_develop(args), timeout=0.5)
                except asyncio.TimeoutError:
                    pass

            await limited_run()

            mock_run_agent_task.assert_called_once()
            # Verify that run_test was NOT called
            mock_run_test.assert_not_called()

    @patch('main.FileSystemEventHandler')
    @patch('main.Observer')
    @patch('main.run_agent_task', new_callable=AsyncMock)
    @patch('main.run_test')
    @patch('main.setup_logger')
    async def test_file_modification_triggers_agent_run(self, mock_setup_logger, mock_run_test, mock_run_agent_task, mock_observer, mock_event_handler):
        """
        Tests that modifying the spec file triggers a new agent run.
        """
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        args = argparse.Namespace(
            spec=self.spec_file,
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            no_tests=False,
            verbose=False,
        )

        # Mock the event loop and ChangeHandler to manually trigger the event
        loop = asyncio.get_running_loop()

        # This is a bit complex: we need to capture the instance of the ChangeHandler
        # that run_develop creates, so we can call its on_modified method directly.
        handler_instance = None

        def capture_handler(handler, path, recursive):
            nonlocal handler_instance
            handler_instance = handler
            # By providing a side_effect, we replace the original method.
            # We don't need to call the original schedule for this test,
            # so we do nothing here to prevent a recursion error.

        mock_observer.return_value.schedule.side_effect = capture_handler

        # We need access to the event that run_develop uses internally.
        run_complete_event_ref = None
        original_event = asyncio.Event

        def event_factory(*args, **kwargs):
            nonlocal run_complete_event_ref
            event = original_event(*args, **kwargs)
            run_complete_event_ref = event
            return event

        # In the test, we're in the same thread, so run_coroutine_threadsafe
        # won't schedule the task as we expect. We'll patch it to just
        # create a task on the current loop.
        def run_coro_on_loop(coro, loop):
            return loop.create_task(coro)

        with patch('sys.exit'), \
             patch('asyncio.Event', side_effect=event_factory), \
             patch('asyncio.run_coroutine_threadsafe', side_effect=run_coro_on_loop):

            develop_task = loop.create_task(run_develop(args))

            # Wait for the first run to complete
            await asyncio.sleep(0.1)
            self.assertIsNotNone(run_complete_event_ref)
            await asyncio.wait_for(run_complete_event_ref.wait(), timeout=1.0)

            self.assertEqual(mock_run_agent_task.call_count, 1)
            self.assertEqual(mock_run_test.call_count, 1)

            # Manually clear the event before triggering the next run
            run_complete_event_ref.clear()

            # --- Simulate a file modification ---
            self.assertIsNotNone(handler_instance)
            mock_event = MagicMock()
            mock_event.src_path = str(self.spec_file)
            handler_instance.on_modified(mock_event)

            # Yield control to the event loop to allow the scheduled task to start
            await asyncio.sleep(0.1)

            # Wait for the second run to complete.
            await asyncio.wait_for(run_complete_event_ref.wait(), timeout=1.0)

            self.assertEqual(mock_run_agent_task.call_count, 2)
            self.assertEqual(mock_run_test.call_count, 2)

            # Clean up the task
            develop_task.cancel()
            try:
                await develop_task
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    unittest.main()

import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import time
from pathlib import Path
import tempfile
import shutil
import argparse
import sys

# Add project root to sys.path to allow imports from other directories
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from main import run_develop, SpecFileEventHandler, run_agent_task, run_test

class TestDevelopCommand(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()
        self.spec_file = self.project_dir / "app_spec.txt"
        self.spec_file.write_text("Initial spec.")

        # Mock args for the develop command
        self.args = argparse.Namespace(
            spec=self.spec_file,
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            verbose=False,
            profile=None,
            dashboard_url="http://localhost:7654",
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main.setup_logger')
    @patch('main.run_agent_task', new_callable=AsyncMock)
    @patch('main.run_test')
    @patch('main.Observer')
    async def test_develop_loop_triggers_agent_and_tests(self, mock_observer_cls, mock_run_test, mock_run_agent_task, mock_setup_logger):
        """
        Verify that modifying the spec file triggers the agent and then the tests.
        """
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        # --- Setup Mocks ---
        mock_observer_instance = MagicMock()
        mock_observer_cls.return_value = mock_observer_instance

        # We need to simulate the event handler being created and running
        loop = asyncio.get_running_loop()

        # Mock the config and client that the event handler will use
        mock_config = MagicMock()
        mock_config.spec_file.resolve.return_value = self.spec_file.resolve()
        mock_config.project_dir = self.project_dir

        mock_client = MagicMock()

        handler = SpecFileEventHandler(loop, mock_config, mock_client)

        # --- Simulate the develop command running ---

        # We'll run run_develop in a separate task so we can control it
        develop_task = loop.create_task(run_develop(self.args))

        # Give it a moment to start the observer
        await asyncio.sleep(0.1)

        # --- Simulate a file modification event ---
        # The watchdog observer runs in a separate thread, so we need to simulate that behavior.
        # We can directly call the on_modified method of the handler that `run_develop` would have created.

        # To get the handler, we need to inspect the call to observer.schedule
        # But for this test, let's create our own handler instance and call it.

        # The key is `asyncio.run_coroutine_threadsafe`. We patch it to run the coroutine directly.
        with patch('asyncio.run_coroutine_threadsafe', side_effect=lambda coro, loop: loop.create_task(coro)):
            # Create a mock event
            mock_event = MagicMock()
            mock_event.is_directory = False
            mock_event.src_path = str(self.spec_file.resolve())

            # Call the handler's on_modified method
            handler.on_modified(mock_event)

            # Allow the created task to run
            await asyncio.sleep(0.1)

        # --- Assertions ---
        mock_run_agent_task.assert_called_once()
        mock_run_test.assert_called_once()

        # Check that run_test was called with the correct project directory
        test_call_args = mock_run_test.call_args[0][0]
        self.assertEqual(test_call_args.project_dir, self.project_dir)

        # --- Cleanup ---
        develop_task.cancel()
        try:
            await develop_task
        except asyncio.CancelledError:
            pass # Expected

    @patch('main.time.time')
    @patch('asyncio.run_coroutine_threadsafe')
    async def test_debounce_logic(self, mock_run_coroutine, mock_time):
        """
        Test that the event handler respects the debounce period.
        """
        loop = asyncio.get_running_loop()
        mock_config = MagicMock()
        mock_config.spec_file.resolve.return_value = self.spec_file.resolve()
        handler = SpecFileEventHandler(loop, mock_config, MagicMock())

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(self.spec_file.resolve())

        # First call should trigger
        mock_time.return_value = 100.0
        handler.on_modified(mock_event)
        mock_run_coroutine.assert_called_once()

        # Second call immediately after should be ignored
        mock_time.return_value = 100.5 # 0.5s later
        handler.on_modified(mock_event)
        mock_run_coroutine.assert_called_once() # Still only called once

        # Third call after the debounce period should trigger again
        mock_time.return_value = 103.0 # 2.5s after the first call
        handler.on_modified(mock_event)
        self.assertEqual(mock_run_coroutine.call_count, 2)

if __name__ == '__main__':
    unittest.main()

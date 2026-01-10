
import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil
import time
import argparse

# Make sure the main module can be imported
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import main

class TestMainDevelopCommand(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.spec_file = self.project_dir / "app_spec.txt"
        self.spec_file.write_text("Initial spec content.")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('time.time')
    @patch('main.run_test')
    @patch('main.run_agent_task', new_callable=AsyncMock)
    @patch('main.Observer')
    @patch('asyncio.run_coroutine_threadsafe')
    async def test_develop_mode_triggers_agent_and_tests_on_change(
        self, mock_run_coro_threadsafe, mock_observer_cls, mock_run_agent_task, mock_run_test, mock_time
    ):
        """Verify that a file change triggers an agent run followed by a test run."""
        loop = asyncio.get_running_loop()
        # Make run_coroutine_threadsafe schedule a task on the current loop for predictability in tests
        mock_run_coro_threadsafe.side_effect = lambda coro, loop_arg: loop.create_task(coro)

        mock_observer_instance = mock_observer_cls.return_value
        mock_handler_instance = MagicMock()
        def store_handler(handler, path, recursive):
            mock_handler_instance.handler = handler
        mock_observer_instance.schedule.side_effect = store_handler

        # --- Initial Run ---
        mock_time.return_value = 1000.0
        async def develop_task():
            args = argparse.Namespace(
                command='develop', spec=self.spec_file, project_dir=self.project_dir,
                agent='gemini', model=None, verbose=False, profile=None
            )
            # We expect this to loop until cancelled
            with self.assertRaises(asyncio.CancelledError):
                await main.run_develop(args)

        develop_future = loop.create_task(develop_task())
        await asyncio.sleep(0) # Allow initial run to start
        self.assertEqual(mock_run_agent_task.call_count, 1)
        self.assertEqual(mock_run_test.call_count, 1)
        mock_run_agent_task.reset_mock()
        mock_run_test.reset_mock()

        # --- Simulate a File Change ---
        mock_time.return_value = 1003.0  # More than debounce period of 2.0
        mock_event = MagicMock(src_path=str(self.spec_file))
        actual_handler = mock_handler_instance.handler
        actual_handler.on_modified(mock_event)
        await asyncio.sleep(0)  # Yield to allow the scheduled task to run

        # --- Assertions for second run ---
        await asyncio.sleep(0)
        self.assertEqual(mock_run_agent_task.call_count, 1, "Agent task should run again after change")
        self.assertEqual(mock_run_test.call_count, 1, "Test run should run again after change")

        # --- Cleanup ---
        develop_future.cancel()


    @patch('time.time')
    @patch('main.run_test')
    @patch('main.run_agent_task', new_callable=AsyncMock)
    @patch('main.Observer')
    @patch('asyncio.run_coroutine_threadsafe')
    async def test_develop_mode_debounces_rapid_changes(
        self, mock_run_coro_threadsafe, mock_observer_cls, mock_run_agent_task, mock_run_test, mock_time
    ):
        """Verify that rapid file changes only trigger one agent run due to debouncing."""
        loop = asyncio.get_running_loop()
        mock_run_coro_threadsafe.side_effect = lambda coro, loop_arg: loop.create_task(coro)

        mock_observer_instance = mock_observer_cls.return_value
        mock_handler_instance = MagicMock()
        def store_handler(handler, path, recursive):
            mock_handler_instance.handler = handler
        mock_observer_instance.schedule.side_effect = store_handler

        # --- Initial Run ---
        mock_time.return_value = 1000.0
        async def develop_task():
            args = argparse.Namespace(
                command='develop', spec=self.spec_file, project_dir=self.project_dir,
                agent='gemini', model=None, verbose=False, profile=None
            )
            with self.assertRaises(asyncio.CancelledError):
                await main.run_develop(args)

        develop_future = loop.create_task(develop_task())
        await asyncio.sleep(0)
        self.assertEqual(mock_run_agent_task.call_count, 1, "Initial run should happen once")
        mock_run_agent_task.reset_mock()
        mock_run_test.reset_mock()

        # --- Simulate Rapid File Changes ---
        actual_handler = mock_handler_instance.handler
        mock_event = MagicMock(src_path=str(self.spec_file))

        # First modification (after debounce period)
        mock_time.return_value = 1003.0
        actual_handler.on_modified(mock_event)
        await asyncio.sleep(0)

        # Second modification (within debounce period)
        mock_time.return_value = 1003.5
        actual_handler.on_modified(mock_event)
        await asyncio.sleep(0)

        # Third modification (still within debounce period of the first change)
        mock_time.return_value = 1004.0
        actual_handler.on_modified(mock_event)
        await asyncio.sleep(0)

        # --- Assertions ---
        # Check that only one run was triggered by the series of changes
        self.assertEqual(mock_run_agent_task.call_count, 1, "Should only be called once for rapid changes")
        self.assertEqual(mock_run_test.call_count, 1, "Tests should also only run once")

        # --- Cleanup ---
        develop_future.cancel()

if __name__ == '__main__':
    unittest.main()

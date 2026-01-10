import sys
from pathlib import Path
import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import time
import argparse
import shutil

# Add project root to path to allow direct import of main
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_develop, SpecChangeHandler

class TestDevelopCommand(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project_develop")
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.spec_file = self.project_dir / "app_spec.txt"
        self.spec_file.write_text("Initial spec")

        self.args = argparse.Namespace(
            spec=self.spec_file,
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            profile=None,
            max_iterations=10,
            verbose=False,
            dashboard_url="http://localhost:7654",
        )

import shutil

class TestDevelopCommand(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)
        self.spec_file = self.project_dir / "app_spec.txt"
        self.spec_file.write_text("Initial spec")

        self.args = argparse.Namespace(
            spec=self.spec_file,
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            profile=None,
            max_iterations=10,
            verbose=False,
            dashboard_url="http://localhost:7654",
        )

    def tearDown(self):
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    @patch("main.sys.exit")
    @patch("main.Observer")
    @patch("main.run_agent_task", new_callable=AsyncMock)
    @patch("main.run_test")
    @patch("main.ensure_config_exists")
    @patch("main.load_config_from_file")
    async def test_run_develop_starts_and_watches(
        self, mock_load_config, mock_ensure_config, mock_run_test, mock_run_agent_task, mock_observer, mock_sys_exit
    ):
        mock_load_config.return_value = {}
        observer_instance = mock_observer.return_value

        develop_task = asyncio.create_task(run_develop(self.args))

        # Allow the task to start and run the initial cycle
        await asyncio.sleep(0.1)

        # Cancel the task to break the infinite loop
        develop_task.cancel()

        # The task will be cancelled, so we expect a CancelledError
        with self.assertRaises(asyncio.CancelledError):
            await develop_task

        # Verify that the observer was started and watching the correct path
        observer_instance.schedule.assert_called_once()
        observer_instance.start.assert_called_once()

        # The finally block in run_develop should call stop and join
        observer_instance.stop.assert_called_once()
        observer_instance.join.assert_called_once()

        # Check that the initial run was triggered
        mock_run_agent_task.assert_called_once()
        mock_run_test.assert_called_once()

    @patch("asyncio.run_coroutine_threadsafe")
    async def test_spec_change_handler_on_modified(self, mock_run_coroutine):
        handler = SpecChangeHandler(self.args, MagicMock(spec_file=self.spec_file))
        # Manually assign the loop in the test context
        handler.loop = asyncio.get_running_loop()

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(self.spec_file.resolve())

        # Simulate a file modification event
        handler.on_modified(mock_event)

        # Assert that the async dev cycle was scheduled to run
        mock_run_coroutine.assert_called_once()

    @patch("main.run_agent_task", new_callable=AsyncMock)
    @patch("main.run_test")
    @patch("main.ensure_git_safe")
    async def test_dev_cycle_runs_agent_and_tests(self, mock_ensure_git, mock_run_test, mock_run_agent_task):
        config = MagicMock(
            spec_file=self.spec_file,
            project_dir=self.project_dir,
            agent_type="gemini"
        )
        handler = SpecChangeHandler(self.args, config)

        await handler.run_dev_cycle()

        mock_ensure_git.assert_called_once()
        mock_run_agent_task.assert_called_once()
        mock_run_test.assert_called_once()

if __name__ == "__main__":
    unittest.main()

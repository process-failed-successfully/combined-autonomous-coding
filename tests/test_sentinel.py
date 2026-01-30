import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import time
import asyncio
import sys

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.sentinel import Sentinel, SentinelEventHandler

class TestSentinelEventHandler(unittest.TestCase):
    def test_debounce(self):
        """Verify that multiple events within debounce time only trigger callback once."""
        callback = MagicMock()
        project_dir = Path("/tmp")
        # Increase debounce time to avoid flakiness in slow CI environments
        handler = SentinelEventHandler(project_dir, callback, debounce_seconds=0.5)

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/tmp/file.py"

        # Trigger twice quickly
        handler.on_modified(mock_event)
        handler.on_modified(mock_event)

        callback.assert_called_once()

        # Wait and trigger again
        time.sleep(0.6)
        handler.on_modified(mock_event)
        self.assertEqual(callback.call_count, 2)

    def test_ignore_patterns(self):
        """Verify ignored files do not trigger callback."""
        callback = MagicMock()
        project_dir = Path("/tmp")
        handler = SentinelEventHandler(project_dir, callback)

        mock_event = MagicMock()
        mock_event.is_directory = False

        # Ignored paths
        for p in [".git/HEAD", "__pycache__/x.pyc", ".venv/lib/site.py"]:
            mock_event.src_path = f"/tmp/{p}"
            handler.on_modified(mock_event)

        callback.assert_not_called()

        # Valid path
        mock_event.src_path = "/tmp/src/main.py"
        handler.on_modified(mock_event)
        callback.assert_called_once()

class TestSentinel(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/project")

        # Patch dependencies
        self.patcher_obs = patch("shared.sentinel.Observer")
        self.mock_observer_cls = self.patcher_obs.start()
        self.mock_observer = self.mock_observer_cls.return_value

        self.patcher_tm = patch("shared.sentinel.TroubleshootManager")
        self.mock_tm_cls = self.patcher_tm.start()
        self.mock_tm = self.mock_tm_cls.return_value

        # Patch verify functions
        self.patcher_lint = patch("shared.sentinel.run_lint")
        self.mock_run_lint = self.patcher_lint.start()

        self.patcher_tests = patch("shared.sentinel.run_tests")
        self.mock_run_tests = self.patcher_tests.start()

    def tearDown(self):
        patch.stopall()

    def test_start(self):
        """Test Sentinel start triggers observer."""
        sentinel = Sentinel(self.project_dir)

        # Mock time.sleep to raise KeyboardInterrupt to exit loop immediately
        with patch("time.sleep", side_effect=KeyboardInterrupt):
            sentinel.start()

        self.mock_observer.schedule.assert_called()
        self.mock_observer.start.assert_called()
        self.mock_observer.stop.assert_called()

    async def test_run_cycle_success(self):
        """Test run_cycle when checks pass."""
        sentinel = Sentinel(self.project_dir, checks=["lint", "test"])

        self.mock_run_lint.return_value = {"success": True}
        self.mock_run_tests.return_value = {"success": True}

        await sentinel.run_cycle()

        # Should NOT initialize TroubleshootManager if auto_fix is False (default)
        self.mock_tm_cls.assert_not_called()

    async def test_run_cycle_failure_no_fix(self):
        """Test run_cycle failure without auto-fix."""
        sentinel = Sentinel(self.project_dir, checks=["lint"], auto_fix=False)

        self.mock_run_lint.return_value = {"success": False, "stderr": "Error"}

        await sentinel.run_cycle()

        self.mock_tm_cls.assert_not_called()

    async def test_run_cycle_failure_auto_fix(self):
        """Test run_cycle failure with auto-fix."""
        sentinel = Sentinel(self.project_dir, checks=["lint"], auto_fix=True)

        self.mock_run_lint.return_value = {"success": False, "stderr": "Error"}

        # Mock diagnosis and fix
        self.mock_tm.diagnose = AsyncMock(return_value="Diagnosis")
        self.mock_tm.apply_fix = AsyncMock(return_value="Fixed")

        # Re-inject mocked TroubleshootManager instance since it's created in __init__
        # Actually, Sentinel creates it in __init__, so self.mock_tm is correct if patch was active during __init__
        # Yes, setUp patches it before test runs.

        await sentinel.run_cycle()

        self.mock_tm.diagnose.assert_awaited()
        self.mock_tm.apply_fix.assert_awaited()

if __name__ == "__main__":
    unittest.main()

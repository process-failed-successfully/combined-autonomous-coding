import unittest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
import sys
import argparse
import asyncio

from shared.optimize import OptimizationManager, run_optimize_logic

class TestOptimizationManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("./test_project_optimize")
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.target_script = self.project_dir / "slow_script.py"
        self.target_script.write_text("""
import time
def slow_function():
    time.sleep(0.1)

if __name__ == "__main__":
    slow_function()
""")

    def tearDown(self):
        import shutil
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    @patch("shared.optimize.GeminiAgent")
    @patch("shared.optimize.subprocess.run")
    async def test_optimize_script_success(self, mock_subprocess, MockAgent):
        # Setup mocks
        mock_agent_instance = MockAgent.return_value
        f = asyncio.Future()
        f.set_result(("response", "AI analysis", "cost"))
        mock_agent_instance.run_agent_session.return_value = f

        stats_file = self.project_dir / ".profile.stats"
        import cProfile
        cProfile.run("print('hello')", str(stats_file))

        manager = OptimizationManager(self.project_dir)

        # Run
        result = await manager.optimize_script(
            script_path=self.target_script,
            script_args=[],
            agent_type="gemini"
        )

        self.assertTrue(result)

        expected_cmd = [sys.executable, "-m", "cProfile", "-o", str(stats_file), str(self.target_script.resolve())]
        mock_subprocess.assert_called_with(expected_cmd, cwd=self.project_dir, check=True)

        MockAgent.assert_called()
        mock_agent_instance.run_agent_session.assert_called()

        self.assertFalse(stats_file.exists())

    async def test_optimize_script_not_found(self):
        manager = OptimizationManager(self.project_dir)
        result = await manager.optimize_script(Path("non_existent.py"))
        self.assertFalse(result)

    @patch("shared.optimize.OptimizationManager")
    async def test_run_optimize_logic(self, MockManager):
        mock_instance = MockManager.return_value
        f = asyncio.Future()
        f.set_result(True)
        mock_instance.optimize_script.return_value = f

        args = argparse.Namespace(
            project_dir=self.project_dir,
            script="slow_script.py",
            args=["--verbose"],
            agent="gemini",
            model=None,
            limit=10
        )

        await run_optimize_logic(args)

        MockManager.assert_called_with(self.project_dir)
        mock_instance.optimize_script.assert_called_with(
            script_path=self.project_dir / "slow_script.py",
            script_args=["--verbose"],
            agent_type="gemini",
            model=None,
            limit=10
        )

if __name__ == "__main__":
    unittest.main()

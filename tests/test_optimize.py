import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import sys
import cProfile
from shared.optimize import OptimizationManager

# Ensure agents.gemini is imported so patch finds it
import agents.gemini

class TestOptimizationManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = OptimizationManager(self.test_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    @patch('shared.optimize.subprocess.run')
    def test_run_profile_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        script = Path("myscript.py")

        stats_file = self.manager.run_profile(script, ["--arg"])

        self.assertEqual(stats_file, self.test_dir / ".agent_profile.stats")
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertIn("-m", cmd)
        self.assertIn("cProfile", cmd)
        self.assertIn(str(script), cmd)

    @patch('shared.optimize.subprocess.run')
    def test_run_profile_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="Error")

        stats_file = self.manager.run_profile(Path("myscript.py"), [])
        self.assertIsNone(stats_file)

    def test_analyze_stats_real(self):
        # Create a dummy profile
        def slow():
            total = 0
            for i in range(1000):
                total += i

        stats_file = self.test_dir / "test.stats"
        cProfile.runctx('slow()', globals(), locals(), filename=str(stats_file))

        funcs = self.manager.analyze_stats(stats_file)
        self.assertTrue(len(funcs) > 0)
        found = any(f['name'] == 'slow' for f in funcs)
        self.assertTrue(found)

    @patch('agents.gemini.GeminiAgent')
    async def test_optimize_flow(self, mock_agent_cls):
        # 1. Setup Mock Agent
        mock_agent = AsyncMock()
        mock_agent.run_agent_session.return_value = ("COMPLETED", "Optimization Suggestion", [])
        mock_agent_cls.return_value = mock_agent

        # We DO NOT mock get_optimize_prompt to verify it works

        # 2. Setup Mock Stats and Source
        with patch.object(self.manager, 'run_profile') as mock_run_profile:
            mock_run_profile.return_value = self.test_dir / ".agent_profile.stats"

            with patch.object(self.manager, 'analyze_stats') as mock_analyze:
                mock_analyze.return_value = [
                    {
                        "filename": "myscript.py",
                        "line": 10,
                        "name": "slow_func",
                        "ncalls": 100,
                        "tottime": 5.0,
                        "cumtime": 5.0
                    }
                ]

                with patch.object(self.manager, 'get_source_code') as mock_get_source:
                    mock_get_source.return_value = "def slow_func(): pass"

                    # 3. Run
                    script_path = self.test_dir / "myscript.py"
                    script_path.touch()

                    # Note: We need to use "gemini" agent which maps to GeminiAgent
                    result = await self.manager.optimize(Path("myscript.py"), [])

                    self.assertTrue(result)
                    mock_agent_cls.assert_called_once()
                    mock_agent.run_agent_session.assert_awaited_once()

                    call_args = mock_agent.run_agent_session.call_args[0][0]
                    # Verify real prompt loaded
                    self.assertIn("expert Python Performance Engineer", call_args) # From actual prompt file
                    self.assertIn("slow_func", call_args)

    def test_get_source_code(self):
        script_content = """
def func1():
    pass

def func2():
    print("hello")
"""
        script_path = self.test_dir / "source_test.py"
        script_path.write_text(script_content)

        # Line 5 is func2
        code = self.manager.get_source_code("source_test.py", 5)
        self.assertIn("def func2():", code)
        self.assertIn('print("hello")', code)

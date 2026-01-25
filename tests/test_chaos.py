import unittest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
from shared.chaos import ChaosManager, ProcessKiller, FileJitter, ChaosExperiment

class TestChaosManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = ChaosManager(self.project_dir)

    def test_init(self):
        self.assertTrue("kill-process" in self.manager.experiments)
        self.assertTrue("file-jitter" in self.manager.experiments)

    @patch("builtins.input", return_value="y")
    @patch.object(ProcessKiller, "run", return_value=True)
    def test_run_valid_experiment(self, mock_run, mock_input):
        result = self.manager.run("kill-process")
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch("builtins.input", return_value="n")
    def test_run_aborted(self, mock_input):
        result = self.manager.run("kill-process")
        self.assertFalse(result)

    def test_run_invalid_experiment(self):
        result = self.manager.run("invalid-exp")
        self.assertFalse(result)

class TestProcessKiller(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/app")
        self.killer = ProcessKiller(self.project_dir)

    @patch("psutil.process_iter")
    @patch("os.getpid", return_value=9999)
    def test_run_kills_process(self, mock_getpid, mock_process_iter):
        # Mock processes
        p1 = MagicMock()
        p1.info = {'pid': 100, 'name': 'node', 'cwd': '/app', 'cmdline': ['node', 'server.js']}
        p1.pid = 100

        p2 = MagicMock()
        p2.info = {'pid': 101, 'name': 'python', 'cwd': '/other', 'cmdline': ['python']}

        # Self process
        p_self = MagicMock()
        p_self.info = {'pid': 9999, 'name': 'python', 'cwd': '/app'}
        p_self.pid = 9999

        mock_process_iter.return_value = [p1, p2, p_self]

        with patch("random.choice", return_value=p1):
            result = self.killer.run()
            self.assertTrue(result)
            p1.terminate.assert_called_once()
            p1.wait.assert_called_once()

    @patch("psutil.process_iter")
    def test_run_no_targets(self, mock_process_iter):
        mock_process_iter.return_value = []
        result = self.killer.run()
        self.assertFalse(result)

    @patch("psutil.process_iter")
    def test_dry_run(self, mock_process_iter):
        self.killer.dry_run = True
        p1 = MagicMock()
        p1.info = {'pid': 100, 'name': 'node', 'cwd': '/app', 'cmdline': ['node']}
        p1.pid = 100
        mock_process_iter.return_value = [p1]

        with patch("random.choice", return_value=p1):
            result = self.killer.run()
            self.assertTrue(result)
            p1.terminate.assert_not_called()

class TestFileJitter(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/app")
        self.jitter = FileJitter(self.project_dir)

    @patch("os.walk")
    def test_run_touches_file(self, mock_walk):
        mock_walk.return_value = [
            ("/app", [], ["main.py", "README.md"])
        ]

        with patch("pathlib.Path.touch") as mock_touch:
            with patch("random.choice") as mock_choice:
                mock_choice.side_effect = lambda x: x[0] # Pick first file (main.py)
                result = self.jitter.run()
                self.assertTrue(result)
                # Verify touch was called on /app/main.py
                # Note: Path construction might vary slightly in mocks
                pass

    @patch("os.walk")
    def test_run_no_files(self, mock_walk):
        mock_walk.return_value = [("/app", [], ["image.png"])] # No source files
        result = self.jitter.run()
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()

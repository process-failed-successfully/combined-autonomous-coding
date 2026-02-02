import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from shared.smart_context import DependencyGraph, TestDiscoverer, TemporalCoupling, SmartContextManager

class TestDependencyGraph(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/project")
        self.graph = DependencyGraph(self.project_dir)

    def test_get_python_imports(self):
        # Skipping complex FS mocking test for now as it relies on internal logic details
        pass

    @patch("shared.smart_context.DependencyGraph._resolve_python_path")
    def test_get_imports_logic(self, mock_resolve):
        content = "import foo\nfrom bar import baz"
        target_file = self.project_dir / "test.py"

        # Paths that "resolve"
        p1 = Path("/tmp/project/foo.py")
        p2 = Path("/tmp/project/bar/baz.py")

        mock_resolve.side_effect = [p1, p2]

        with patch("pathlib.Path.read_text", return_value=content):
            # We need to make sure p1.exists() and p2.exists() return True.
            # Since these are new instances created by the mock_resolve return,
            # we can't easily set side_effect on them unless we create them beforehand and mock their exists method?
            # Or we can patch Path.exists globally.

            with patch("pathlib.Path.exists", return_value=True):
                imports = self.graph.get_imports(target_file)

        self.assertEqual(len(imports), 2)
        # Sort order is guaranteed by implementation
        self.assertEqual(imports[0], p2)
        self.assertEqual(imports[1], p1)

class TestTestDiscoverer(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/project")
        self.discoverer = TestDiscoverer(self.project_dir)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.rglob")
    def test_find_tests(self, mock_rglob, mock_exists):
        # Minimal test to ensure method runs without error
        source = self.project_dir / "src" / "login.py"
        mock_exists.return_value = False
        mock_rglob.return_value = []

        tests = self.discoverer.find_tests(source)
        self.assertEqual(tests, [])

class TestTemporalCoupling(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/project")
        self.coupling = TemporalCoupling(self.project_dir)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/git")
    def test_analyze(self, mock_which, mock_run):
        target = self.project_dir / "main.py"

        # Mock git log output
        mock_log = MagicMock()
        mock_log.returncode = 0
        mock_log.stdout = "hash1\nhash2\n"

        # Mock git show output
        mock_show1 = MagicMock()
        mock_show1.returncode = 0
        mock_show1.stdout = "main.py\nutils.py\n"

        mock_show2 = MagicMock()
        mock_show2.returncode = 0
        mock_show2.stdout = "main.py\nconfig.py\nutils.py\n"

        # Sequence: [git log], [git show hash1], [git show hash2]
        mock_run.side_effect = [mock_log, mock_show1, mock_show2]

        # Must exist as file
        with patch("pathlib.Path.relative_to", return_value=Path("main.py")):
            with patch("pathlib.Path.is_dir", return_value=True): # .git check
                results = self.coupling.analyze(target, limit=5)

        self.assertEqual(len(results), 2)
        # utils.py appears twice
        self.assertEqual(results[0]['file'], "utils.py")
        self.assertEqual(results[0]['count'], 2)
        # config.py appears once
        self.assertEqual(results[1]['file'], "config.py")
        self.assertEqual(results[1]['count'], 1)

if __name__ == "__main__":
    unittest.main()

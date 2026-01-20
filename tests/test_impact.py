import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.impact import ImpactAnalyzer, run_impact_logic

class TestImpactAnalyzer(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.analyzer = ImpactAnalyzer(self.project_dir)

    def test_resolve_import_file(self):
        self.analyzer.files_map = {
            "shared/utils.py": self.project_dir / "shared/utils.py",
            "main.py": self.project_dir / "main.py"
        }

        resolved = self.analyzer._resolve_import("shared.utils", self.project_dir / "main.py")
        self.assertEqual(resolved, "shared/utils.py")

    def test_resolve_import_init(self):
        self.analyzer.files_map = {
            "shared/__init__.py": self.project_dir / "shared/__init__.py",
            "main.py": self.project_dir / "main.py"
        }

        resolved = self.analyzer._resolve_import("shared", self.project_dir / "main.py")
        self.assertEqual(resolved, "shared/__init__.py")

    def test_find_impacted_files(self):
        # A -> B -> C
        # TestA -> A

        self.analyzer.reverse_dependencies = {
            "file_c.py": {"file_b.py"},
            "file_b.py": {"file_a.py"},
            "file_a.py": {"tests/test_a.py"}
        }

        changed = ["file_c.py"]
        impacted_source, impacted_tests = self.analyzer.find_impacted_files(changed)

        self.assertIn("file_b.py", impacted_source)
        self.assertIn("file_a.py", impacted_source)
        self.assertIn("tests/test_a.py", impacted_tests)
        self.assertIn("file_c.py", impacted_source) # It impacts itself/dependents

    @patch("shared.impact.shutil.which")
    @patch("shared.impact.subprocess.run")
    def test_get_changed_files(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/git"

        # Mock git diff output
        mock_diff_proc = MagicMock()
        mock_diff_proc.stdout = "shared/utils.py\nmain.py"
        mock_diff_proc.returncode = 0

        # Mock git ls-files output
        mock_ls_proc = MagicMock()
        mock_ls_proc.stdout = "new_file.py"
        mock_ls_proc.returncode = 0

        mock_run.side_effect = [mock_diff_proc, mock_ls_proc]

        # Mock file existence
        with patch.object(Path, "exists", return_value=True):
            changed = self.analyzer.get_changed_files()

        self.assertIn("shared/utils.py", changed)
        self.assertIn("main.py", changed)
        self.assertIn("new_file.py", changed)

if __name__ == "__main__":
    unittest.main()

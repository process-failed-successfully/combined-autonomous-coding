import unittest
from unittest.mock import patch, MagicMock, ANY, call
from pathlib import Path
import sys

# Ensure main is importable
from main import run_test

class TestMainSmartTest(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.args = MagicMock()
        self.args.project_dir = self.project_dir
        self.args.test_args = []
        self.args.smart = True

    @patch("main.subprocess.run")
    @patch("main.sys.exit")
    @patch("main.ImpactAnalyzer")
    @patch("main.shutil.which")
    def test_run_test_smart_python(self, mock_which, mock_impact_cls, mock_exit, mock_run):
        # Make sys.exit raise SystemExit to stop execution flow
        mock_exit.side_effect = SystemExit

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = lambda: False

            mock_which.return_value = "/usr/bin/pytest"

            mock_dir = MagicMock()
            self.args.project_dir = mock_dir
            mock_dir.resolve.return_value = mock_dir

            mock_package_json = MagicMock()
            mock_package_json.exists.return_value = False

            mock_pyproject = MagicMock()
            mock_pyproject.exists.return_value = False

            mock_requirements = MagicMock()
            mock_requirements.exists.return_value = True

            def div_side_effect(other):
                if other == "package.json":
                    return mock_package_json
                if other == "pyproject.toml":
                    return mock_pyproject
                if other == "requirements.txt":
                    return mock_requirements
                return MagicMock()

            mock_dir.__truediv__.side_effect = div_side_effect

            # Setup ImpactAnalyzer mock
            mock_analyzer = mock_impact_cls.return_value
            mock_analyzer.get_changed_files.return_value = ["changed_file.py"]
            mock_analyzer.find_impacted_files.return_value = (set(), {"tests/test_impacted.py"})

            # Mock subprocess.run to return successful result
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Run and expect SystemExit
            with self.assertRaises(SystemExit):
                run_test(self.args)

            # Verify
            mock_impact_cls.assert_called()
            mock_analyzer.build_graph.assert_called_once()
            mock_analyzer.find_impacted_files.assert_called_once()

            # Check command
            mock_run.assert_called_with(["pytest", "tests/test_impacted.py"], cwd=mock_dir)
            mock_exit.assert_called_with(0)

    @patch("main.subprocess.run")
    @patch("main.sys.exit")
    @patch("main.ImpactAnalyzer")
    @patch("main.shutil.which")
    def test_run_test_smart_no_impact(self, mock_which, mock_impact_cls, mock_exit, mock_run):
        mock_exit.side_effect = SystemExit

        mock_which.return_value = "/usr/bin/pytest"

        mock_dir = MagicMock()
        self.args.project_dir = mock_dir
        mock_dir.resolve.return_value = mock_dir

        mock_package_json = MagicMock()
        mock_package_json.exists.return_value = False
        mock_requirements = MagicMock()
        mock_requirements.exists.return_value = True

        def div_side_effect(other):
            if other == "package.json":
                return mock_package_json
            if other == "requirements.txt":
                return mock_requirements
            return MagicMock()

        mock_dir.__truediv__.side_effect = div_side_effect

        mock_analyzer = mock_impact_cls.return_value
        mock_analyzer.get_changed_files.return_value = ["changed_file.py"]
        mock_analyzer.find_impacted_files.return_value = (set(), set()) # No tests impacted

        with self.assertRaises(SystemExit):
            run_test(self.args)

        # Should exit with 0
        mock_exit.assert_called_with(0)
        mock_run.assert_not_called()

if __name__ == "__main__":
    unittest.main()

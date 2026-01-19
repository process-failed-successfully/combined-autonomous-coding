
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Add repo root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.coverage import run_coverage_logic, check_dependencies, parse_coverage_xml

class TestCoverage(unittest.TestCase):

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_check_dependencies_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/pytest"
        mock_run.return_value.stdout = "options:\n  --cov=SOURCE"

        self.assertTrue(check_dependencies())

    @patch("shutil.which")
    def test_check_dependencies_missing_pytest(self, mock_which):
        mock_which.return_value = None
        self.assertFalse(check_dependencies())

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_check_dependencies_missing_plugin(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/pytest"
        mock_run.return_value.stdout = "options:\n  --verbose" # No --cov

        self.assertFalse(check_dependencies())

    @patch("shared.coverage.check_dependencies")
    @patch("subprocess.run")
    def test_run_coverage_success(self, mock_run, mock_check):
        mock_check.return_value = True
        mock_run.return_value.returncode = 0

        success = run_coverage_logic(Path("."))
        self.assertTrue(success)

        # Verify call args
        args = mock_run.call_args[0][0]
        self.assertIn("pytest", args)
        self.assertIn("--cov-report=term-missing", args)

    @patch("shared.coverage.check_dependencies")
    @patch("subprocess.run")
    def test_run_coverage_failure(self, mock_run, mock_check):
        mock_check.return_value = True
        mock_run.return_value.returncode = 1 # Failure

        success = run_coverage_logic(Path("."))
        self.assertFalse(success)

    @patch("shared.coverage.check_dependencies")
    @patch("subprocess.run")
    def test_run_coverage_options(self, mock_run, mock_check):
        mock_check.return_value = True
        mock_run.return_value.returncode = 0

        run_coverage_logic(
            Path("."),
            html_report=True,
            xml_report=True,
            fail_under=80,
            test_args=["-v"]
        )

        args = mock_run.call_args[0][0]
        self.assertIn("--cov-report=html", args)
        self.assertIn("--cov-report=xml", args)
        self.assertIn("--cov-fail-under=80", args)
        self.assertIn("-v", args)

    @patch("xml.etree.ElementTree.parse")
    def test_parse_coverage_xml(self, mock_parse):
        mock_root = MagicMock()
        mock_root.attrib = {"line-rate": "0.85", "branch-rate": "0.75"}
        mock_root.findall.return_value = [1, 2, 3] # Mock list of elements

        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree

        # Mock Path.exists to return True
        with patch("pathlib.Path.exists", return_value=True):
            result = parse_coverage_xml(Path("coverage.xml"))

        self.assertEqual(result["total_coverage"], 85.0)
        self.assertEqual(result["line_rate"], 0.85)

if __name__ == "__main__":
    unittest.main()

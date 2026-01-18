import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from io import StringIO
from shared.coverage import (
    parse_coverage_xml,
    run_tests_with_coverage,
    get_coverage_color,
    display_coverage_report,
    CoverageStats
)

class TestCoverage(unittest.TestCase):
    def test_display_coverage_report(self):
        stats = [
            CoverageStats("file1.py", 100, 10, 90.0),
            CoverageStats("file2.py", 50, 40, 20.0),
        ]

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            display_coverage_report(stats)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()

        self.assertIn("Code Coverage Report", output)
        self.assertIn("file1.py", output)
        self.assertIn("file2.py", output)
        self.assertIn("90.00%", output)
        self.assertIn("20.00%", output)
        # Check colors
        self.assertIn("92m", output) # Green for 90%
        self.assertIn("91m", output) # Red for 20%

    def test_get_coverage_color(self):
        self.assertIn("92m", get_coverage_color(90))
        self.assertIn("93m", get_coverage_color(60))
        self.assertIn("91m", get_coverage_color(30))

    @patch("xml.etree.ElementTree.parse")
    def test_parse_coverage_xml(self, mock_parse):
        # Mock XML structure
        # <coverage>
        #   <packages>
        #     <package>
        #       <classes>
        #         <class filename="test.py">
        #           <lines>
        #             <line hits="1"/>
        #             <line hits="0"/>
        #           </lines>
        #         </class>
        #       </classes>
        #     </package>
        #   </packages>
        # </coverage>

        mock_tree = MagicMock()
        mock_root = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree

        mock_package = MagicMock()
        mock_class = MagicMock()
        mock_class.get.return_value = "test.py"

        mock_lines = MagicMock()
        mock_line1 = MagicMock()
        mock_line1.get.return_value = "1"
        mock_line2 = MagicMock()
        mock_line2.get.return_value = "0"

        mock_lines.findall.return_value = [mock_line1, mock_line2]
        mock_class.find.return_value = mock_lines

        mock_package.findall.return_value = [mock_class]
        mock_root.findall.return_value = [mock_package]

        # Sources mock
        mock_root.find.return_value = None

        with patch.object(Path, "exists", return_value=True):
            stats = parse_coverage_xml(Path("dummy.xml"))

        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0].file, "test.py")
        self.assertEqual(stats[0].statements, 2)
        self.assertEqual(stats[0].missed, 1)
        self.assertEqual(stats[0].percent, 50.0)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_tests_with_coverage_python(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/pytest"
        project_dir = Path("/tmp/project")

        # Mock file existence checks
        with patch.object(Path, "exists") as mock_exists:
            # pyproject.toml exists, coverage.xml exists after run
            mock_exists.side_effect = lambda: True

            report = run_tests_with_coverage(project_dir)

            self.assertEqual(report, project_dir / "coverage.xml")
            mock_run.assert_called_with(
                ["pytest", "--cov=.", "--cov-report=xml:coverage.xml", "--cov-report=term-missing"],
                cwd=project_dir,
                check=False
            )

    @patch("subprocess.run")
    def test_run_tests_with_coverage_no_project(self, mock_run):
        project_dir = Path("/tmp/empty")
        with patch.object(Path, "exists", return_value=False):
            report = run_tests_with_coverage(project_dir)
            self.assertIsNone(report)

if __name__ == "__main__":
    unittest.main()

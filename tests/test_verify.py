
import unittest
from unittest.mock import patch
from pathlib import Path
from shared.verify import run_verify_logic


class TestVerify(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch("shared.verify.check_dependencies")
    @patch("shared.verify.run_lint")
    @patch("shared.verify.run_type_check")
    @patch("shared.verify.run_security_scan")
    @patch("shared.verify.run_tests")
    def test_run_verify_all_success(self, mock_tests, mock_security, mock_type, mock_lint, mock_deps):
        mock_deps.return_value = []
        mock_lint.return_value = {"check": "lint", "success": True, "stdout": "ok", "stderr": ""}
        mock_type.return_value = {"check": "type", "success": True, "stdout": "ok", "stderr": ""}
        mock_security.return_value = {"check": "security", "success": True, "stdout": "ok", "stderr": ""}
        mock_tests.return_value = {"check": "test", "success": True, "stdout": "ok", "stderr": ""}

        success = run_verify_logic(self.project_dir, output_format="text")
        self.assertTrue(success)
        mock_lint.assert_called_once()
        mock_type.assert_called_once()
        mock_security.assert_called_once()
        mock_tests.assert_called_once()

    @patch("shared.verify.check_dependencies")
    @patch("shared.verify.run_lint")
    def test_run_verify_lint_failure(self, mock_lint, mock_deps):
        mock_deps.return_value = []
        mock_lint.return_value = {"check": "lint", "success": False, "stdout": "fail", "stderr": ""}

        success = run_verify_logic(self.project_dir, checks=["lint"], output_format="text")
        self.assertFalse(success)
        mock_lint.assert_called_once()

    @patch("shared.verify.check_dependencies")
    def test_run_verify_missing_deps(self, mock_deps):
        mock_deps.return_value = ["flake8"]
        success = run_verify_logic(self.project_dir, output_format="text")
        self.assertFalse(success)

    @patch("shared.verify.check_dependencies")
    @patch("shared.verify.run_lint")
    @patch("shared.verify.run_type_check")
    def test_run_verify_subset(self, mock_type, mock_lint, mock_deps):
        mock_deps.return_value = []
        mock_lint.return_value = {"check": "lint", "success": True, "stdout": "", "stderr": ""}

        run_verify_logic(self.project_dir, checks=["lint"], output_format="text")
        mock_lint.assert_called_once()
        mock_type.assert_not_called()

    @patch("shared.verify.check_dependencies")
    @patch("shared.verify.run_formatter")
    @patch("shared.verify.run_lint")
    def test_run_verify_fix(self, mock_lint, mock_formatter, mock_deps):
        mock_deps.return_value = []
        mock_formatter.return_value = {"check": "format", "success": True, "stdout": "formatted", "stderr": ""}
        mock_lint.return_value = {"check": "lint", "success": True, "stdout": "", "stderr": ""}

        success = run_verify_logic(self.project_dir, checks=["lint"], fix=True, output_format="text")
        self.assertTrue(success)
        mock_formatter.assert_called_once()
        mock_lint.assert_called_once()


if __name__ == "__main__":
    unittest.main()

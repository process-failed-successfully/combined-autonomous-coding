import unittest
from unittest.mock import MagicMock, patch
import sys
import main
from pathlib import Path

class TestMainSecurity(unittest.TestCase):

    @patch("main.SecurityAuditor")
    def test_run_security_defaults(self, mock_auditor_cls):
        # Setup mock
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.run_all.return_value = []

        # Setup args
        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "low"
        args.output = None
        args.ignore_add = None
        args.install_hook = False
        args.fix = False

        # Run command (should exit 0)
        with self.assertRaises(SystemExit) as cm:
            main.run_security(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify calls
        mock_auditor_cls.assert_called_with(Path(".").resolve())
        mock_auditor.run_all.assert_called_with(scan_type="all", severity="low")

    @patch("main.SecurityAuditor")
    def test_run_security_with_findings(self, mock_auditor_cls):
        # Setup mock
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.run_all.return_value = [
            {
                "type": "secret",
                "severity": "HIGH",
                "description": "AWS Key found",
                "file": "config.py",
                "line": 1
            }
        ]

        # Setup args
        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "all"
        args.severity = "low"
        args.output = None
        args.ignore_add = None
        args.install_hook = False
        args.fix = False

        # Run command (should exit 1 because of HIGH severity)
        with self.assertRaises(SystemExit) as cm:
            main.run_security(args)
        self.assertEqual(cm.exception.code, 1)

    @patch("main.SecurityAuditor")
    def test_run_security_output_file(self, mock_auditor_cls):
        # Setup mock
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.run_all.return_value = []

        # Setup args
        output_file = Path("security_report.json")
        args = MagicMock()
        args.project_dir = Path(".")
        args.scan_type = "sast"
        args.severity = "medium"
        args.output = str(output_file)
        args.ignore_add = None
        args.install_hook = False
        args.fix = False

        # Run command
        with self.assertRaises(SystemExit) as cm:
            main.run_security(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify output file creation
        self.assertTrue(output_file.exists())
        output_file.unlink() # Cleanup

    @patch("main.SecurityAuditor")
    @patch("main.install_hooks")
    @patch("shared.config_loader.get_config_path")
    @patch("yaml.safe_load")
    @patch("yaml.dump")
    @patch("builtins.open", new_callable=MagicMock)
    def test_run_security_install_hook(self, mock_open, mock_yaml_dump, mock_yaml_load, mock_get_config_path, mock_install_hooks, mock_auditor_cls):
        # Setup mock
        mock_get_config_path.return_value = Path("agent_config.yaml")
        mock_yaml_load.return_value = {"git_hooks": {"pre-commit": ["lint"]}}
        mock_install_hooks.return_value = True

        # Setup args
        args = MagicMock()
        args.project_dir = Path(".")
        args.install_hook = True
        args.ignore_add = None
        args.fix = False

        # Run command
        with self.assertRaises(SystemExit) as cm:
            main.run_security(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify config update
        mock_yaml_dump.assert_called()
        args, kwargs = mock_yaml_dump.call_args
        config_data = args[0]
        self.assertIn("security --scan-type secrets --severity HIGH", config_data["git_hooks"]["pre-commit"])

        # Verify install call
        mock_install_hooks.assert_called()

    @patch("main.SecurityAuditor")
    @patch("shared.security_fix.SecurityRemediator")
    def test_run_security_fix(self, mock_remediator_cls, mock_auditor_cls):
        # Setup mock
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.run_all.return_value = [{"type": "dependency", "severity": "HIGH"}]

        mock_remediator = mock_remediator_cls.return_value
        mock_remediator.run_remediation.return_value = {
            "fixed": ["pkg1"], "failed": [], "skipped": []
        }

        # Setup args
        args = MagicMock()
        args.project_dir = Path(".")
        args.fix = True
        args.ignore_add = None
        args.install_hook = False
        args.scan_type = "deps"
        args.severity = "high"
        args.dry_run = False
        args.yes = True

        # Run command
        with self.assertRaises(SystemExit) as cm:
            main.run_security(args)

        # Should exit 0 on success
        self.assertEqual(cm.exception.code, 0)

        # Verify calls
        mock_auditor.run_all.assert_called_with(scan_type="deps", severity="high")
        mock_remediator_cls.assert_called_once()
        mock_remediator.run_remediation.assert_called_with(
            mock_auditor.run_all.return_value,
            dry_run=False,
            yes=True
        )

if __name__ == "__main__":
    unittest.main()

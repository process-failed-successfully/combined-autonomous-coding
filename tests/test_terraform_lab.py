import unittest
from unittest.mock import patch
from pathlib import Path
import argparse

from shared.terraform_lab import TerraformManager, run_terraform_lab_logic


class TestTerraformLab(unittest.TestCase):
    def setUp(self):
        self.mock_working_dir = Path("/tmp/test_project")

    @patch('shared.terraform_lab.shutil.which')
    def test_check_install_success(self, mock_which):
        mock_which.return_value = "/usr/bin/terraform"
        manager = TerraformManager()
        self.assertTrue(manager.check_install())

    @patch('shared.terraform_lab.shutil.which')
    def test_check_install_failure(self, mock_which):
        mock_which.return_value = None
        manager = TerraformManager()
        self.assertFalse(manager.check_install())

    @patch('shared.terraform_lab.subprocess.run')
    @patch('shared.terraform_lab.shutil.which')
    def test_init(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/terraform"
        mock_run.return_value.returncode = 0

        manager = TerraformManager(working_dir=self.mock_working_dir)
        success = manager.init()

        self.assertTrue(success)
        mock_run.assert_called_with(
            ['/usr/bin/terraform', 'init'],
            cwd=self.mock_working_dir,
            check=False,
            text=True,
            capture_output=False
        )

    @patch('shared.terraform_lab.subprocess.run')
    @patch('shared.terraform_lab.shutil.which')
    def test_init_upgrade(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/terraform"
        mock_run.return_value.returncode = 0

        manager = TerraformManager(working_dir=self.mock_working_dir)
        success = manager.init(upgrade=True)

        self.assertTrue(success)
        mock_run.assert_called_with(
            ['/usr/bin/terraform', 'init', '-upgrade'],
            cwd=self.mock_working_dir,
            check=False,
            text=True,
            capture_output=False
        )

    @patch('shared.terraform_lab.subprocess.run')
    @patch('shared.terraform_lab.shutil.which')
    def test_plan(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/terraform"
        mock_run.return_value.returncode = 0

        manager = TerraformManager(working_dir=self.mock_working_dir)
        success = manager.plan(out_file="plan.tfplan")

        self.assertTrue(success)
        mock_run.assert_called_with(
            ['/usr/bin/terraform', 'plan', '-out', 'plan.tfplan'],
            cwd=self.mock_working_dir,
            check=False,
            text=True,
            capture_output=False
        )

    @patch('shared.terraform_lab.subprocess.run')
    @patch('shared.terraform_lab.shutil.which')
    def test_apply(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/terraform"
        mock_run.return_value.returncode = 0

        manager = TerraformManager(working_dir=self.mock_working_dir)
        success = manager.apply(auto_approve=True)

        self.assertTrue(success)
        mock_run.assert_called_with(
            ['/usr/bin/terraform', 'apply', '-auto-approve'],
            cwd=self.mock_working_dir,
            check=False,
            text=True,
            capture_output=False
        )

    @patch('shared.terraform_lab.subprocess.run')
    @patch('shared.terraform_lab.shutil.which')
    def test_apply_with_plan(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/terraform"
        mock_run.return_value.returncode = 0

        manager = TerraformManager(working_dir=self.mock_working_dir)
        success = manager.apply(plan_file="plan.tfplan")

        self.assertTrue(success)
        mock_run.assert_called_with(
            ['/usr/bin/terraform', 'apply', 'plan.tfplan'],
            cwd=self.mock_working_dir,
            check=False,
            text=True,
            capture_output=False
        )

    @patch('shared.terraform_lab.subprocess.run')
    @patch('shared.terraform_lab.shutil.which')
    def test_output(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/terraform"
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"key": "value"}'

        manager = TerraformManager(working_dir=self.mock_working_dir)
        result = manager.output(json_format=True)

        self.assertEqual(result, '{"key": "value"}')
        mock_run.assert_called_with(
            ['/usr/bin/terraform', 'output', '-json'],
            cwd=self.mock_working_dir,
            check=False,
            text=True,
            capture_output=True
        )

    @patch('shared.terraform_lab.sys.exit')
    @patch('shared.terraform_lab.TerraformManager')
    def test_cli_logic_init(self, MockManager, mock_exit):
        # Setup mock manager instance
        instance = MockManager.return_value
        instance.check_install.return_value = True
        instance.init.return_value = True

        # Setup args
        args = argparse.Namespace(
            action="init",
            upgrade=True,
            project_dir=Path(".")
        )

        run_terraform_lab_logic(args)

        instance.init.assert_called_with(upgrade=True)
        mock_exit.assert_called_with(0)

    @patch('shared.terraform_lab.sys.exit')
    @patch('shared.terraform_lab.TerraformManager')
    def test_cli_logic_missing_install(self, MockManager, mock_exit):
        # Setup mock manager instance
        instance = MockManager.return_value
        instance.check_install.return_value = False
        # Make sys.exit raise SystemExit so execution stops
        mock_exit.side_effect = SystemExit(1)

        # Setup args
        args = argparse.Namespace(
            action="init",
            project_dir=Path(".")
        )

        with self.assertRaises(SystemExit):
            run_terraform_lab_logic(args)

        mock_exit.assert_called_with(1)


if __name__ == '__main__':
    unittest.main()

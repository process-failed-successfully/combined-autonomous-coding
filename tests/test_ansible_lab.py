import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import sys
import shutil

import argparse
from shared.ansible_lab import AnsibleManager, run_ansible_lab_logic

class TestAnsibleLab(unittest.TestCase):
    def setUp(self):
        self.mock_subprocess = patch('subprocess.run').start()
        self.mock_shutil_which = patch('shutil.which').start()
        self.addCleanup(patch.stopall)

        # Default behavior: tools exist
        self.mock_shutil_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"

        self.manager = AnsibleManager()

    def test_check_install(self):
        self.assertTrue(self.manager.check_install())
        self.mock_shutil_which.side_effect = lambda cmd: None
        manager = AnsibleManager()
        self.assertFalse(manager.check_install())

    def test_run_playbook_basic(self):
        self.manager.run_playbook("site.yml")
        self.mock_subprocess.assert_called_with(
            ['/usr/bin/ansible-playbook', 'site.yml'],
            cwd=Path("."),
            check=False,
            text=True,
            capture_output=False
        )

    def test_run_playbook_options(self):
        self.manager.run_playbook(
            "site.yml",
            inventory="hosts",
            check_mode=True,
            diff_mode=True,
            limit="web",
            extra_vars="foo=bar"
        )
        self.mock_subprocess.assert_called_with(
            ['/usr/bin/ansible-playbook', 'site.yml', '-i', 'hosts', '--check', '--diff', '--limit', 'web', '--extra-vars', 'foo=bar'],
            cwd=Path("."),
            check=False,
            text=True,
            capture_output=False
        )

    def test_run_playbook_missing_tool(self):
        self.manager.playbook_cmd = None
        result = self.manager.run_playbook("site.yml")
        self.assertFalse(result)

    def test_lint(self):
        self.manager.lint()
        self.mock_subprocess.assert_called_with(
            ['/usr/bin/ansible-lint', '.'],
            cwd=Path("."),
            check=False,
            text=True,
            capture_output=False
        )

    def test_lint_specific_path(self):
        self.manager.lint("playbooks/")
        self.mock_subprocess.assert_called_with(
            ['/usr/bin/ansible-lint', 'playbooks/'],
            cwd=Path("."),
            check=False,
            text=True,
            capture_output=False
        )

    def test_list_inventory(self):
        self.mock_subprocess.return_value.returncode = 0
        self.mock_subprocess.return_value.stdout = '{"all": ...}'

        output = self.manager.list_inventory(inventory="hosts")

        self.mock_subprocess.assert_called_with(
            ['/usr/bin/ansible-inventory', '--list', '-i', 'hosts'],
            cwd=Path("."),
            check=False,
            text=True,
            capture_output=True
        )
        self.assertEqual(output, '{"all": ...}')

    def test_show_doc(self):
        self.manager.show_doc("copy")
        self.mock_subprocess.assert_called_with(
            ['/usr/bin/ansible-doc', 'copy'],
            cwd=Path("."),
            check=False,
            text=True,
            capture_output=False
        )

    def test_init_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            manager = AnsibleManager(working_dir=tmp_path)

            manager.init_structure("myproject")

            project_dir = tmp_path / "myproject"
            self.assertTrue(project_dir.exists())
            self.assertTrue((project_dir / "inventory").is_dir())
            self.assertTrue((project_dir / "roles").is_dir())
            self.assertTrue((project_dir / "playbooks").is_dir())
            self.assertTrue((project_dir / "ansible.cfg").is_file())
            self.assertTrue((project_dir / "inventory/hosts").is_file())
            self.assertTrue((project_dir / "playbooks/site.yml").is_file())

    @patch('shared.ansible_lab.AnsibleManager')
    def test_run_ansible_lab_logic(self, mock_manager_cls):
        # Mock the manager instance
        mock_manager = mock_manager_cls.return_value
        mock_manager.run_playbook.return_value = True

        # Mock args
        args = argparse.Namespace(
            project_dir=".",
            action="playbook",
            playbook="site.yml",
            inventory="hosts",
            check=True,
            diff=False,
            limit=None,
            extra_vars=None
        )

        with self.assertRaises(SystemExit) as cm:
            run_ansible_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)

        mock_manager.run_playbook.assert_called_with(
            playbook="site.yml",
            inventory="hosts",
            check_mode=True,
            diff_mode=False,
            limit=None,
            extra_vars=None
        )

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch
import argparse
from shared.helm_lab import HelmLabManager, run_helm_lab_logic


class TestHelmLab(unittest.TestCase):

    def setUp(self):
        self.mock_shutil_which = patch('shutil.which').start()
        self.mock_subprocess_run = patch('subprocess.run').start()

        # Default behavior: helm is installed
        self.mock_shutil_which.return_value = "/usr/bin/helm"

        # Default behavior: subprocess run returns success
        self.mock_process = MagicMock()
        self.mock_process.returncode = 0
        self.mock_subprocess_run.return_value = self.mock_process

    def tearDown(self):
        patch.stopall()

    def test_check_install_success(self):
        manager = HelmLabManager()
        self.assertTrue(manager.check_install())

    def test_check_install_failure(self):
        self.mock_shutil_which.return_value = None
        manager = HelmLabManager()
        self.assertFalse(manager.check_install())

    def test_list_releases(self):
        manager = HelmLabManager()
        manager.list_releases()
        self.mock_subprocess_run.assert_called_with(
            ['/usr/bin/helm', 'list'],
            cwd=manager.working_dir,
            check=False,
            text=True,
            capture_output=False
        )

    def test_list_releases_all(self):
        manager = HelmLabManager()
        manager.list_releases(all_namespaces=True)
        self.mock_subprocess_run.assert_called_with(
            ['/usr/bin/helm', 'list', '--all-namespaces'],
            cwd=manager.working_dir,
            check=False,
            text=True,
            capture_output=False
        )

    def test_install_chart(self):
        manager = HelmLabManager()
        manager.install_chart(release_name="my-release", chart="my-chart")
        self.mock_subprocess_run.assert_called_with(
            ['/usr/bin/helm', 'install', 'my-release', 'my-chart'],
            cwd=manager.working_dir,
            check=False,
            text=True,
            capture_output=False
        )

    def test_install_chart_with_options(self):
        manager = HelmLabManager()
        manager.install_chart(
            release_name="my-release",
            chart="my-chart",
            namespace="my-ns",
            values="vals.yaml",
            sets=["key=val", "foo=bar"]
        )
        self.mock_subprocess_run.assert_called_with(
            ['/usr/bin/helm', 'install', 'my-release', 'my-chart', '--namespace', 'my-ns', '--values', 'vals.yaml', '--set', 'key=val', '--set', 'foo=bar'],
            cwd=manager.working_dir,
            check=False,
            text=True,
            capture_output=False
        )

    def test_cli_list(self):
        args = argparse.Namespace(
            action="list",
            all=True,
            namespace=None,
            project_dir=MagicMock()
        )
        args.project_dir.resolve.return_value = "."

        with self.assertRaises(SystemExit) as cm:
            run_helm_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)

        self.mock_subprocess_run.assert_called_with(
            ['/usr/bin/helm', 'list', '--all-namespaces'],
            cwd=".",
            check=False,
            text=True,
            capture_output=False
        )


if __name__ == '__main__':
    unittest.main()

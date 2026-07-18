import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from shared.ssh_lab import SshLabManager


class TestSshLabManager(unittest.TestCase):
    def setUp(self):
        self.ssh_dir = Path("/tmp/mock_ssh")
        self.manager = SshLabManager(ssh_dir=self.ssh_dir)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.mkdir")
    def test_ensure_ssh_dir(self, mock_mkdir, mock_exists):
        mock_exists.return_value = False
        self.manager.ensure_ssh_dir()
        mock_mkdir.assert_called_once_with(mode=0o700, parents=True)

    @patch("pathlib.Path.iterdir")
    @patch("pathlib.Path.exists")
    def test_list_keys(self, mock_exists, mock_iterdir):
        mock_exists.return_value = True

        # Mock file items
        key1 = MagicMock(spec=Path)
        key1.is_file.return_value = True
        key1.name = "id_rsa"
        key1.with_suffix.return_value.exists.return_value = True
        key1.__str__.return_value = "/tmp/mock_ssh/id_rsa"  # type: ignore

        key2 = MagicMock(spec=Path)
        key2.is_file.return_value = True
        key2.name = "id_ed25519"
        key2.with_suffix.return_value.exists.return_value = False
        key2.__str__.return_value = "/tmp/mock_ssh/id_ed25519"  # type: ignore

        config_file = MagicMock(spec=Path)
        config_file.is_file.return_value = True
        config_file.name = "config"

        mock_iterdir.return_value = [key1, key2, config_file]

        keys = self.manager.list_keys()

        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0]['name'], "id_rsa")
        self.assertTrue(keys[0]['has_pub'])
        self.assertEqual(keys[1]['name'], "id_ed25519")
        self.assertFalse(keys[1]['has_pub'])

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_generate_key_success(self, mock_exists, mock_run):
        # exists() called twice: ensure_ssh_dir and check key existence
        # First call (ssh_dir check) -> True (mocked for simplicity)
        # Second call (key file check) -> False (so we can generate)
        mock_exists.side_effect = [True, False]

        mock_run.return_value.returncode = 0

        result = self.manager.generate_key("ed25519", 4096, "test@example.com", "id_test")

        self.assertTrue(result["success"])
        self.assertIn("path", result)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn("ssh-keygen", args)
        self.assertIn("id_test", args[8])

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_get_fingerprint_success(self, mock_exists, mock_run):
        mock_exists.return_value = True
        mock_run.return_value.stdout = "256 SHA256:abc... comment (ED25519)"

        result = self.manager.get_fingerprint("id_rsa")

        self.assertTrue(result["success"])
        self.assertEqual(result["fingerprint"], "256 SHA256:abc... comment (ED25519)")

    @patch("pathlib.Path.exists")
    def test_list_hosts(self, mock_exists):
        mock_exists.return_value = True

        config_content = """
Host myserver
    HostName 192.168.1.1
    User admin

Host github.com
    User git
    IdentityFile ~/.ssh/id_github
"""
        with patch("builtins.open", mock_open(read_data=config_content)):
            hosts = self.manager.list_hosts()

        self.assertEqual(len(hosts), 2)
        self.assertEqual(hosts[0]['Host'], "myserver")
        self.assertEqual(hosts[0]['HostName'], "192.168.1.1")
        self.assertEqual(hosts[1]['Host'], "github.com")
        self.assertEqual(hosts[1]['IdentityFile'], "~/.ssh/id_github")

    @patch("pathlib.Path.exists")
    def test_add_host(self, mock_exists):
        mock_exists.return_value = True  # for ensure_ssh_dir

        m_open = mock_open()
        with patch("builtins.open", m_open):
            self.manager.add_host("newhost", "10.0.0.1", "root", "~/.ssh/id_new")

        handle = m_open()
        handle.write.assert_called()
        written = handle.write.call_args[0][0]
        self.assertIn("Host newhost", written)
        self.assertIn("HostName 10.0.0.1", written)
        self.assertIn("User root", written)
        self.assertIn("IdentityFile", written)

    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_read_public_key(self, mock_exists, mock_read_text):
        # Case 1: Standard key
        mock_exists.return_value = True
        mock_read_text.return_value = "ssh-rsa AAAA..."

        content = self.manager.read_public_key("id_rsa")
        self.assertEqual(content, "ssh-rsa AAAA...")

        # Case 2: .pub missing
        mock_exists.return_value = False
        content = self.manager.read_public_key("id_missing")
        self.assertIsNone(content)

    @patch("main.run_tui")
    def test_run_ssh_lab_tui(self, mock_run_tui):
        import argparse
        import sys
        from main import run_ssh_lab

        # Test args.action == "tui"
        args = argparse.Namespace(action="tui", tui=False)
        try:
            run_ssh_lab(args)
        except SystemExit:
            pass
        mock_run_tui.assert_called_once_with(args, start_tab="tab-ssh")
        mock_run_tui.reset_mock()

        # Test args.tui == True
        args = argparse.Namespace(action="list", tui=True)
        try:
            run_ssh_lab(args)
        except SystemExit:
            pass
        mock_run_tui.assert_called_once_with(args, start_tab="tab-ssh")

    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.exists")
    def test_delete_key(self, mock_exists, mock_unlink):
        # Case 1: Both exist
        mock_exists.return_value = True
        result = self.manager.delete_key("id_rsa")
        self.assertTrue(result)
        self.assertEqual(mock_unlink.call_count, 2)  # private + public

        # Case 2: Neither exist (but exists() called multiple times internally)
        # reset mocks
        mock_unlink.reset_mock()
        mock_exists.return_value = False
        result = self.manager.delete_key("id_gone")
        self.assertFalse(result)
        mock_unlink.assert_not_called()


if __name__ == "__main__":
    unittest.main()

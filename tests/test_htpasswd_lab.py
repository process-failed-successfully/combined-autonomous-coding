import unittest
import argparse
from unittest.mock import patch, MagicMock
from shared.htpasswd_lab import HtpasswdManager, run_htpasswd_lab_logic
import pytest

pytest.importorskip("textual")
from shared.tui_htpasswd import HtpasswdLabTab


class TestHtpasswdLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = HtpasswdManager()

    def test_generate_bcrypt(self):
        res = self.manager.generate("testuser", "testpass", "bcrypt")
        if res["success"]:
            self.assertTrue(res["entry"].startswith("testuser:"))
            self.assertEqual(res["algorithm"], "bcrypt")
        else:
            self.assertIn("bcrypt library not installed", res["error"])

    def test_generate_md5(self):
        res = self.manager.generate("testuser", "testpass", "md5")
        self.assertTrue(res["success"])
        self.assertTrue(res["entry"].startswith("testuser:$1$"))
        self.assertEqual(res["algorithm"], "md5-crypt")

    def test_generate_sha1(self):
        res = self.manager.generate("testuser", "testpass", "sha1")
        self.assertTrue(res["success"])
        self.assertTrue(res["entry"].startswith("testuser:{SHA}"))
        self.assertEqual(res["algorithm"], "sha1")

    def test_generate_crypt(self):
        res = self.manager.generate("testuser", "testpass", "crypt")
        self.assertTrue(res["success"])
        self.assertTrue(res["entry"].startswith("testuser:"))
        self.assertEqual(res["algorithm"], "crypt")

    def test_generate_plain(self):
        res = self.manager.generate("testuser", "testpass", "plain")
        self.assertTrue(res["success"])
        self.assertEqual(res["entry"], "testuser:testpass")
        self.assertEqual(res["algorithm"], "plain")

    def test_generate_invalid_algorithm(self):
        res = self.manager.generate("testuser", "testpass", "invalid")
        self.assertFalse(res["success"])
        self.assertIn("Unknown algorithm", res["error"])


class TestHtpasswdLabCLI(unittest.TestCase):
    @patch('sys.stdout')
    def test_cli_success(self, mock_stdout):
        args = argparse.Namespace(username="user", password="password", algorithm="plain")
        self.assertTrue(run_htpasswd_lab_logic(args))

    @patch('sys.stderr')
    def test_cli_missing_args(self, mock_stderr):
        args = argparse.Namespace(username=None, password=None, algorithm="plain")
        self.assertFalse(run_htpasswd_lab_logic(args))


from textual.app import App

class DummyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notifications = []

    def notify(self, message, *, title="", severity="information", timeout=None, markup=True):
        self.notifications.append((message, severity))


class TestHtpasswdLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_tui_generation(self):
        app = DummyApp()
        tab = HtpasswdLabTab()

        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = app

        try:
            async with app.run_test() as pilot:
                await pilot.app.mount(tab)
                await pilot.pause()

                # Find input fields
                user_input = pilot.app.query_one("#htpasswd-username")
                pass_input = pilot.app.query_one("#htpasswd-password")
                alg_select = pilot.app.query_one("#htpasswd-algorithm")

                # Empty inputs
                await pilot.click("#btn-htpasswd-generate")
                await pilot.pause()

                # Fill inputs
                user_input.value = "admin"
                pass_input.value = "secret123"
                alg_select.value = "plain"

                await pilot.click("#btn-htpasswd-generate")
                await pilot.pause()

                log = pilot.app.query_one("#htpasswd-output-log")
                # Wait for reactively updated text
                self.assertIsNotNone(log)

                # Test copy
                with patch("pyperclip.copy") as mock_copy:
                    await pilot.click("#btn-htpasswd-copy")
                    await pilot.pause()
                    mock_copy.assert_called_once()
        finally:
            if hasattr(type(tab), 'app'):
                del type(tab).app

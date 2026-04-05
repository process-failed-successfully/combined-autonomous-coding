import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
import argparse
from shared.hash_validator_lab import HashValidatorManager, run_hash_validator_lab_logic


class TestHashValidatorManager(unittest.TestCase):
    def setUp(self):
        self.manager = HashValidatorManager()

    def test_detect_hash_type_md5(self):
        md5_hash = "098f6bcd4621d373cade4e832627b4f6"  # test
        algos = self.manager.detect_hash_type(md5_hash)
        self.assertIn("md5", algos)

    def test_detect_hash_type_sha256(self):
        sha256_hash = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"  # test
        algos = self.manager.detect_hash_type(sha256_hash)
        self.assertIn("sha256", algos)

    def test_detect_hash_type_invalid(self):
        algos = self.manager.detect_hash_type("not-a-valid-hex-string")
        self.assertEqual(algos, [])

    def test_verify_hash_success(self):
        sha256_hash = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        result = self.manager.verify_hash("test", sha256_hash)
        self.assertTrue(result["success"])
        self.assertTrue(result["match"])
        self.assertEqual(result["algorithm"], "sha256")

    def test_verify_hash_failure(self):
        sha256_hash = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        result = self.manager.verify_hash("wrong-input", sha256_hash)
        self.assertTrue(result["success"])
        self.assertFalse(result["match"])
        self.assertIn("sha256", result["tried_algorithms"])

    def test_verify_hash_unsupported_algo(self):
        result = self.manager.verify_hash("test", "098f6bcd4621d373cade4e832627b4f6", algorithm="not-real-algo")
        self.assertTrue(result["success"])
        self.assertFalse(result["match"])
        self.assertIn("not-real-algo", result["tried_algorithms"])

    def test_verify_hash_no_algos(self):
        result = self.manager.verify_hash("test", "too-short")
        self.assertFalse(result["success"])
        self.assertFalse(result["match"])
        self.assertIn("none was provided", result["error"])


class TestHashValidatorLabCLI(unittest.TestCase):
    @patch('sys.exit')
    @patch('builtins.print')
    def test_detect_cli_success(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="detect",
            hash="098f6bcd4621d373cade4e832627b4f6"
        )
        run_hash_validator_lab_logic(args)

        mock_print.assert_any_call("  - md5")
        mock_exit.assert_called_with(0)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_detect_cli_missing_hash(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="detect",
            hash=None
        )
        run_hash_validator_lab_logic(args)
        mock_exit.assert_called_with(1)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_detect_cli_no_algos(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="detect",
            hash="123"
        )
        run_hash_validator_lab_logic(args)
        mock_exit.assert_called_with(1)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_verify_cli_success_text(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="verify",
            hash="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            text="test",
            file=None,
            algorithm=None
        )
        run_hash_validator_lab_logic(args)

        mock_print.assert_any_call("✅ Match found! Algorithm: sha256")
        mock_exit.assert_called_with(0)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_verify_cli_failure(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="verify",
            hash="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            text="wrong",
            file=None,
            algorithm=None
        )
        run_hash_validator_lab_logic(args)
        mock_print.assert_any_call("❌ No match found.")
        mock_exit.assert_called_with(1)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_verify_cli_missing_hash(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="verify",
            hash=None,
            text="test",
            file=None,
            algorithm=None
        )
        run_hash_validator_lab_logic(args)
        mock_exit.assert_called_with(1)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_verify_cli_file_success(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="verify",
            hash="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            text=None,
            file="dummy.txt",
            algorithm=None
        )
        with patch('builtins.open', mock_open(read_data="test")):
            run_hash_validator_lab_logic(args)
            mock_print.assert_any_call("✅ Match found! Algorithm: sha256")
            mock_exit.assert_called_with(0)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_verify_cli_file_error(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="verify",
            hash="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            text=None,
            file="dummy.txt",
            algorithm=None
        )
        with patch('builtins.open', side_effect=IOError("Test Error")):
            run_hash_validator_lab_logic(args)
            mock_exit.assert_called_with(1)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_verify_cli_stdin_error(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="verify",
            hash="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            text=None,
            file=None,
            algorithm=None
        )
        with patch('sys.stdin.isatty', return_value=True):
            run_hash_validator_lab_logic(args)
            mock_exit.assert_called_with(1)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_verify_cli_stdin_success(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="verify",
            hash="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            text=None,
            file=None,
            algorithm=None
        )
        with patch('sys.stdin.isatty', return_value=False):
            with patch('sys.stdin.read', return_value="test"):
                run_hash_validator_lab_logic(args)
                mock_print.assert_any_call("✅ Match found! Algorithm: sha256")
                mock_exit.assert_called_with(0)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_unknown_action(self, mock_print, mock_exit):
        args = argparse.Namespace(
            action="invalid"
        )
        run_hash_validator_lab_logic(args)
        mock_exit.assert_called_with(1)

    @patch('sys.exit')
    def test_tui_launch(self, mock_exit):
        import pytest
        pytest.importorskip("textual")
        import shared.tui
        with patch('shared.tui.AgentTUI.run') as mock_tui_run:
            args = argparse.Namespace(action="tui", project_dir=Path("."))
            run_hash_validator_lab_logic(args)

            mock_tui_run.assert_called_once()
            mock_exit.assert_called_with(0)


class TestHashValidatorLabTUI(unittest.IsolatedAsyncioTestCase):
    async def test_tui_instantiation_and_actions(self):
        from textual.app import App
        from typing import Any
        from shared.tui_hash_validator import HashValidatorLabTab
        from textual.widgets import Input, TextArea, RichLog

        class DummyApp(App[Any]):
            def compose(self):
                yield HashValidatorLabTab()

        app = DummyApp()
        async with app.run_test(size=(80, 24)) as pilot:
            tab = app.query_one(HashValidatorLabTab)
            self.assertIsNotNone(tab)

            log = app.query_one("#hash-validator-log", RichLog)

            # Test empty detect
            app.query_one("#btn-hash-detect").press()
            await pilot.pause()
            self.assertIn("No hash provided", str(list(log.lines)))

            # Test valid detect
            app.query_one("#hash-expected-input", Input).value = "098f6bcd4621d373cade4e832627b4f6"
            app.query_one("#btn-hash-detect").press()
            await pilot.pause()
            self.assertIn("md5", str(list(log.lines)))

            # Test invalid detect length
            app.query_one("#hash-expected-input", Input).value = "123"
            app.query_one("#btn-hash-detect").press()
            await pilot.pause()
            self.assertIn("Could not detect any standard hash algorithm", str(list(log.lines)))

            # Test verify without text
            app.query_one("#hash-expected-input", Input).value = "098f6bcd4621d373cade4e832627b4f6"
            app.query_one("#hash-text-input", TextArea).load_text("")
            app.query_one("#btn-hash-verify").press()
            await pilot.pause()
            self.assertIn("No input text provided", str(list(log.lines)))

            # Test verify success
            app.query_one("#hash-text-input", TextArea).load_text("test")
            app.query_one("#btn-hash-verify").press()
            await pilot.pause()
            self.assertIn("Match found!", str(list(log.lines)))

            # Test verify failure
            app.query_one("#hash-text-input", TextArea).load_text("wrong")
            app.query_one("#btn-hash-verify").press()
            await pilot.pause()
            self.assertIn("No match found.", str(list(log.lines)))

            # Test verify no hash
            app.query_one("#hash-expected-input", Input).value = ""
            app.query_one("#btn-hash-verify").press()
            await pilot.pause()
            self.assertIn("No expected hash provided", str(list(log.lines)))

            # Test verify empty detection
            app.query_one("#hash-expected-input", Input).value = "123"
            app.query_one("#hash-text-input", TextArea).load_text("test")
            app.query_one("#btn-hash-verify").press()
            await pilot.pause()
            self.assertIn("Could not detect hash algorithm", str(list(log.lines)))

            # Test verify unsupported algo
            app.query_one("#hash-expected-input", Input).value = "098f6bcd4621d373cade4e832627b4f6"
            app.query_one("#hash-text-input", TextArea).load_text("test")
            app.query_one("#hash-algo-input", Input).value = "unsupported-algo"
            app.query_one("#btn-hash-verify").press()
            await pilot.pause()
            self.assertIn("No match found.", str(list(log.lines)))

            # Test clear
            app.query_one("#btn-hash-clear").press()
            await pilot.pause()
            self.assertEqual(app.query_one("#hash-expected-input", Input).value, "")
            self.assertEqual(app.query_one("#hash-text-input", TextArea).text, "")
            self.assertEqual(app.query_one("#hash-algo-input", Input).value, "")


if __name__ == '__main__':
    pass

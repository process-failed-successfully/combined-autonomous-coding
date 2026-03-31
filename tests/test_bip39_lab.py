import io
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from textual.app import App, ComposeResult
from typing import Any

from shared.bip39_lab import Bip39LabManager, run_bip39_lab_logic, HAS_MNEMONIC
from shared.tui_bip39 import Bip39LabTab


class DummyApp(App[Any]):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield Bip39LabTab(self.project_dir)


class TestBip39Lab(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        if not HAS_MNEMONIC:
            self.skipTest("mnemonic library not installed")

    def test_bip39_generate(self):
        manager = Bip39LabManager()

        # Test 12 words (128 bits)
        phrase12 = manager.generate(strength=128)
        self.assertEqual(len(phrase12.split()), 12)
        self.assertTrue(manager.validate(phrase12))

        # Test 24 words (256 bits)
        phrase24 = manager.generate(strength=256)
        self.assertEqual(len(phrase24.split()), 24)
        self.assertTrue(manager.validate(phrase24))

        # Test invalid strength
        with self.assertRaises(ValueError):
            manager.generate(strength=100)

    def test_bip39_validate(self):
        manager = Bip39LabManager()
        # Valid phrase
        valid_phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        self.assertTrue(manager.validate(valid_phrase))

        # Invalid phrase (wrong checksum or words)
        invalid_phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"
        self.assertFalse(manager.validate(invalid_phrase))

        invalid_phrase2 = "not a real phrase here buddy"
        self.assertFalse(manager.validate(invalid_phrase2))

    def test_bip39_seed(self):
        manager = Bip39LabManager()
        # Test vector from BIP39 spec
        phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        passphrase = "TREZOR"
        seed = manager.generate_seed(phrase, passphrase)
        seed_hex = seed.hex()
        # Expected from BIP39 test vectors
        self.assertEqual(seed_hex, "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04")

        # Without passphrase
        seed_no_pass = manager.generate_seed(phrase)
        self.assertNotEqual(seed_no_pass.hex(), seed_hex)

        # Invalid phrase
        with self.assertRaises(ValueError):
            manager.generate_seed("invalid phrase")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_bip39_cli_generate(self, mock_stdout):
        args = MagicMock()
        args.action = "generate"
        args.strength = 128
        args.language = "english"

        success = run_bip39_lab_logic(args)
        self.assertTrue(success)
        output = mock_stdout.getvalue().strip()
        self.assertEqual(len(output.split()), 12)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_bip39_cli_validate(self, mock_stdout):
        args = MagicMock()
        args.action = "validate"
        args.phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        args.language = "english"

        success = run_bip39_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("Valid", mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_bip39_cli_validate_invalid(self, mock_stderr):
        args = MagicMock()
        args.action = "validate"
        args.phrase = "invalid phrase"
        args.language = "english"

        success = run_bip39_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Invalid", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_bip39_cli_seed(self, mock_stdout):
        args = MagicMock()
        args.action = "seed"
        args.phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        args.passphrase = "TREZOR"
        args.language = "english"

        success = run_bip39_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_bip39_cli_seed_invalid(self, mock_stderr):
        args = MagicMock()
        args.action = "seed"
        args.phrase = "invalid phrase"
        args.passphrase = ""
        args.language = "english"

        success = run_bip39_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error:", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_bip39_cli_unknown_action(self, mock_stderr):
        args = MagicMock()
        args.action = "unknown"
        args.language = "english"
        success = run_bip39_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Unknown action", mock_stderr.getvalue())

    async def test_bip39_tui(self):
        project_dir = Path("/tmp")
        app = DummyApp(project_dir)
        async with app.run_test(size=(200, 200)) as pilot:
            # Empty validation
            await pilot.click("#btn-bip39-validate")
            log_widget = app.query_one("#bip39-log")
            log_text = str(list(log_widget.lines))
            self.assertIn("Phrase is empty", log_text)

            # Empty seed
            await pilot.click("#btn-bip39-seed")
            log_text = str(list(log_widget.lines))
            self.assertIn("Phrase is empty", log_text)

            # Generate phrase
            await pilot.click("#btn-bip39-generate")
            phrase_input = app.query_one("#bip39-phrase")
            self.assertNotEqual(phrase_input.value, "")
            self.assertEqual(len(phrase_input.value.split()), 12)

            # Validate phrase
            await pilot.click("#btn-bip39-validate")
            log_widget = app.query_one("#bip39-log")
            log_text = str(list(log_widget.lines))
            self.assertIn("valid BIP39 mnemonic", log_text)

            # Invalid validation
            phrase_input.value = "invalid"
            await pilot.click("#btn-bip39-validate")
            log_text = str(list(log_widget.lines))
            self.assertIn("invalid", log_text)

            # Seed generation
            phrase_input.value = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
            passphrase_input = app.query_one("#bip39-passphrase")
            passphrase_input.value = "TREZOR"
            await pilot.click("#btn-bip39-seed")
            seed_output = app.query_one("#bip39-seed-output")
            self.assertEqual(seed_output.text, "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04")

            # Invalid seed generation
            phrase_input.value = "invalid"
            await pilot.click("#btn-bip39-seed")
            self.assertEqual(seed_output.text, "")

            # Error coverage in generate
            with patch.object(app.query_one("Bip39LabTab").manager, 'generate', side_effect=Exception("mock err")):
                await pilot.click("#btn-bip39-generate")
                log_text = str(list(log_widget.lines))
                self.assertIn("mock err", log_text)

            # Error coverage in validate
            with patch.object(app.query_one("Bip39LabTab").manager, 'validate', side_effect=Exception("mock err")):
                phrase_input.value = "test"
                await pilot.click("#btn-bip39-validate")
                log_text = str(list(log_widget.lines))
                self.assertIn("mock err", log_text)

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_bip39_cli_empty_phrase_validate(self, mock_stderr):
        args = MagicMock()
        args.action = "validate"
        args.phrase = ""
        args.language = "english"
        success = run_bip39_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Phrase is required", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_bip39_cli_empty_phrase_seed(self, mock_stderr):
        args = MagicMock()
        args.action = "seed"
        args.phrase = ""
        args.language = "english"
        success = run_bip39_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Phrase is required", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_bip39_cli_generate_error(self, mock_stderr):
        args = MagicMock()
        args.action = "generate"
        args.language = "english"
        args.strength = "not_an_int"
        success = run_bip39_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error", mock_stderr.getvalue())

    @patch('shared.bip39_lab.Bip39LabManager.__init__', side_effect=Exception("Mock Init Error"))
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_bip39_cli_init_error(self, mock_stderr, mock_init):
        args = MagicMock()
        args.action = "generate"
        args.language = "english"
        success = run_bip39_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Mock Init Error", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_bip39_cli_tui(self, mock_stdout):
        # We patch __import__ or Textual's App.run to avoid it taking over.
        # But we can just patch AgentTUI in shared.tui
        with patch('shared.tui.AgentTUI') as MockApp:
            mock_instance = MockApp.return_value
            args = MagicMock()
            args.action = "tui"
            args.language = "english"
            args.project_dir = Path("/tmp")
            success = run_bip39_lab_logic(args)
            self.assertTrue(success)
            mock_instance.run.assert_called_once()

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('asyncio.get_running_loop')
    def test_bip39_cli_tui_async(self, mock_get_running_loop, mock_stdout):
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        mock_get_running_loop.return_value = mock_loop

        with patch('shared.tui.AgentTUI') as MockApp:
            mock_instance = MockApp.return_value
            args = MagicMock()
            args.action = "tui"
            args.language = "english"
            args.project_dir = Path("/tmp")
            with patch('asyncio.ensure_future') as mock_ensure:
                success = run_bip39_lab_logic(args)
                self.assertTrue(success)
                mock_ensure.assert_called_once_with(mock_instance.run_async.return_value)

    @patch('shared.bip39_lab.HAS_MNEMONIC', False)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_bip39_cli_no_library(self, mock_stderr):
        args = MagicMock()
        args.action = "generate"
        success = run_bip39_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("not installed", mock_stderr.getvalue())

    @patch('shared.tui_bip39.HAS_MNEMONIC', False)
    async def test_bip39_tui_no_library(self):
        project_dir = Path("/tmp")
        app = DummyApp(project_dir)
        async with app.run_test(size=(200, 200)):
            error_static = app.query_one("#bip39-error")
            self.assertIn("not installed", str(error_static.render()))

    async def test_bip39_tui_no_manager(self):
        project_dir = Path("/tmp")
        app = DummyApp(project_dir)
        async with app.run_test(size=(200, 200)) as pilot:
            app.query_one("Bip39LabTab").manager = None
            await pilot.click("#btn-bip39-generate")
            log_widget = app.query_one("#bip39-log")
            log_text = str(list(log_widget.lines))
            self.assertIn("manager not initialized", log_text)

            # Use pilot to avoid F841 unused variable warning from flake8
            await pilot.click("#btn-bip39-validate")

    def test_manager_no_library(self):
        import shared.bip39_lab as bl
        orig = bl.HAS_MNEMONIC
        try:
            bl.HAS_MNEMONIC = False
            with self.assertRaises(ImportError):
                bl.Bip39LabManager()
        finally:
            bl.HAS_MNEMONIC = orig

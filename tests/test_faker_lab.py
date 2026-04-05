import unittest
import argparse
from unittest.mock import patch
from shared.faker_lab import FakerLabManager, run_faker_lab_logic
import pytest
from textual.app import App

# Need to check if textual is installed to skip TUI tests safely
pytest.importorskip("textual")
from shared.tui_faker import FakerLabTab  # noqa: E402


class DummyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notifications = []

    def notify(self, message, *, title="", severity="information", timeout=None, markup=True):
        self.notifications.append((message, severity))


class TestFakerLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = FakerLabManager()

    def test_init_invalid_locale(self):
        manager = FakerLabManager(locale="invalid_LOCALE_123")
        # Should fallback without error
        self.assertEqual(manager.locale, "invalid_LOCALE_123")
        self.assertIsNotNone(manager.fake)

    def test_generate_person(self):
        res = self.manager.generate_person(count=2)
        self.assertEqual(len(res), 2)
        self.assertIn("name", res[0])
        self.assertIn("address", res[0])

    def test_generate_internet(self):
        res = self.manager.generate_internet(count=1)
        self.assertEqual(len(res), 1)
        self.assertIn("ipv4", res[0])
        self.assertIn("domain_name", res[0])

    def test_generate_text(self):
        res = self.manager.generate_text(count=3)
        self.assertEqual(len(res), 3)
        self.assertIsInstance(res[0], str)

    def test_generate_credit_card(self):
        res = self.manager.generate_credit_card(count=1)
        self.assertEqual(len(res), 1)
        self.assertIn("provider", res[0])
        self.assertIn("number", res[0])


class TestFakerLabCLI(unittest.TestCase):
    @patch('sys.stdout')
    def test_cli_person(self, mock_stdout):
        args = argparse.Namespace(type="person", count=1, locale="en_US")
        self.assertTrue(run_faker_lab_logic(args))

    @patch('sys.stdout')
    def test_cli_internet(self, mock_stdout):
        args = argparse.Namespace(type="internet", count=2, locale="en_US")
        self.assertTrue(run_faker_lab_logic(args))

    @patch('sys.stdout')
    def test_cli_text(self, mock_stdout):
        args = argparse.Namespace(type="text", count=1, locale="en_US")
        self.assertTrue(run_faker_lab_logic(args))

    @patch('sys.stdout')
    def test_cli_credit_card(self, mock_stdout):
        args = argparse.Namespace(type="credit_card", count=1, locale="en_US")
        self.assertTrue(run_faker_lab_logic(args))

    @patch('sys.stderr')
    def test_cli_invalid_type(self, mock_stderr):
        args = argparse.Namespace(type="unknown_type", count=1, locale="en_US")
        self.assertFalse(run_faker_lab_logic(args))

    @patch('sys.stderr')
    @patch.object(FakerLabManager, 'generate_person', side_effect=Exception("Test Error"))
    def test_cli_exception(self, mock_generate, mock_stderr):
        args = argparse.Namespace(type="person", count=1, locale="en_US")
        self.assertFalse(run_faker_lab_logic(args))


class TestFakerLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_tui_initialization(self):
        app = DummyApp()
        tab = FakerLabTab()

        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = app

        try:
            async with app.run_test() as pilot:
                await pilot.app.mount(tab)
                await pilot.pause()

                # Find input fields
                type_select = pilot.app.query_one("#faker-type")
                locale_input = pilot.app.query_one("#faker-locale")
                count_input = pilot.app.query_one("#faker-count")

                # Test Generate Person
                app.query_one("#btn-faker-generate").press()
                await pilot.pause()
                await pilot.pause()
                log = pilot.app.query_one("#faker-output-log")
                self.assertIsNotNone(log)

                # Change type to internet
                type_select.value = "internet"
                app.query_one("#btn-faker-generate").press()
                await pilot.pause()
                await pilot.pause()

                # Change type to text
                type_select.value = "text"
                app.query_one("#btn-faker-generate").press()
                await pilot.pause()
                await pilot.pause()

                # Change type to credit_card
                type_select.value = "credit_card"
                app.query_one("#btn-faker-generate").press()
                await pilot.pause()
                await pilot.pause()

                # Change locale
                locale_input.value = "fr_FR"
                app.query_one("#btn-faker-generate").press()
                await pilot.pause()
                await pilot.pause()

                # Invalid count
                count_input.value = "-5"
                app.query_one("#btn-faker-generate").press()
                await pilot.pause()
                await pilot.pause()

                # Simulate Exception during generation
                with patch.object(tab.manager, 'generate_credit_card', side_effect=Exception("Simulated TUI Error")):
                    type_select.value = "credit_card"
                    count_input.value = "1"
                    app.query_one("#btn-faker-generate").press()
                    await pilot.pause()
                    await pilot.pause()
        finally:
            if hasattr(type(tab), 'app'):
                del type(tab).app

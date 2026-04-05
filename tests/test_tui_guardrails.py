import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from textual.app import App
from shared.tui_guardrails import GuardrailsTab

class GuardrailsTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self):
        yield GuardrailsTab(self.project_dir)

class TestTUIGuardrails(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path("/tmp/test_tui_guardrails")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        # Clean up
        pass

    async def test_mount_and_load(self):
        app = GuardrailsTestApp(self.test_dir)
        async with app.run_test() as pilot:
            tab = app.query_one(GuardrailsTab)
            self.assertIsNotNone(tab)

            # Check if manager is initialized
            self.assertEqual(tab.manager.project_dir, self.test_dir)

    @patch("shared.tui_guardrails.GuardrailsManager")
    async def test_run_checks(self, MockManager):
        # Setup mock
        mock_instance = MockManager.return_value
        mock_instance.policies = [MagicMock(name="TestPolicy")]

        # Mock run to return violations
        from shared.guardrails import Violation
        mock_instance.run.return_value = [Violation("TestPolicy", "Failed", "file.py")]

        app = GuardrailsTestApp(self.test_dir)
        async with app.run_test() as pilot:
            # Click check button
            app.query_one("#btn-gr-check").press()
        await pilot.pause()

            # Verify run was called
            mock_instance.run.assert_called()

            # Verify notification or table update (checking table content is hard in unit test without full integration)
            # But we can check if table row count increased?
            table = app.query_one("#gr-violations-table")
            self.assertGreater(len(table.rows), 0)

if __name__ == "__main__":
    unittest.main()

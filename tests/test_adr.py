import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import shutil
import tempfile
from shared.adr import ADRManager

class TestADRManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = ADRManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init_adr_repo(self):
        msg = self.manager.init_adr_repo()
        self.assertTrue((self.test_dir / "docs/adr").exists())
        self.assertTrue((self.test_dir / "docs/adr/0000-record-architecture-decisions.md").exists())
        self.assertIn("Initialized ADR repository", msg)

        # Test idempotency
        msg = self.manager.init_adr_repo()
        self.assertIn("already initialized", msg)

    def test_create_adr(self):
        self.manager.init_adr_repo()
        path = self.manager.create_adr("Use Python", status="Accepted")
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "0001-use-python.md")
        content = path.read_text(encoding="utf-8")
        self.assertIn("# 1. Use Python", content)
        self.assertIn("Accepted", content)

    def test_create_adr_numbering(self):
        self.manager.init_adr_repo()
        self.manager.create_adr("First")
        path = self.manager.create_adr("Second")
        self.assertEqual(path.name, "0002-second.md")

    def test_list_adrs(self):
        self.manager.init_adr_repo()
        self.manager.create_adr("My Feature")
        adrs = self.manager.list_adrs()
        self.assertEqual(len(adrs), 2) # 0000 and 0001
        self.assertEqual(adrs[1]["title"], "1. My Feature")
        self.assertEqual(adrs[1]["status"], "Proposed")

    def test_update_status(self):
        self.manager.init_adr_repo()
        self.manager.create_adr("To Change")

        # Update by ID
        success = self.manager.update_status("1", "Rejected")
        self.assertTrue(success)

        adrs = self.manager.list_adrs()
        self.assertEqual(adrs[1]["status"], "Rejected")

        # Verify content
        path = self.test_dir / "docs/adr/0001-to-change.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("Rejected", content)

    @patch("shared.adr.GeminiAgent")
    async def test_generate_adr_content(self, mock_agent_class):
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.run_agent_session.return_value = (True, "# Generated ADR\n\nDate: 2023-01-01\n\n## Status\nProposed", [])

        content = await self.manager.generate_adr_content("AI Feature", "Context here")
        self.assertIn("Generated ADR", content)

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Button, DataTable, Input, RichLog, Select
from shared.tui_research import ResearchTab

class ResearchTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield ResearchTab(self.project_dir)

class TestResearchTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = ResearchTestApp(self.project_dir)

    @patch("shared.tui_research.ResearchManager")
    async def test_start_research(self, MockManager):
        mock_instance = MockManager.return_value
        # Mock crawl to return results
        mock_instance.crawl.return_value = [
            {"url": "https://example.com", "content": "Example Content"}
        ]

        async with self.app.run_test(size=(200, 100)) as pilot:
            tab = self.app.query_one(ResearchTab)

            # Set Inputs
            url_input = tab.query_one("#research-url", Input)
            url_input.value = "https://example.com"

            # Click Start
            btn = tab.query_one("#btn-research-start", Button)
            btn.press()
            await pilot.pause(0.5) # Wait for thread

            # Verify crawl called
            mock_instance.crawl.assert_called()

            # Verify table populated
            table = tab.query_one("#research-table", DataTable)
            # We don't easily check rows content without key knowledge, but we can check row count
            # Wait, update_table is called via call_from_thread which puts it on main loop.
            await pilot.pause(0.1)
            # Check crawled_data
            self.assertEqual(len(tab.crawled_data), 1)
            self.assertEqual(tab.crawled_data[0]["url"], "https://example.com")

    @patch("shared.tui_research.ResearchManager")
    @patch("shared.tui_research.GeminiAgent")
    async def test_summarize(self, MockAgent, MockManager):
        # Setup Data
        async with self.app.run_test(size=(200, 100)) as pilot:
            tab = self.app.query_one(ResearchTab)
            tab.crawled_data = [{"url": "https://example.com", "content": "Content to summarize"}]

            # Simulate selection
            table = tab.query_one("#research-table", DataTable)
            table.add_row("Success", "https://example.com", key="https://example.com")

            # Click row (simulate event)
            # pilot.click on table row is hard. We can call the handler directly or use keyboard navigation
            # Let's call the handler directly for stability
            class MockEvent:
                class RowKey:
                    value = "https://example.com"
                row_key = RowKey()

            tab.on_url_selected(MockEvent())

            # Check if summarize button enabled
            self.assertFalse(tab.query_one("#btn-research-summarize").disabled)

            # Mock Agent response
            mock_agent_instance = MockAgent.return_value
            mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, "This is a summary.", []))

            # Click Summarize
            btn = tab.query_one("#btn-research-summarize", Button)
            btn.press()
            await pilot.pause(0.2)

            # Verify agent called
            mock_agent_instance.run_agent_session.assert_called()
            self.assertEqual(tab.current_summary, "This is a summary.")

            # Check Save button enabled
            self.assertFalse(tab.query_one("#btn-research-save").disabled)

    @patch("shared.tui_research.KnowledgeManager")
    async def test_save_summary(self, MockKB):
        mock_kb = MockKB.return_value

        async with self.app.run_test(size=(200, 100)) as pilot:
            tab = self.app.query_one(ResearchTab)
            tab.selected_url = "https://example.com"
            tab.current_summary = "My Summary"

            # Enable save button manually to simulate state
            tab.query_one("#btn-research-save").disabled = False

            btn = tab.query_one("#btn-research-save", Button)
            btn.press()
            await pilot.pause(0.1)

            mock_kb.add_knowledge.assert_called_with(
                content="Summary of https://example.com:\n\nMy Summary",
                category="RESEARCH_SUMMARY",
                source="tui_research"
            )

if __name__ == "__main__":
    unittest.main()

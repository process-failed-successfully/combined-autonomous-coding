import unittest
import shutil
import tempfile
import asyncio
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.widgets import ListView, Static, Select
from shared.tui import AgentTUI
from shared.tui_pattern import PatternLabTab
from textual.widgets import Static

class TestTUIPattern(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

        # Start patches manually to keep references
        self.patchers = []

        # Helper to start patch
        def start_patch(target, **kwargs):
            p = patch(target, **kwargs)
            m = p.start()
            self.patchers.append(p)
            return m

        start_patch('shared.tui.get_all_log_files', return_value=[])
        start_patch('shared.tui.get_git_info', return_value={"branch": "main", "status": "Clean"})
        start_patch('shared.tui.get_workflow_stage', return_value="Dev")
        start_patch('shared.tui.init_db')

        # Patch other managers
        start_patch('shared.tui.WorkSessionManager')
        start_patch('shared.tui.TimelineCollector')
        start_patch('shared.tui.TimelineRenderer')
        start_patch('shared.tui.RecipeManager')
        start_patch('shared.tui.WorktreeManager')
        start_patch('shared.tui.DependencyAnalyzer')
        start_patch('shared.tui.DependencyUpdater')
        start_patch('shared.tui.TaskManager')
        start_patch('shared.tui.KnowledgeManager')
        start_patch('shared.tui.ApiLabManager')
        start_patch('shared.tui.PlaygroundManager')
        start_patch('shared.tui.SecretsManager')
        start_patch('shared.tui.TroubleshootManager')
        start_patch('shared.tui.RecipeLearner')
        start_patch('shared.tui.DebtCollector')
        start_patch('shared.tui.SecurityAuditor')
        start_patch('shared.tui.OptimizationManager')
        start_patch('shared.tui.DocstringManager')
        start_patch('shared.tui.LinkChecker')
        start_patch('shared.tui.OpenAPIGenerator')
        start_patch('shared.tui_knowledge_graph.KnowledgeManager')
        start_patch('shared.tui.ProcessExplorerTab', side_effect=lambda *args, **kwargs: Static("Mock ProcessExplorer Tab", id="tab-process-explorer"))

        # Capture the specific mock we need
        self.mock_pattern_cls = start_patch('shared.tui_pattern.PatternLabManager')
        self.mock_pattern_mgr = self.mock_pattern_cls.return_value

        # Setup specific PatternLabManager mock behavior
        self.mock_pattern_mgr.list_patterns.return_value = ["Singleton", "Factory"]
        self.mock_pattern_mgr.list_languages.return_value = ["python", "javascript"]
        self.mock_pattern_mgr.get_template.return_value = "class Singleton: pass"

    async def asyncTearDown(self):
        for p in reversed(self.patchers):
            p.stop()
        shutil.rmtree(self.test_dir)

    async def test_pattern_tab_rendering(self):
        app = AgentTUI(project_dir=self.test_dir)

        async with app.run_test(size=(120, 40)) as pilot:
            tabs = app.query_one("#main-tabs")
            tabs.active = "tab-pattern-lab"
            await pilot.pause()

            tab = app.query_one(PatternLabTab)
            self.assertIsNotNone(tab)

            # Check widgets
            list_view = tab.query_one("#pattern-list", ListView)
            self.assertEqual(len(list_view.children), 2) # Singleton, Factory

            select = tab.query_one("#pattern-lang-select", Select)
            self.assertEqual(select.value, "python")

    async def test_pattern_selection(self):
        app = AgentTUI(project_dir=self.test_dir)

        async with app.run_test(size=(120, 40)) as pilot:
            tabs = app.query_one("#main-tabs")
            tabs.active = "tab-pattern-lab"
            await pilot.pause()

            tab = app.query_one(PatternLabTab)
            list_view = tab.query_one("#pattern-list", ListView)

            # Ensure focus
            list_view.focus()

            # Select "Singleton" (first item)
            list_view.index = 0

            # Trigger selection event manually by simulating enter press
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Verify preview update
            self.mock_pattern_mgr.get_template.assert_called_with("Singleton", "python")

    async def test_language_change(self):
        app = AgentTUI(project_dir=self.test_dir)

        async with app.run_test(size=(120, 40)) as pilot:
            tabs = app.query_one("#main-tabs")
            tabs.active = "tab-pattern-lab"
            await pilot.pause()

            tab = app.query_one(PatternLabTab)

            # Select pattern first (to ensure preview update triggers something)
            list_view = tab.query_one("#pattern-list", ListView)
            list_view.focus()
            list_view.index = 0
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Change language
            select = tab.query_one("#pattern-lang-select", Select)

            # Use event to change value safely
            select.value = "javascript"
            await pilot.pause(0.5)

            # Verify preview update with new lang
            self.mock_pattern_mgr.get_template.assert_called_with("Singleton", "javascript")

if __name__ == "__main__":
    unittest.main()

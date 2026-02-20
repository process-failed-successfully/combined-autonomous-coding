import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import DataTable, Input, Select, Button, Label
from textual.containers import Container
from shared.tui import AgentTUI, TasksTab
from shared.task_manager import Task

class MockServicesTab(Container):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def compose(self):
        yield Label("Mock Services")

class TestTUITasks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock dependencies
        self.patcher_db = patch("shared.tui.init_db")
        self.mock_init_db = self.patcher_db.start()

        self.patcher_km = patch("shared.tui.KnowledgeManager")
        self.mock_km = self.patcher_km.start()

        self.patcher_ask = patch("shared.tui.run_ask_logic", new_callable=AsyncMock)
        self.mock_ask = self.patcher_ask.start()

        self.patcher_tm = patch("shared.tui.TaskManager")
        self.mock_tm_class = self.patcher_tm.start()
        self.mock_tm = self.mock_tm_class.return_value

        # Mock heavy tabs to avoid side effects and speed up tests
        side_effect = lambda *args, **kwargs: Container()
        self.patcher_tabs = patch.multiple("shared.tui",
            ProcLabTab=MagicMock(side_effect=side_effect),
            LogTailTab=MagicMock(side_effect=side_effect),
            AnalyticsTab=MagicMock(side_effect=side_effect),
            HealthTab=MagicMock(side_effect=side_effect),
            TroubleshootTab=MagicMock(side_effect=side_effect),
            DocumentationTab=MagicMock(side_effect=side_effect),
            ConfigTab=MagicMock(side_effect=side_effect),
            CostTab=MagicMock(side_effect=side_effect),
            PromptLabTab=MagicMock(side_effect=side_effect),
            RefactorTab=MagicMock(side_effect=side_effect),
            SecretsTab=MagicMock(side_effect=side_effect),
            SessionTab=MagicMock(side_effect=side_effect),
            RecipesTab=MagicMock(side_effect=side_effect),
            WorktreesTab=MagicMock(side_effect=side_effect),
            ApiLabTab=MagicMock(side_effect=side_effect),
            PlaygroundTab=MagicMock(side_effect=side_effect),
            CodeReviewTab=MagicMock(side_effect=side_effect),
            ReleaseTab=MagicMock(side_effect=side_effect),
            TestGenTab=MagicMock(side_effect=side_effect),
            GitTab=MagicMock(side_effect=side_effect),
            PullRequestsTab=MagicMock(side_effect=side_effect),
            ConflictTab=MagicMock(side_effect=side_effect),
            BisectTab=MagicMock(side_effect=side_effect),
            DependenciesTab=MagicMock(side_effect=side_effect),
            SecurityTab=MagicMock(side_effect=side_effect),
            GuardrailsTab=MagicMock(side_effect=side_effect),
            ImpactTab=MagicMock(side_effect=side_effect),
            SentinelTab=MagicMock(side_effect=side_effect),
            DiskUsageTab=MagicMock(side_effect=side_effect),
            CodeMapTab=MagicMock(side_effect=side_effect),
            NetworkTab=MagicMock(side_effect=side_effect),
            NetDiagTab=MagicMock(side_effect=side_effect),
            SnippetsTab=MagicMock(side_effect=side_effect),
            TimelineTab=MagicMock(side_effect=side_effect),
            DataLabTab=MagicMock(side_effect=side_effect),
            SemVerTab=MagicMock(side_effect=side_effect),
            LogicLabTab=MagicMock(side_effect=side_effect),
            DatabaseTab=MagicMock(side_effect=side_effect),
            DatabaseDiagramTab=MagicMock(side_effect=side_effect),
            EnvTab=MagicMock(side_effect=side_effect),
            ProxyLabTab=MagicMock(side_effect=side_effect),
            JwtLabTab=MagicMock(side_effect=side_effect),
            SanitizerTab=MagicMock(side_effect=side_effect),
            FrontendTab=MagicMock(side_effect=side_effect),
            I18nTab=MagicMock(side_effect=side_effect),
            PresentationTab=MagicMock(side_effect=side_effect),
            QuizTab=MagicMock(side_effect=side_effect),
            RegexLabTab=MagicMock(side_effect=side_effect),
            CronLabTab=MagicMock(side_effect=side_effect),
            TimeLabTab=MagicMock(side_effect=side_effect),
            MathLabTab=MagicMock(side_effect=side_effect),
            UnitLabTab=MagicMock(side_effect=side_effect),
            NotebookLabTab=MagicMock(side_effect=side_effect),
            DevToolsTab=MagicMock(side_effect=side_effect),
            HexTab=MagicMock(side_effect=side_effect),
            JsonLabTab=MagicMock(side_effect=side_effect),
            YamlLabTab=MagicMock(side_effect=side_effect),
            MarkdownLabTab=MagicMock(side_effect=side_effect),
            CsvLabTab=MagicMock(side_effect=side_effect),
            DiffLabTab=MagicMock(side_effect=side_effect),
            ImageLabTab=MagicMock(side_effect=side_effect),
            ServicesTab=MagicMock(side_effect=side_effect),
            OtpLabTab=MagicMock(side_effect=side_effect),
            SearchTab=MagicMock(side_effect=side_effect),
            ScaffoldTab=MagicMock(side_effect=side_effect),
            PlanTab=MagicMock(side_effect=side_effect),
            ResearchTab=MagicMock(side_effect=side_effect),
            GanttTab=MagicMock(side_effect=side_effect),
            StandupTab=MagicMock(side_effect=side_effect),
            SystemMonitorTab=MagicMock(side_effect=side_effect),
            TerminalTab=MagicMock(side_effect=side_effect),
            DockerTab=MagicMock(side_effect=side_effect),
            K8sTab=MagicMock(side_effect=side_effect),
            TerraformTab=MagicMock(side_effect=side_effect),
            ChaosTab=MagicMock(side_effect=side_effect),
            SchedulerTab=MagicMock(side_effect=side_effect),
            IdeConfigTab=MagicMock(side_effect=side_effect),
            ADRTab=MagicMock(side_effect=side_effect),
            ProductivityTab=MagicMock(side_effect=side_effect),
            ProfileTab=MagicMock(side_effect=side_effect),
        )
        self.patcher_tabs.start()

    def tearDown(self):
        self.patcher_db.stop()
        self.patcher_km.stop()
        self.patcher_ask.stop()
        self.patcher_tm.stop()
        self.patcher_tabs.stop()
        shutil.rmtree(self.test_dir)

    async def test_tasks_tab_structure(self):
        """Test that the Tasks tab has the correct widgets."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            # Check if tab exists
            self.assertTrue(app.query_one("#tab-tasks"))

            # Switch to tasks tab
            app.query_one("#main-tabs").active = "tab-tasks"
            await pilot.pause()

            tasks_tab = app.query_one(TasksTab)
            self.assertIsNotNone(tasks_tab)

            self.assertIsInstance(tasks_tab.query_one("#tasks-table"), DataTable)
            self.assertIsInstance(tasks_tab.query_one("#btn-tasks-refresh"), Button)
            self.assertIsInstance(tasks_tab.query_one("#select-task-source"), Select)
            self.assertIsInstance(tasks_tab.query_one("#input-task-filter"), Input)

    async def test_tasks_load(self):
        """Test that tasks are loaded into the table."""
        mock_tasks = [
            Task(id="1", source="github", title="Task 1", status="Open"),
            Task(id="2", source="todo", title="Task 2", status="Open")
        ]
        self.mock_tm.fetch_all_tasks.return_value = mock_tasks

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            app.query_one("#main-tabs").active = "tab-tasks"
            await pilot.pause()

            tasks_tab = app.query_one(TasksTab)
            table = tasks_tab.query_one("#tasks-table", DataTable)

            self.assertEqual(table.row_count, 2)
            self.mock_tm.fetch_all_tasks.assert_called()

    async def test_tasks_refresh(self):
        """Test the refresh button."""
        self.mock_tm.fetch_all_tasks.return_value = []

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            app.query_one("#main-tabs").active = "tab-tasks"
            await pilot.pause()

            initial_count = self.mock_tm.fetch_all_tasks.call_count

            await pilot.click("#btn-tasks-refresh")
            await pilot.pause()

            self.assertGreater(self.mock_tm.fetch_all_tasks.call_count, initial_count)

    async def test_tasks_filter(self):
        """Test filtering tasks locally."""
        mock_tasks = [
            Task(id="1", source="github", title="Alpha", status="Open"),
            Task(id="2", source="todo", title="Beta", status="Open")
        ]
        self.mock_tm.fetch_all_tasks.return_value = mock_tasks

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            app.query_one("#main-tabs").active = "tab-tasks"
            await pilot.pause()

            tasks_tab = app.query_one(TasksTab)
            table = tasks_tab.query_one("#tasks-table", DataTable)
            self.assertEqual(table.row_count, 2)

            # Filter by text
            await pilot.click("#input-task-filter")
            await pilot.press("A", "l", "p")
            await pilot.pause()

            # Should filter to 1
            if table.row_count == 2:
                 input_widget = tasks_tab.query_one("#input-task-filter", Input)
                 input_widget.value = "Alp"
                 await pilot.pause()

            self.assertLess(table.row_count, 2)

if __name__ == "__main__":
    unittest.main()

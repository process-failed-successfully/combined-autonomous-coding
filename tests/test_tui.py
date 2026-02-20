import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, DirectoryTree, RichLog, TabbedContent, DataTable, Input, Select, ListView, Checkbox
from textual.containers import Container
from shared.tui import AgentTUI, DashboardTab, InteractTab, KnowledgeTab
from shared.tui_explorer import FileExplorerTab
from shared.tui_log_explorer import LogExplorerTab

class TestTUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock init_db to prevent side effects
        self.patcher_db = patch("shared.tui.init_db")
        self.mock_init_db = self.patcher_db.start()

        # Mock KnowledgeManager
        self.patcher_km = patch("shared.tui.KnowledgeManager")
        self.mock_km = self.patcher_km.start()

        # Mock run_ask_logic to avoid API calls
        self.patcher_ask = patch("shared.tui.run_ask_logic", new_callable=AsyncMock)
        self.mock_ask = self.patcher_ask.start()

        # Patch heavy tabs to avoid side effects (timers, threads, IO) and speed up tests
        # We replace them with a simple Container
        side_effect = lambda *args, **kwargs: Container()

        self.patcher_tabs = patch.multiple("shared.tui",
            ProcLabTab=MagicMock(side_effect=side_effect),
            LogTailTab=MagicMock(side_effect=side_effect),
            TasksTab=MagicMock(side_effect=side_effect),
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
        self.patcher_tabs.stop()
        shutil.rmtree(self.test_dir)

    async def test_app_startup(self):
        """Test that the app starts up and has the expected title and tabs."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            # Check if TabbedContent exists
            self.assertIsInstance(app.query_one("#main-tabs"), TabbedContent)
            # Check if tabs are present by ID
            self.assertTrue(app.query_one("#tab-dashboard"))
            self.assertTrue(app.query_one("#tab-explorer"))
            self.assertTrue(app.query_one("#tab-logs"))
            # Check new tabs
            self.assertTrue(app.query_one("#tab-interact"))
            self.assertTrue(app.query_one("#tab-knowledge"))
            self.assertTrue(app.query_one("#tab-ide-config"))

    async def test_dashboard_content(self):
        """Test that the dashboard tab displays project info."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            # Switch to dashboard is default
            dashboard = app.query_one(DashboardTab)
            self.assertIsNotNone(dashboard)

            # Check for labels
            labels = dashboard.query(Label)
            # We look for partial matches as content might vary
            self.assertTrue(any("Project:" in str(l.render()) for l in labels))

            # Check for buttons
            self.assertTrue(dashboard.query_one("#btn-test"))
            self.assertTrue(dashboard.query_one("#btn-lint"))

            # Check new history section
            self.assertTrue(dashboard.query_one("#history-log"))

    async def test_file_explorer_tab(self):
        """Test the file explorer tab structure."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            # Switch to explorer tab
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-explorer"
            await pilot.pause()

            explorer = app.query_one(FileExplorerTab)
            self.assertIsNotNone(explorer)

            # Check for DirectoryTree and RichLog (preview)
            self.assertIsInstance(explorer.query_one(DirectoryTree), DirectoryTree)
            self.assertIsInstance(explorer.query_one(RichLog), RichLog)
            # Check for Hex View Checkbox
            self.assertIsInstance(explorer.query_one("#chk-hex-view"), Checkbox)

    @patch("shared.tui_log_explorer.get_all_log_files")
    async def test_logs_tab(self, mock_get_logs):
        """Test log explorer updates with file list."""
        # Setup mock log files
        log1 = self.test_dir / "test1.log"
        log1.write_text("10:00:00 - INFO - Log 1 Content")
        log2 = self.test_dir / "test2.log"
        log2.write_text("10:00:00 - INFO - Log 2 Content")

        mock_get_logs.return_value = [log1, log2]

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            # Switch to logs tab
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-logs"
            await pilot.pause()

            logs_tab = app.query_one(LogExplorerTab)
            log_list = logs_tab.query_one("#log-run-list", ListView)

            # Check list populated
            self.assertEqual(len(log_list.children), 2)

            # Simulate refresh
            await pilot.click("#btn-log-refresh")
            mock_get_logs.assert_called()

    async def test_interact_tab(self):
        """Test InteractTab structure."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-interact"
            await pilot.pause()

            interact = app.query_one(InteractTab)
            self.assertIsNotNone(interact)

            self.assertIsInstance(interact.query_one("#chat-history"), RichLog)
            self.assertIsInstance(interact.query_one("#chat-input"), Input)
            self.assertIsInstance(interact.query_one("#agent-select"), Select)

    async def test_knowledge_tab(self):
        """Test KnowledgeTab structure and loading."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-knowledge"
            await pilot.pause()

            knowledge = app.query_one(KnowledgeTab)
            self.assertIsNotNone(knowledge)

            self.assertIsInstance(knowledge.query_one("#knowledge-table"), DataTable)
            self.assertIsInstance(knowledge.query_one("#knowledge-input"), Input)

            # Verify DB was initialized on mount (implicit in InteractTab mount which happens on startup for all tabs in Textual?)
            # Wait, TabPane content might be lazy loaded or not. But on_mount of the widget itself happens.
            # TabbedContent mounts all children? Usually.

            # Let's verify KM list_knowledge was called
            self.mock_km.return_value.list_knowledge.assert_called()


class TestTUIComponents(unittest.IsolatedAsyncioTestCase):
    """Unit tests for individual components logic."""
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(parents=True, exist_ok=True)

    @patch("shared.tui.run_ask_logic", new_callable=AsyncMock)
    async def test_interact_tab_submit(self, mock_run_ask):
        """Test that submitting input in InteractTab calls the agent logic."""
        tab = InteractTab(self.project_dir)

        # Mock query_one to return mocks for widgets
        mock_log = MagicMock(spec=RichLog)
        mock_input = MagicMock(spec=Input)
        mock_select = MagicMock(spec=Select)
        mock_select.value = "gemini"

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#chat-history": mock_log,
            "#chat-input": mock_input,
            "#agent-select": mock_select
        }.get(selector))

        mock_event = MagicMock()
        mock_event.value = "Hello agent"
        mock_event.input = mock_input

        await tab.on_input_submitted(mock_event)

        mock_run_ask.assert_called_once()
        call_args = mock_run_ask.call_args[1]
        self.assertEqual(call_args["query"], "Hello agent")
        self.assertEqual(call_args["agent_type"], "gemini")

    @patch("shared.tui.KnowledgeManager")
    @patch("shared.tui.init_db")
    def test_knowledge_tab_load(self, mock_init_db, MockKnowledgeManager):
        """Test that KnowledgeTab loads data on mount."""
        mock_manager = MockKnowledgeManager.return_value
        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.category = "Test"
        mock_item.content = "Content"
        mock_item.source_agent = "User"
        mock_manager.list_knowledge.return_value = [mock_item]

        tab = KnowledgeTab(self.project_dir)

        mock_table = MagicMock(spec=DataTable)
        tab.query_one = MagicMock(return_value=mock_table)

        tab.on_mount()

        mock_init_db.assert_called_once()
        mock_manager.list_knowledge.assert_called_once()
        mock_table.add_row.assert_called_with("1", "Test", "Content", "User")

    @patch("main.sys.exit")
    @patch("shared.tui.AgentTUI")
    def test_main_run_tui(self, MockAgentTUI, mock_exit):
        """Test that main.run_tui instantiates and runs the app."""
        from main import run_tui
        import argparse

        args = argparse.Namespace(project_dir=self.project_dir)

        run_tui(args)

        MockAgentTUI.assert_called_with(project_dir=self.project_dir)
        MockAgentTUI.return_value.run.assert_called_once()
        mock_exit.assert_called_with(0)

    def test_file_explorer_hex_view(self):
        """Test file explorer hex view logic."""
        tab = FileExplorerTab(self.project_dir)

        # Test hexdump
        data = b"Hello World"
        dump = tab.hexdump(data)
        self.assertIn("48 65 6c 6c 6f", dump) # Hex for Hello
        self.assertIn("|Hello World|", dump)

if __name__ == "__main__":
    unittest.main()

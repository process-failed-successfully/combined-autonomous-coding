import unittest
import shutil
import tempfile
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.widgets import TextArea, DataTable, Button, RichLog
from textual.containers import Container
from shared.tui import AgentTUI, DocumentationTab

# Mock tab to isolate DocumentationTab testing
class MockTab(Container):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

class TestTUIDocs(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Create temp dir
        self.test_dir = Path(tempfile.mkdtemp())

        self.mock_docstring_mgr = MagicMock()
        self.mock_link_checker = MagicMock()
        self.mock_openapi_gen = MagicMock()

        self.patches = [
            patch('shared.tui.DocstringManager', return_value=self.mock_docstring_mgr),
            patch('shared.tui.LinkChecker', return_value=self.mock_link_checker),
            patch('shared.tui.OpenAPIGenerator', return_value=self.mock_openapi_gen),
            # Patch other managers instantiated by AgentTUI to avoid side effects
            patch('shared.tui.WorkSessionManager'),
            patch('shared.tui.TimelineCollector'),
            patch('shared.tui.TimelineRenderer'),
            patch('shared.tui.get_all_log_files', return_value=[]),
            patch('shared.tui.get_git_info', return_value={"branch": "main", "status": "Clean"}),
            patch('shared.tui.get_workflow_stage', return_value="Dev"),
            patch('shared.tui.get_git_log', return_value=[]),
            patch('shared.tui.scan_project', return_value={}),
            patch('shared.tui.RecipeManager'),
            patch('shared.tui.WorktreeManager'),
            patch('shared.tui.DependencyAnalyzer'),
            patch('shared.tui.DependencyUpdater'),
            patch('shared.tui.TaskManager'),
            patch('shared.tui.KnowledgeManager'),
            patch('shared.tui.init_db'), # prevent db init
            patch('shared.tui.ApiLabManager'),
            patch('shared.tui.PlaygroundManager'),
            patch('shared.tui.SecretsManager'),
            patch('shared.tui.TroubleshootManager'),
            patch('shared.tui.RecipeLearner'),
            patch('shared.tui.DebtCollector'),
            patch('shared.tui.SecurityAuditor'),
            patch('shared.tui.OptimizationManager'),

            # Patch tabs to isolate testing and prevent ServicesTab error
            patch('shared.tui.ServicesTab', MockTab),
            patch('shared.tui.DashboardTab', MockTab),
            patch('shared.tui.SystemMonitorTab', MockTab),
            patch('shared.tui.TerminalTab', MockTab),
            patch('shared.tui.DockerTab', MockTab),
            patch('shared.tui.ChaosTab', MockTab),
            patch('shared.tui.SchedulerTab', MockTab),
            patch('shared.tui.ConfigTab', MockTab),
            patch('shared.tui.IdeConfigTab', MockTab),
            patch('shared.tui.ADRTab', MockTab),
            patch('shared.tui.TestGenTab', MockTab),
            patch('shared.tui.ScaffoldTab', MockTab),
            patch('shared.tui.RefactorTab', MockTab),
            patch('shared.tui.PlanTab', MockTab),
            patch('shared.tui.InteractTab', MockTab),
            patch('shared.tui.ResearchTab', MockTab),
            patch('shared.tui.RecipesTab', MockTab),
            patch('shared.tui.CodeReviewTab', MockTab),
            patch('shared.tui.SearchTab', MockTab),
            patch('shared.tui.TasksTab', MockTab),
            patch('shared.tui.GanttTab', MockTab),
            patch('shared.tui.StandupTab', MockTab),
            patch('shared.tui.GitTab', MockTab),
            patch('shared.tui.PullRequestsTab', MockTab),
            patch('shared.tui.ConflictTab', MockTab),
            patch('shared.tui.BisectTab', MockTab),
            patch('shared.tui.ReleaseTab', MockTab),
            patch('shared.tui.WorktreesTab', MockTab),
            patch('shared.tui.DependenciesTab', MockTab),
            patch('shared.tui.AnalyticsTab', MockTab),
            patch('shared.tui.SecurityTab', MockTab),
            patch('shared.tui.GuardrailsTab', MockTab),
            patch('shared.tui.HealthTab', MockTab),
            patch('shared.tui.ImpactTab', MockTab),
            patch('shared.tui.TroubleshootTab', MockTab),
            patch('shared.tui.SentinelTab', MockTab),
            patch('shared.tui.KnowledgeTab', MockTab),
            patch('shared.tui.FileExplorerTab', MockTab),
            patch('shared.tui.DiskUsageTab', MockTab),
            patch('shared.tui.CodeMapTab', MockTab),
            patch('shared.tui.NetworkTab', MockTab),
            patch('shared.tui.SnippetsTab', MockTab),
            patch('shared.tui.ProfileTab', MockTab),
            patch('shared.tui.SessionTab', MockTab),
            patch('shared.tui.TimelineTab', MockTab),
            patch('shared.tui.LogExplorerTab', MockTab),
            patch('shared.tui.DataLabTab', MockTab),
            patch('shared.tui.LogicLabTab', MockTab),
            patch('shared.tui.DatabaseTab', MockTab),
            patch('shared.tui.DatabaseDiagramTab', MockTab),
            patch('shared.tui.SecretsTab', MockTab),
            patch('shared.tui.EnvTab', MockTab),
            patch('shared.tui.ApiLabTab', MockTab),
            patch('shared.tui.SanitizerTab', MockTab),
            patch('shared.tui.FrontendTab', MockTab),
            patch('shared.tui.CostTab', MockTab),
            patch('shared.tui.PlaygroundTab', MockTab),
            patch('shared.tui.PromptLabTab', MockTab),
            patch('shared.tui.PresentationTab', MockTab),
            patch('shared.tui.QuizTab', MockTab),
            patch('shared.tui.RegexLabTab', MockTab),
            patch('shared.tui.CronLabTab', MockTab),
            patch('shared.tui.DevToolsTab', MockTab),
        ]
        for p in self.patches:
            p.start()

    async def asyncTearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.test_dir)

    async def test_docs_tab_rendering(self):
        app = AgentTUI(project_dir=self.test_dir)

        async with app.run_test() as pilot:
            # Navigate to Docs tab
            tabs = app.query_one("#main-tabs")
            tabs.active = "tab-docs"
            await pilot.pause()

            # Check if DocumentationTab is present
            doc_tab = app.query_one(DocumentationTab)
            self.assertIsNotNone(doc_tab)

            # Check if "Overview" pane is active by default
            self.assertIsNotNone(doc_tab.query_one("#readme-editor"))

    async def test_docstrings_scan(self):
        app = AgentTUI(project_dir=self.test_dir)

        # Setup mock return with correct path structure
        dummy_file = self.test_dir / "src" / "main.py"
        self.mock_docstring_mgr.scan.return_value = [
            {"file": dummy_file, "name": "foo", "type": "FunctionDef", "lineno": 10}
        ]

        async with app.run_test() as pilot:
            tabs = app.query_one("#main-tabs")
            tabs.active = "tab-docs"
            await pilot.pause()

            doc_tab = app.query_one(DocumentationTab)

            # Invoke logic directly
            doc_tab.scan_docstrings()

            # Verify mock called
            self.mock_docstring_mgr.scan.assert_called_once()

            # Verify table population
            table = doc_tab.query_one("#docstring-table", DataTable)
            self.assertEqual(table.row_count, 1)

    async def test_check_links(self):
        app = AgentTUI(project_dir=self.test_dir)

        # Create a dummy markdown file so rglob finds something
        (self.test_dir / "README.md").write_text("# Hello")

        # Setup mock
        self.mock_link_checker.check_files.return_value = {
            "total_links": 1,
            "broken_links_count": 1,
            "files_with_issues": 1,
            "details": {
                self.test_dir / "README.md": [{"line": 1, "url": "http://bad.com", "status": 404, "error": None}]
            }
        }

        async with app.run_test() as pilot:
            tabs = app.query_one("#main-tabs")
            tabs.active = "tab-docs"
            await pilot.pause()

            doc_tab = app.query_one(DocumentationTab)

            # Trigger check
            await doc_tab.check_links()

            # Verify mock called
            self.mock_link_checker.check_files.assert_called_once()

            # Verify table population
            table = doc_tab.query_one("#links-table", DataTable)
            self.assertEqual(table.row_count, 1)

    async def test_generate_openapi(self):
        app = AgentTUI(project_dir=self.test_dir)

        # Setup mock
        self.mock_openapi_gen.generate = AsyncMock(return_value=True) # Async method

        async with app.run_test() as pilot:
            tabs = app.query_one("#main-tabs")
            tabs.active = "tab-docs"
            await pilot.pause()

            doc_tab = app.query_one(DocumentationTab)

            # Trigger generation
            await doc_tab.generate_openapi()

            # Verify mock called
            self.mock_openapi_gen.generate.assert_called_once()

import unittest
import shutil
import tempfile
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.widgets import TextArea, DataTable, Button, RichLog
from shared.tui import AgentTUI, DocumentationTab

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
            patch('shared.tui.get_git_info', return_value={"branch": "main", "status": "Clean"}),
            patch('shared.tui.get_workflow_stage', return_value="Dev"),
            patch('shared.tui.RecipeManager'),
            patch('shared.tui.WorktreeManager'),
            patch('shared.tui.TaskManager'),
            patch('shared.tui.KnowledgeManager'),
            patch('shared.tui.ApiLabManager'),
            patch('shared.tui.PlaygroundManager'),
            patch('shared.tui.SecretsManager'),
            patch('shared.tui.TroubleshootManager'),
            patch('shared.tui.RecipeLearner'),
            patch('shared.tui.DebtCollector'),
            patch('shared.tui.SecurityAuditor'),
            patch('shared.tui.OptimizationManager'),
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

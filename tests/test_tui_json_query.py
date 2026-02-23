import unittest
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_json import JsonLabTab
from unittest.mock import MagicMock, patch
import asyncio

class JsonLabTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir
        self.tab = JsonLabTab(project_dir)

    def compose(self) -> ComposeResult:
        yield self.tab

class TestTuiJsonQuery(unittest.IsolatedAsyncioTestCase):
    async def test_query_execution(self):
        project_dir = Path(".")
        app = JsonLabTestApp(project_dir)

        # Mock Manager
        app.tab.manager = MagicMock()
        app.tab.manager.load_json.return_value = {"items": [{"id": 1}, {"id": 2}]}
        app.tab.manager.query.return_value = [{"id": 2}]

        async with app.run_test(size=(120, 40)) as pilot:
            # Inject data
            app.tab.current_data = {"items": [{"id": 1}, {"id": 2}]}
            app.tab.build_tree()

            # Switch to Query tab
            tabbed_content = app.tab.query_one("#json-mode-tabs")
            tabbed_content.active = "tab-json-query"

            # Wait for tab switch
            await pilot.pause()

            # Set query input
            query_input = app.tab.query_one("#json-query-input")
            query_input.value = "[i for i in data['items'] if i['id'] > 1]"

            # Run query
            await pilot.click("#btn-json-run-query")

            # Wait for event processing
            await pilot.pause()

            # Check manager call
            app.tab.manager.query.assert_called_with(app.tab.current_data, "[i for i in data['items'] if i['id'] > 1]")

            # Check results table
            table = app.tab.query_one("#json-query-table")
            self.assertEqual(table.row_count, 1)
            self.assertEqual(str(table.get_cell_at((0, 0))), "2")

    async def test_tree_filter(self):
        project_dir = Path(".")
        app = JsonLabTestApp(project_dir)

        # Flatted data structure for easier testing of root children
        data = {
            "match_key": "value",
            "ignore_key": "value",
            "nested_container": {
                "match_inner": "inner"
            }
        }

        async with app.run_test(size=(120, 40)) as pilot:
            app.tab.current_data = data
            app.tab.build_tree()
            await pilot.pause()

            tree = app.tab.query_one("#json-tree")
            # Root should have 3 children: match_key, ignore_key, nested_container
            self.assertEqual(len(tree.root.children), 3)

            # Apply filter
            app.tab.filter_text = "match"
            app.tab.build_tree()
            await pilot.pause()

            # Expected behavior with simple filter:
            # 1. "match_key" matches "match" -> Shown
            # 2. "ignore_key" does not match -> Hidden (skipped)
            # 3. "nested_container" (key) does not match "match".
            #    Our simple logic says: if it's a container and doesn't match, show it ONLY IF we didn't implement strict filtering.
            #    My implementation:
            #    if self.filter_text and not match:
            #        if is_leaf: continue
            #    So containers ARE added even if they don't match.

            # So we expect "match_key" AND "nested_container" to be present.
            # "ignore_key" (leaf) should be gone.

            children_labels = [str(node.label) for node in tree.root.children]
            # Strip markup for checking
            plain_labels = [l.replace("[bold]", "").replace("[/bold]", "") for l in children_labels]

            self.assertTrue(any("match_key" in l for l in plain_labels))
            self.assertFalse(any("ignore_key" in l for l in plain_labels))
            self.assertTrue(any("nested_container" in l for l in plain_labels))

            self.assertEqual(len(tree.root.children), 2)

if __name__ == '__main__':
    unittest.main()

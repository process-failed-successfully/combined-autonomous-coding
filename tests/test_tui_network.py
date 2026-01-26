import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import asyncio
from shared.tui_network import NetworkTab

class TestNetworkTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = NetworkTab(self.project_dir)
        # Mock Textual methods that interact with UI
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    @patch("shared.tui_network.NetworkBuilder")
    async def test_build_graph_logic(self, MockBuilder):
        mock_builder = MockBuilder.return_value

        # Mock return of add_file_nodes needed for add_import_edges
        mock_builder.add_file_nodes.return_value = {}

        # Setup mock data that would be populated by builder methods
        mock_builder.nodes = {
            "1": {"id": "1", "label": "A.py", "group": "file"},
            "2": {"id": "2", "label": "B.py", "group": "file"},
            "3": {"id": "3", "label": "Dev", "group": "author"}
        }
        mock_builder.edges = [
            {"from": "1", "to": "2", "title": "imports"},
            {"from": "3", "to": "1", "title": "edited"}
        ]

        # Run the method
        await self.tab._build_graph()

        # Assertions
        self.assertEqual(self.tab.nodes, mock_builder.nodes)
        self.assertEqual(self.tab.edges, mock_builder.edges)

        # Verify graph processing (adjacency lists)
        # 1 -> 2
        self.assertEqual(len(self.tab.adj_out["1"]), 1)
        self.assertEqual(self.tab.adj_out["1"][0]["to"], "2")

        # 3 -> 1
        self.assertEqual(len(self.tab.adj_out["3"]), 1)
        self.assertEqual(self.tab.adj_out["3"][0]["to"], "1")

        # 2 <- 1
        self.assertEqual(len(self.tab.adj_in["2"]), 1)
        self.assertEqual(self.tab.adj_in["2"][0]["from"], "1")

        # Verify Builder method calls
        # Since these are called in a thread, checking call count might be tricky if not awaited properly
        # But we await asyncio.to_thread, so it should be done.

        # Note: mocking methods on the instance that is returned by constructor
        mock_builder.add_file_nodes.assert_called()
        mock_builder.add_import_edges.assert_called()
        mock_builder.add_git_history.assert_called()

        # Verify UI update called
        self.tab.query_one.assert_called() # _update_list calls this to get ListView

    @patch("shared.tui_network.NetworkBuilder")
    async def test_error_handling(self, MockBuilder):
        mock_builder = MockBuilder.return_value
        mock_builder.add_file_nodes.side_effect = Exception("Git error")

        await self.tab._build_graph()

        self.tab.notify.assert_called_with("Error building graph: Git error", severity="error")

if __name__ == "__main__":
    unittest.main()

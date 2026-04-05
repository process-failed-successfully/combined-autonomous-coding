import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from textual.app import App, ComposeResult
from shared.tui_chart import ChartLabTab
import tempfile
import os
import shutil

class ChartTestApp(App):
    def compose(self) -> ComposeResult:
        yield ChartLabTab()

class TestChartLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.test_dir, "test.csv")
        with open(self.csv_path, "w") as f:
            f.write("X,Y\n1,10\n2,20")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    async def asyncSetUp(self):
        self.app = ChartTestApp()
        self.manager_mock = MagicMock()

    async def test_load_and_plot(self):
        # We need to set a screen size to ensure visibility/clickability
        async with self.app.run_test(size=(120, 40)) as pilot:
            tab = self.app.query_one(ChartLabTab)
            # Mock the manager
            tab.manager = self.manager_mock

            # Setup mock return values
            sample_data = [{"X": 1, "Y": 10}, {"X": 2, "Y": 20}]

            # Simulate Load Data
            input_widget = tab.query_one("#chart-file-input")
            input_widget.value = self.csv_path

            # Mock asyncio.to_thread
            with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
                mock_to_thread.return_value = sample_data

                app.query_one("#btn-chart-load-file").press()
        await pilot.pause()

                # Check if data loaded
                self.assertEqual(tab.current_data, sample_data)

                # Check selects populated
                select_x = tab.query_one("#select-chart-x")
                select_y = tab.query_one("#select-chart-y")

                # Textual Select widget logic
                self.assertEqual(select_x.value, "X")
                self.assertEqual(select_y.value, "Y")

                # Mock plot_bar return
                tab.manager.plot_bar = MagicMock(return_value="[BAR CHART]")

                # Trigger Plot
                app.query_one("#btn-chart-plot").press()
        await pilot.pause()

                # Verify plot called
                tab.manager.plot_bar.assert_called_with(sample_data, "X", "Y")

    async def test_initial_state(self):
        async with self.app.run_test(size=(120, 40)) as pilot:
            tab = self.app.query_one(ChartLabTab)
            self.assertEqual(tab.current_data, [])
            self.assertTrue(tab.query_one("#btn-chart-plot").disabled)

if __name__ == "__main__":
    unittest.main()

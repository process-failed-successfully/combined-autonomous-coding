import sys
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from textual.app import App, ComposeResult
from shared.tui_geo import GeoLabTab

class GeoLabApp(App):
    def compose(self) -> ComposeResult:
        yield GeoLabTab()

class TestGeoLabTUIErrors(unittest.IsolatedAsyncioTestCase):
    @patch("shared.tui_geo.GeoLabManager")
    async def test_geo_locate_error(self, MockGeoManager):
        mock_mgr_instance = MockGeoManager.return_value
        mock_mgr_instance.locate.return_value = {
            "status": "fail",
            "message": "invalid query"
        }

        app = GeoLabApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#geo-query-input").value = "invalid"
            app.query_one("#btn-geo-locate").press()

            await pilot.pause(0.1)

            mock_mgr_instance.locate.assert_called_with("invalid")
            log = app.query_one("#geo-locate-log")
            self.assertIn("Failed", "\n".join(line.text for line in log.lines))

    @patch("shared.tui_geo.GeoLabManager")
    async def test_geo_distance_error(self, MockGeoManager):
        app = GeoLabApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Invalid input
            app.query_one("#geo-dist-p1").value = "invalid"
            app.query_one("#geo-dist-p2").value = "41.0,-75.0"

            app.query_one("#btn-geo-dist").press()
            await pilot.pause(0.1)

            log = app.query_one("#geo-dist-log")
            self.assertIn("Error", "\n".join(line.text for line in log.lines))

    @patch("shared.tui_geo.GeoLabManager")
    async def test_geo_map_error(self, MockGeoManager):
        app = GeoLabApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Invalid input
            app.query_one("#geo-map-input").value = "invalid"

            app.query_one("#btn-geo-map").press()
            await pilot.pause(0.1)

            log = app.query_one("#geo-map-log")
            self.assertIn("Error", "\n".join(line.text for line in log.lines))

if __name__ == '__main__':
    unittest.main()

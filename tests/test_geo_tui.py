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

class TestGeoLabTUI(unittest.IsolatedAsyncioTestCase):
    @patch("shared.tui_geo.GeoLabManager")
    async def test_geo_locate(self, MockGeoManager):
        # Setup mock manager
        mock_mgr_instance = MockGeoManager.return_value
        mock_mgr_instance.locate.return_value = {
            "status": "success",
            "query": "8.8.8.8",
            "city": "Test City",
            "regionName": "Test Region",
            "country": "Test Country",
            "lat": 1.0,
            "lon": 2.0,
            "isp": "Test ISP",
            "timezone": "UTC"
        }
        mock_mgr_instance.map_url.return_value = "http://maps.google.com/?q=1.0,2.0"

        app = GeoLabApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#geo-query-input").value = "8.8.8.8"

            app.query_one("#btn-geo-locate").press()

            await pilot.pause(0.1)

            mock_mgr_instance.locate.assert_called_with("8.8.8.8")
            log = app.query_one("#geo-locate-log")
            self.assertIn("Test City", "\n".join(line.text for line in log.lines))

    @patch("shared.tui_geo.GeoLabManager")
    async def test_geo_distance(self, MockGeoManager):
        mock_mgr_instance = MockGeoManager.return_value
        mock_mgr_instance.calculate_distance.return_value = {
            "km": 10.5,
            "miles": 6.5
        }

        app = GeoLabApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#geo-dist-p1").value = "40.0,-74.0"
            app.query_one("#geo-dist-p2").value = "41.0,-75.0"

            app.query_one("#btn-geo-dist").press()
            await pilot.pause(0.1)

            mock_mgr_instance.calculate_distance.assert_called_with(40.0, -74.0, 41.0, -75.0)
            log = app.query_one("#geo-dist-log")
            self.assertIn("10.5 km", "\n".join(line.text for line in log.lines))

    @patch("shared.tui_geo.GeoLabManager")
    async def test_geo_map(self, MockGeoManager):
        mock_mgr_instance = MockGeoManager.return_value
        mock_mgr_instance.map_url.return_value = "http://maps.google.com/?q=40.0,-74.0"

        app = GeoLabApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#geo-map-input").value = "40.0,-74.0"

            app.query_one("#btn-geo-map").press()
            await pilot.pause(0.1)

            mock_mgr_instance.map_url.assert_called_with(40.0, -74.0)
            log = app.query_one("#geo-map-log")
            self.assertIn("http://maps.google.com/?q=40.0,-74.0", "\n".join(line.text for line in log.lines))

if __name__ == '__main__':
    unittest.main()

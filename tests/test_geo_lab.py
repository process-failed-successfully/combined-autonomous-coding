import unittest
from unittest.mock import MagicMock, patch
from shared.geo_lab import GeoLabManager

class TestGeoLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = GeoLabManager()

    @patch("requests.get")
    def test_locate_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "query": "8.8.8.8",
            "country": "United States",
            "lat": 39.03,
            "lon": -77.5
        }
        mock_get.return_value = mock_response

        result = self.manager.locate("8.8.8.8")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["country"], "United States")

    @patch("requests.get")
    def test_locate_fail(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "fail",
            "message": "reserved range"
        }
        mock_get.return_value = mock_response

        result = self.manager.locate("127.0.0.1")
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["message"], "reserved range")

    def test_distance(self):
        # Distance between London (51.5074, -0.1278) and Paris (48.8566, 2.3522)
        # Approx 344 km
        dist = self.manager.calculate_distance(51.5074, -0.1278, 48.8566, 2.3522)
        self.assertTrue(340 < dist["km"] < 350)
        self.assertTrue(210 < dist["miles"] < 220)

    def test_map_url(self):
        url = self.manager.map_url(40.7128, -74.0060)
        self.assertIn("40.7128,-74.006", url)
        self.assertTrue(url.startswith("https://www.google.com/maps/search/"))

if __name__ == '__main__':
    unittest.main()

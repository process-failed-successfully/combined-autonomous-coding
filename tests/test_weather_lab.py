import unittest
from unittest.mock import patch, MagicMock
from shared.weather_lab import WeatherLabManager

class TestWeatherLab(unittest.TestCase):

    def setUp(self):
        self.manager = WeatherLabManager()

    @patch('shared.weather_lab.GeoLabManager')
    @patch('shared.weather_lab.requests.get')
    def test_get_weather_success(self, mock_get, MockGeo):
        # Mock GeoLabManager
        mock_geo_instance = MockGeo.return_value
        mock_geo_instance.locate.return_value = {
            "status": "success",
            "lat": 51.5,
            "lon": -0.12,
            "city": "London",
            "regionName": "England",
            "country": "UK",
            "timezone": "Europe/London"
        }

        # Mock Requests
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current_weather": {
                "temperature": 15.0,
                "windspeed": 10.0,
                "weathercode": 1
            },
            "daily": {
                "time": ["2023-10-01", "2023-10-02"],
                "temperature_2m_max": [16.0, 17.0],
                "temperature_2m_min": [10.0, 11.0],
                "weathercode": [1, 2]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Need to re-init manager to use the mocked GeoLabManager class if it was instantiated in __init__
        # But wait, __init__ instantiates it. So patching the class 'shared.weather_lab.GeoLabManager'
        # before setUp runs would be ideal, but here I can just replace the instance attribute.
        self.manager.geo_manager = mock_geo_instance

        data = self.manager.get_weather("London")

        self.assertNotIn("error", data)
        self.assertEqual(data["location"]["city"], "London")
        self.assertEqual(data["current_weather"]["temperature"], 15.0)
        self.assertEqual(len(data["daily"]["time"]), 2)

    @patch('shared.weather_lab.GeoLabManager')
    def test_get_weather_location_fail(self, MockGeo):
        mock_geo_instance = MockGeo.return_value
        mock_geo_instance.locate.return_value = {"status": "fail", "message": "Not found"}
        self.manager.geo_manager = mock_geo_instance

        data = self.manager.get_weather("InvalidCity")
        self.assertIn("error", data)
        self.assertIn("Location not found", data["error"])

    def test_weather_code_description(self):
        self.assertEqual(self.manager.get_weather_code_description(0), "Clear sky")
        self.assertEqual(self.manager.get_weather_code_description(999), "Unknown")

if __name__ == '__main__':
    unittest.main()

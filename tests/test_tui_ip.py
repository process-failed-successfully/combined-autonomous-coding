import unittest
from unittest.mock import patch, MagicMock
from textual.app import App
from shared.tui_ip import IpLabTab
from textual.widgets import Input, Markdown, Button


class DummyApp(App):
    def compose(self):
        yield IpLabTab()


class TestIpLabTab(unittest.IsolatedAsyncioTestCase):
    @patch('shared.ip_lab.IPLabManager.get_public_ip')
    async def test_get_public_ip(self, mock_get_public_ip):
        mock_get_public_ip.return_value = "8.8.8.8"
        app = DummyApp()
        async with app.run_test(size=(80, 24)) as pilot:
            with patch.object(Markdown, 'update', new_callable=MagicMock) as mock_markdown_update:
                tab = app.query_one(IpLabTab)
                btn = app.query_one("#btn-public-ip", Button)
                tab.on_button_pressed(Button.Pressed(btn))
                await pilot.pause()

                ip_input = app.query_one("#ip-input", Input)
                self.assertEqual(ip_input.value, "8.8.8.8")

                mock_markdown_update.assert_called()
                self.assertIn("8.8.8.8", mock_markdown_update.call_args[0][0])

    @patch('shared.ip_lab.IPLabManager.get_public_ip')
    async def test_get_public_ip_failure(self, mock_get_public_ip):
        mock_get_public_ip.return_value = None
        app = DummyApp()
        async with app.run_test(size=(80, 24)) as pilot:
            with patch.object(Markdown, 'update', new_callable=MagicMock) as mock_markdown_update:
                tab = app.query_one(IpLabTab)
                btn = app.query_one("#btn-public-ip", Button)
                tab.on_button_pressed(Button.Pressed(btn))
                await pilot.pause()

                mock_markdown_update.assert_called()
                self.assertIn("Failed to fetch public IP", mock_markdown_update.call_args[0][0])

    @patch('shared.ip_lab.IPLabManager.get_info')
    @patch('shared.ip_lab.IPLabManager.geolocate')
    @patch('shared.ip_lab.IPLabManager.is_valid')
    async def test_info_and_geolocation(self, mock_is_valid, mock_geolocate, mock_get_info):
        mock_is_valid.return_value = True
        mock_get_info.return_value = {
            'version': 4,
            'is_private': False,
            'is_global': True,
            'is_multicast': False,
            'is_loopback': False,
            'is_link_local': False,
            'hex': '0x08080808'
        }
        mock_geolocate.return_value = {
            'city': 'Mountain View',
            'region': 'California',
            'country_name': 'United States',
            'latitude': '37.386',
            'longitude': '-122.0838',
            'org': 'Google LLC'
        }

        app = DummyApp()
        async with app.run_test(size=(80, 24)) as pilot:
            with patch.object(Markdown, 'update', new_callable=MagicMock) as mock_markdown_update:
                ip_input = app.query_one("#ip-input", Input)
                ip_input.value = "8.8.8.8"

                tab = app.query_one(IpLabTab)
                btn = app.query_one("#btn-ip-info", Button)
                tab.on_button_pressed(Button.Pressed(btn))
                await pilot.pause()

                mock_markdown_update.assert_called()
                called_text = mock_markdown_update.call_args[0][0]
                self.assertIn("IPv4", called_text)
                self.assertIn("0x08080808", called_text)
                self.assertIn("Mountain View", called_text)
                self.assertIn("Google LLC", called_text)

    @patch('shared.ip_lab.IPLabManager.is_valid')
    async def test_info_invalid_ip(self, mock_is_valid):
        mock_is_valid.return_value = False

        app = DummyApp()
        async with app.run_test(size=(80, 24)) as pilot:
            with patch.object(Markdown, 'update', new_callable=MagicMock) as mock_markdown_update:
                ip_input = app.query_one("#ip-input", Input)
                ip_input.value = "invalid_ip"

                tab = app.query_one(IpLabTab)
                btn = app.query_one("#btn-ip-info", Button)
                tab.on_button_pressed(Button.Pressed(btn))
                await pilot.pause()

                mock_markdown_update.assert_called()
                self.assertIn("Invalid IP address format", mock_markdown_update.call_args[0][0])

    async def test_clear_button(self):
        app = DummyApp()
        async with app.run_test(size=(80, 24)) as pilot:
            with patch.object(Markdown, 'update', new_callable=MagicMock) as mock_markdown_update:
                ip_input = app.query_one("#ip-input", Input)
                ip_input.value = "1.2.3.4"

                tab = app.query_one(IpLabTab)
                btn = app.query_one("#btn-clear", Button)
                tab.on_button_pressed(Button.Pressed(btn))
                await pilot.pause()

                self.assertEqual(ip_input.value, "")
                mock_markdown_update.assert_called()
                self.assertIn("Results cleared", mock_markdown_update.call_args[0][0])


if __name__ == '__main__':
    unittest.main()

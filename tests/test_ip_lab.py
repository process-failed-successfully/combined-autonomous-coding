import unittest
from unittest.mock import patch, MagicMock
from shared.ip_lab import IPLabManager, run_ip_lab_logic
import argparse


class TestIPLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = IPLabManager()

    @patch('shared.ip_lab.requests.get')
    def test_get_public_ip_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'ip': '1.2.3.4'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        ip = self.manager.get_public_ip()
        self.assertEqual(ip, '1.2.3.4')
        mock_get.assert_called_with('https://api.ipify.org?format=json', timeout=5)

    @patch('shared.ip_lab.requests.get')
    def test_get_public_ip_failure(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException()

        ip = self.manager.get_public_ip()
        self.assertIsNone(ip)

    @patch('shared.ip_lab.requests.get')
    def test_geolocate_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'city': 'Test City', 'country_name': 'Test Country'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        geo = self.manager.geolocate('8.8.8.8')
        self.assertEqual(geo['city'], 'Test City')
        mock_get.assert_called_with('https://ipapi.co/8.8.8.8/json/', timeout=5)

    def test_is_valid_ip(self):
        self.assertTrue(self.manager.is_valid('192.168.1.1'))
        self.assertTrue(self.manager.is_valid('2001:db8::1'))
        self.assertFalse(self.manager.is_valid('invalid_ip'))
        self.assertFalse(self.manager.is_valid('256.256.256.256'))

    def test_get_info_ipv4(self):
        info = self.manager.get_info('192.168.1.1')
        self.assertEqual(info['version'], 4)
        self.assertTrue(info['is_private'])
        self.assertEqual(info['hex'], '0xC0A80101')

    def test_get_info_ipv6(self):
        info = self.manager.get_info('2001:4860:4860::8888')
        self.assertEqual(info['version'], 6)
        self.assertFalse(info['is_private'])

    def test_get_info_invalid(self):
        info = self.manager.get_info('invalid')
        self.assertIsNone(info)


class TestIPLabCLI(unittest.TestCase):
    @patch('shared.ip_lab.IPLabManager.get_public_ip')
    def test_run_public(self, mock_get_public_ip):
        mock_get_public_ip.return_value = '1.2.3.4'
        args = argparse.Namespace(action='public', ip=None)

        with patch('builtins.print') as mock_print:
            result = run_ip_lab_logic(args)
            self.assertTrue(result)
            mock_print.assert_any_call("Public IP: 1.2.3.4")

    @patch('shared.ip_lab.IPLabManager.get_info')
    def test_run_info(self, mock_get_info):
        mock_get_info.return_value = {'version': 4, 'is_private': True, 'is_global': False, 'is_multicast': False, 'is_loopback': False, 'is_link_local': False, 'hex': '0xC0A80101'}
        args = argparse.Namespace(action='info', ip='192.168.1.1')

        with patch('builtins.print') as mock_print:
            result = run_ip_lab_logic(args)
            self.assertTrue(result)
            mock_print.assert_any_call("IP: 192.168.1.1")
            mock_print.assert_any_call("Version: IPv4")

    @patch('shared.ip_lab.IPLabManager.get_public_ip')
    @patch('shared.ip_lab.IPLabManager.geolocate')
    @patch('shared.ip_lab.IPLabManager.is_valid')
    def test_run_geo(self, mock_is_valid, mock_geolocate, mock_get_public_ip):
        mock_get_public_ip.return_value = '1.2.3.4'
        mock_is_valid.return_value = True
        mock_geolocate.return_value = {'city': 'Test City', 'country_name': 'Test Country', 'latitude': '10.0', 'longitude': '20.0'}
        args = argparse.Namespace(action='geo', ip=None)

        with patch('builtins.print') as mock_print:
            result = run_ip_lab_logic(args)
            self.assertTrue(result)
            mock_print.assert_any_call("Geolocating 1.2.3.4...")
            mock_print.assert_any_call("City: Test City")


if __name__ == '__main__':
    unittest.main()

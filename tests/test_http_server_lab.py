import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from shared.http_server_lab import HttpServerManager

class TestHttpServerManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.manager = HttpServerManager()

    @patch('shared.http_server_lab.web')
    async def test_start_static(self, mock_web):
        # Mock web.Application and runner
        mock_app = MagicMock()
        mock_web.Application.return_value = mock_app
        mock_runner = AsyncMock()
        mock_web.AppRunner.return_value = mock_runner
        mock_site = AsyncMock()
        mock_web.TCPSite.return_value = mock_site

        # We need to mock Path to avoid "Invalid directory" error since we pass a fake path
        with patch('shared.http_server_lab.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.is_dir.return_value = True
            # str(p) needs to return the path string
            mock_path.return_value.__str__.return_value = '/fake/path'

            await self.manager.start_static('/fake/path', 8000)

        # Verify calls
        mock_web.Application.assert_called_once()
        mock_app.router.add_static.assert_called_with('/', '/fake/path', show_index=True)
        mock_web.AppRunner.assert_called_with(mock_app)
        mock_runner.setup.assert_called_once()
        mock_web.TCPSite.assert_called_with(mock_runner, '0.0.0.0', 8000)
        mock_site.start.assert_called_once()

        self.assertEqual(self.manager.port, 8000)
        self.assertEqual(self.manager.type, "static")

    @patch('shared.http_server_lab.web')
    async def test_start_echo(self, mock_web):
        mock_app = MagicMock()
        mock_web.Application.return_value = mock_app
        mock_runner = AsyncMock()
        mock_web.AppRunner.return_value = mock_runner
        mock_site = AsyncMock()
        mock_web.TCPSite.return_value = mock_site

        await self.manager.start_echo(8001)

        # Verify calls
        mock_web.Application.assert_called_once()
        mock_app.router.add_route.assert_called()
        mock_web.AppRunner.assert_called_with(mock_app)
        mock_runner.setup.assert_called_once()
        mock_web.TCPSite.assert_called_with(mock_runner, '0.0.0.0', 8001)
        mock_site.start.assert_called_once()

        self.assertEqual(self.manager.port, 8001)
        self.assertEqual(self.manager.type, "echo")

    @patch('shared.http_server_lab.web')
    async def test_stop(self, mock_web):
        # Setup fake running server
        mock_runner = AsyncMock()
        mock_site = AsyncMock()

        self.manager.runner = mock_runner
        self.manager.site = mock_site
        self.manager.port = 9000

        await self.manager.stop()

        mock_site.stop.assert_called_once()
        mock_runner.cleanup.assert_called_once()
        self.assertIsNone(self.manager.site)
        self.assertIsNone(self.manager.runner)
        self.assertIsNone(self.manager.port)

if __name__ == '__main__':
    unittest.main()

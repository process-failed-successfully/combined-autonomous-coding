import unittest
from unittest.mock import patch, MagicMock
import sys
import io
from pathlib import Path
from main import main

class TestCliPlugins(unittest.IsolatedAsyncioTestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('main.PluginManager')
    async def test_plugins_list_command(self, mock_pm_cls, mock_stdout):
        # Setup mock manager
        mock_pm = MagicMock()
        mock_pm.list_plugins.return_value = ["test_plugin"]
        mock_pm_cls.return_value = mock_pm

        cmd = ["main.py", "plugins", "list"]
        with patch.object(sys, 'argv', cmd):
            with self.assertRaises(SystemExit) as cm:
                await main()

            self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("Loaded Plugins (1)", output)
        self.assertIn("test_plugin", output)
        # discover_plugins is called in parse_args AND run_plugins
        self.assertGreaterEqual(mock_pm.discover_plugins.call_count, 1)
        self.assertGreaterEqual(mock_pm.load_plugins.call_count, 1)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('main.PluginManager')
    async def test_plugins_install_command(self, mock_pm_cls, mock_stdout):
        mock_pm = MagicMock()
        mock_pm.install_plugin.return_value = True
        mock_pm_cls.return_value = mock_pm

        cmd = ["main.py", "plugins", "install", "https://example.com/plugin.py"]
        with patch.object(sys, 'argv', cmd):
            with self.assertRaises(SystemExit) as cm:
                await main()

            self.assertEqual(cm.exception.code, 0)

        mock_pm.install_plugin.assert_called_with("https://example.com/plugin.py")
        self.assertIn("Plugin installed", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('main.PluginManager')
    async def test_plugins_create_command(self, mock_pm_cls, mock_stdout):
        mock_pm = MagicMock()
        mock_pm.create_plugin.return_value = Path("plugins/my_plugin.py")
        mock_pm_cls.return_value = mock_pm

        cmd = ["main.py", "plugins", "create", "my_plugin"]
        with patch.object(sys, 'argv', cmd):
            with self.assertRaises(SystemExit) as cm:
                await main()

            self.assertEqual(cm.exception.code, 0)

        mock_pm.create_plugin.assert_called_with("my_plugin")
        self.assertIn("Plugin scaffold created", mock_stdout.getvalue())

if __name__ == "__main__":
    unittest.main()

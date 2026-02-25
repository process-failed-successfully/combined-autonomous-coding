import unittest
import shutil
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from shared.dash_lab import DashLabManager, DashboardConfig, WidgetConfig


class TestDashLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = DashLabManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_default_config(self):
        config = self.manager.load_config()
        self.assertIsInstance(config, DashboardConfig)
        self.assertEqual(config.title, "Default Dashboard")
        self.assertTrue(len(config.widgets) > 0)

    def test_save_load_config(self):
        config = DashboardConfig(
            title="Test Dash",
            widgets=[
                WidgetConfig(type="metric", title="W1", row=0, col=0)
            ]
        )
        self.manager.save_config(config)

        loaded = self.manager.load_config()
        self.assertEqual(loaded.title, "Test Dash")
        self.assertEqual(len(loaded.widgets), 1)
        self.assertEqual(loaded.widgets[0].title, "W1")

    @patch('asyncio.create_subprocess_shell')
    def test_execute_command(self, mock_shell):
        # Setup mock process
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"Output\n", b""))
        mock_proc.returncode = 0
        mock_shell.return_value = mock_proc

        widget = WidgetConfig(type="metric", title="T", source="command", command="echo hi", row=0, col=0)

        result = asyncio.run(self.manager.execute_source(widget))
        self.assertEqual(result, "Output")

    def test_read_file(self):
        f = self.test_dir / "test.log"
        f.write_text("Log Content")

        widget = WidgetConfig(type="log", title="L", source="file", file_path="test.log", row=0, col=0)

        result = asyncio.run(self.manager.execute_source(widget))
        self.assertEqual(result, "Log Content")


if __name__ == '__main__':
    unittest.main()

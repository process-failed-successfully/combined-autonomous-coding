import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock
import sys

# Ensure shared module is importable
sys.path.append(str(Path(__file__).parent.parent))
from shared.plugin_manager import PluginManager

class TestPluginManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.plugin_manager = PluginManager(self.test_dir)

        # Create a dummy plugin
        self.plugin_content = """
def register_cli(subparsers):
    subparsers.add_parser("dummy", help="Dummy command")

def register_tui():
    return ("Dummy Tab", "Dummy Widget")
"""

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_discover_plugins_local(self):
        """Test discovering plugins in .agent_plugins directory."""
        plugins_dir = self.test_dir / ".agent_plugins"
        plugins_dir.mkdir()
        (plugins_dir / "test_plugin.py").write_text(self.plugin_content)

        self.plugin_manager.discover_plugins()
        # Should be at least 1, might check for specific inclusion
        self.assertTrue(any(str(p).endswith("test_plugin.py") for p in self.plugin_manager.plugin_paths))

    def test_load_plugins(self):
        """Test loading discovered plugins."""
        plugins_dir = self.test_dir / ".agent_plugins"
        plugins_dir.mkdir()
        (plugins_dir / "test_plugin.py").write_text(self.plugin_content)

        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugins()

        self.assertIn("test_plugin", self.plugin_manager.plugins)
        plugin = self.plugin_manager.plugins["test_plugin"]
        self.assertTrue(hasattr(plugin, "register_cli"))
        self.assertTrue(hasattr(plugin, "register_tui"))

    def test_register_cli(self):
        """Test CLI registration hook."""
        plugins_dir = self.test_dir / ".agent_plugins"
        plugins_dir.mkdir()
        (plugins_dir / "test_plugin.py").write_text(self.plugin_content)

        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugins()

        mock_subparsers = MagicMock()
        self.plugin_manager.register_cli(mock_subparsers)

        # Check if our dummy command was registered
        calls = [args[0] for args, _ in mock_subparsers.add_parser.call_args_list]
        self.assertIn("dummy", calls)

    def test_get_tui_tabs(self):
        """Test TUI tab retrieval."""
        plugins_dir = self.test_dir / ".agent_plugins"
        plugins_dir.mkdir()
        (plugins_dir / "test_plugin.py").write_text(self.plugin_content)

        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugins()

        tabs = self.plugin_manager.get_tui_tabs()
        # Check if our dummy tab is present
        self.assertTrue(any(t == ("Dummy Tab", "Dummy Widget") for t in tabs))

    def test_create_plugin(self):
        """Test creating a new plugin."""
        path = self.plugin_manager.create_plugin("new_plugin")
        self.assertTrue(path.exists())
        self.assertTrue(path.read_text().startswith("import argparse"))

if __name__ == "__main__":
    unittest.main()

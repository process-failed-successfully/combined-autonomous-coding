import unittest
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock
from shared.plugin_manager import PluginManager

# Mock textual widget for testing if textual is not installed
class MockLabel:
    def __init__(self, text):
        self.text = text

class TestPluginManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tests_temp_plugins")
        self.test_dir.mkdir(exist_ok=True)
        self.plugin_dir = self.test_dir / ".agent_plugins"
        self.plugin_dir.mkdir(exist_ok=True)

        # Create fixture dynamically
        fixture_content = """
# Mock Label if textual not present, though in test env we might mock it
class MockLabel:
    def __init__(self, text):
        self.text = text

def run_hello(args):
    print(f"Hello, {args.name}!")

def register_cli(subparsers):
    parser = subparsers.add_parser("hello", help="Prints hello")
    parser.add_argument("name", help="Name to greet")
    parser.set_defaults(run_plugin_func=run_hello)

def register_tui():
    return ("Hello", MockLabel("Hello from Plugin!"))
"""
        (self.plugin_dir / "hello_plugin.py").write_text(fixture_content)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        # Unload module if it was loaded to avoid side effects
        if "agent_plugin_hello_plugin" in sys.modules:
            del sys.modules["agent_plugin_hello_plugin"]

    def test_load_plugins(self):
        manager = PluginManager(self.test_dir)
        manager.load_plugins()
        self.assertIn("hello_plugin", manager.plugins)

    def test_register_cli(self):
        manager = PluginManager(self.test_dir)
        manager.load_plugins()

        mock_subparsers = MagicMock()
        manager.register_cli(mock_subparsers)

        # Check if add_parser was called with "hello"
        # The fixture calls subparsers.add_parser("hello", ...)
        mock_subparsers.add_parser.assert_called()

        # Verify call arguments
        calls = mock_subparsers.add_parser.call_args_list
        found = False
        for call in calls:
            if call[0][0] == "hello":
                found = True
                break
        self.assertTrue(found, "Plugin did not register 'hello' command")

    def test_get_tui_tabs(self):
        manager = PluginManager(self.test_dir)
        manager.load_plugins()

        tabs = manager.get_tui_tabs()
        self.assertGreaterEqual(len(tabs), 1)
        self.assertEqual(tabs[0][0], "Hello")

if __name__ == '__main__':
    unittest.main()

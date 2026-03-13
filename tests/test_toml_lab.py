import unittest
import unittest.mock
from shared.toml_lab import TomlLabManager
import tomlkit
import json

class TestTomlLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = TomlLabManager()
        self.sample_toml = """
[package]
name = "test-package"
version = "0.1.0"

[dependencies]
python = "^3.9"
requests = "^2.25.1"

[[bin]]
name = "test-bin"
path = "bin/test"
"""
        self.sample_data = self.manager.load_toml(self.sample_toml)

    def test_parse_path(self):
        self.assertEqual(self.manager._parse_path("a.b.c"), ["a", "b", "c"])
        self.assertEqual(self.manager._parse_path("a[0].b"), ["a", 0, "b"])
        self.assertEqual(self.manager._parse_path("a.0.b"), ["a", 0, "b"])
        self.assertEqual(self.manager._parse_path("key"), ["key"])

    def test_get(self):
        self.assertEqual(self.manager.get(self.sample_data, "package.name"), "test-package")
        self.assertEqual(self.manager.get(self.sample_data, "dependencies.python"), "^3.9")
        self.assertEqual(self.manager.get(self.sample_data, "bin[0].name"), "test-bin")

        # Test nonexistent keys
        self.assertIsNone(self.manager.get(self.sample_data, "package.description"))
        self.assertIsNone(self.manager.get(self.sample_data, "bin[1]"))

    def test_set(self):
        # Set existing
        self.manager.set(self.sample_data, "package.version", "0.2.0")
        self.assertEqual(self.sample_data["package"]["version"], "0.2.0")

        # Set new key
        self.manager.set(self.sample_data, "package.description", "A test package")
        self.assertEqual(self.sample_data["package"]["description"], "A test package")

        # Set list index
        self.manager.set(self.sample_data, "bin[0].path", "bin/new-test")
        self.assertEqual(self.sample_data["bin"][0]["path"], "bin/new-test")

        # Create nested structure
        data = tomlkit.document()
        self.manager.set(data, "a.b.c", 1)
        self.assertEqual(data["a"]["b"]["c"], 1)

    def test_delete(self):
        # Delete table key
        self.manager.delete(self.sample_data, "dependencies.requests")
        self.assertNotIn("requests", self.sample_data["dependencies"])

        # Delete list item
        self.manager.delete(self.sample_data, "bin[0]")
        self.assertEqual(len(self.sample_data["bin"]), 0)

    def test_merge(self):
        base_str = """
[package]
name = "base"
[dependencies]
a = "1.0"
"""
        override_str = """
[package]
version = "1.0"
[dependencies]
b = "2.0"
"""
        base = self.manager.load_toml(base_str)
        override = self.manager.load_toml(override_str)

        merged = self.manager.merge(base, override)

        self.assertEqual(merged["package"]["name"], "base")
        self.assertEqual(merged["package"]["version"], "1.0")
        self.assertEqual(merged["dependencies"]["a"], "1.0")
        self.assertEqual(merged["dependencies"]["b"], "2.0")

    def test_to_json(self):
        data = tomlkit.parse('key = "value"')
        json_str = self.manager.to_json(data)
        self.assertIn('"key": "value"', json_str)

    def test_validate(self):
        valid_toml = 'key = "value"'
        self.assertTrue(self.manager.validate(valid_toml))

        invalid_toml = 'key = "value" no_newline_key = 1'
        self.assertFalse(self.manager.validate(invalid_toml))

    def test_dump_toml(self):
        data = tomlkit.document()
        data.add("key", "value")
        toml_str = self.manager.dump_toml(data)
        self.assertIn('key = "value"', toml_str)

    def test_preserves_comments(self):
        toml_with_comment = """
# This is a comment
key = "value" # Inline comment
"""
        data = self.manager.load_toml(toml_with_comment)
        self.manager.set(data, "key", "new_value")
        dumped = self.manager.dump_toml(data)

        self.assertIn("# This is a comment", dumped)
        self.assertIn("# Inline comment", dumped)
        self.assertIn('key = "new_value"', dumped)

class TestTomlLabCLI(unittest.TestCase):
    @unittest.mock.patch('sys.exit', side_effect=SystemExit)
    def test_tui_action(self, mock_exit):
        from shared.toml_lab import run_toml_lab_logic
        import argparse
        import sys
        from pathlib import Path

        # We must properly patch the exact path being imported locally in the function
        # The function does `from shared.tui import AgentTUI`

        mock_agent_tui = unittest.mock.MagicMock()
        mock_app = unittest.mock.MagicMock()
        mock_agent_tui.return_value = mock_app

        args = argparse.Namespace(action="tui", input=None)

        # Create a mock module for shared.tui to avoid actually importing it
        mock_shared_tui = unittest.mock.MagicMock()
        mock_shared_tui.AgentTUI = mock_agent_tui

        with unittest.mock.patch.dict('sys.modules', {'shared.tui': mock_shared_tui}):
            with self.assertRaises(SystemExit):
                run_toml_lab_logic(args)

        mock_agent_tui.assert_called_once_with(project_dir=Path("."), start_tab="tab-toml")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_with(0)

if __name__ == '__main__':
    unittest.main()

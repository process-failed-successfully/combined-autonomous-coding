import unittest
from pathlib import Path
import tempfile
import json
import shutil

from shared.ide_config import IdeConfigManager


class TestIdeConfigManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)
        self.manager = IdeConfigManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_detect_project_type_python(self):
        (self.project_dir / "requirements.txt").touch()
        self.assertEqual(self.manager.detect_project_type(), "python")

        (self.project_dir / "requirements.txt").unlink()
        (self.project_dir / "pyproject.toml").touch()
        self.assertEqual(self.manager.detect_project_type(), "python")

    def test_detect_project_type_node(self):
        (self.project_dir / "package.json").touch()
        self.assertEqual(self.manager.detect_project_type(), "node")

    def test_detect_project_type_go(self):
        (self.project_dir / "go.mod").touch()
        self.assertEqual(self.manager.detect_project_type(), "go")

    def test_detect_project_type_unknown(self):
        self.assertEqual(self.manager.detect_project_type(), "unknown")

    def test_generate_vscode_config_python(self):
        # Setup Python project
        (self.project_dir / "requirements.txt").touch()
        (self.project_dir / "app.py").touch()
        (self.project_dir / ".venv").mkdir()

        success = self.manager.generate_vscode_config()
        self.assertTrue(success)

        vscode_dir = self.project_dir / ".vscode"
        self.assertTrue(vscode_dir.exists())
        self.assertTrue((vscode_dir / "settings.json").exists())
        self.assertTrue((vscode_dir / "launch.json").exists())
        self.assertTrue((vscode_dir / "extensions.json").exists())

        # Check settings
        with open(vscode_dir / "settings.json") as f:
            settings = json.load(f)
            self.assertEqual(settings.get("python.defaultInterpreterPath"), "${workspaceFolder}/.venv/bin/python")
            self.assertTrue(settings.get("python.linting.enabled"))

        # Check launch
        with open(vscode_dir / "launch.json") as f:
            launch = json.load(f)
            configs = launch.get("configurations", [])
            self.assertTrue(any(c["name"] == "Python: Run app.py" for c in configs))

    def test_generate_vscode_config_dry_run(self):
        (self.project_dir / "package.json").touch()

        # dry_run=True
        success = self.manager.generate_vscode_config(dry_run=True)
        self.assertTrue(success)

        # Should not exist
        self.assertFalse((self.project_dir / ".vscode").exists())

    def test_generate_vscode_config_no_overwrite(self):
        (self.project_dir / "package.json").touch()
        vscode_dir = self.project_dir / ".vscode"
        vscode_dir.mkdir()
        settings_path = vscode_dir / "settings.json"

        # Create existing file
        original_content = {"test": "value"}
        with open(settings_path, "w") as f:
            json.dump(original_content, f)

        # Run without force
        self.manager.generate_vscode_config(force=False)

        # Content should be unchanged
        with open(settings_path) as f:
            content = json.load(f)
            self.assertEqual(content, original_content)

    def test_generate_vscode_config_force_overwrite(self):
        (self.project_dir / "package.json").touch()
        vscode_dir = self.project_dir / ".vscode"
        vscode_dir.mkdir()
        settings_path = vscode_dir / "settings.json"

        # Create existing file
        original_content = {"test": "value"}
        with open(settings_path, "w") as f:
            json.dump(original_content, f)

        # Run with force
        self.manager.generate_vscode_config(force=True)

        # Content should be updated (checking for node specific setting)
        with open(settings_path) as f:
            content = json.load(f)
            self.assertNotEqual(content, original_content)
            self.assertIn("editor.defaultFormatter", content)

    def test_get_config_previews(self):
        (self.project_dir / "requirements.txt").touch()

        previews = self.manager.get_config_previews()
        self.assertIsInstance(previews, dict)
        self.assertIn("settings.json", previews)
        self.assertIn("launch.json", previews)
        self.assertIn("extensions.json", previews)

        self.assertIn("python.linting.enabled", previews["settings.json"])


if __name__ == '__main__':
    unittest.main()

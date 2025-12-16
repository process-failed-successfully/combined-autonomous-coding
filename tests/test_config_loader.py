import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import yaml

from shared.config_loader import (
    get_config_path,
    load_config_from_file,
    ensure_config_exists
)


class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.test_dir = Path(self.temp_dir.name)

    def test_get_config_path_local(self):
        # Create local config
        local_config = Path("agent_config.yaml")
        local_config.touch()
        try:
            path = get_config_path()
            self.assertEqual(path, local_config)
        finally:
            local_config.unlink()

    @patch("platformdirs.user_config_dir")
    def test_get_config_path_xdg(self, mock_user_config):
        # Mock XDG path
        xdg_dir = self.test_dir / "xdg_config"
        xdg_dir.mkdir()
        xdg_config = xdg_dir / "agent_config.yaml"
        xdg_config.touch()

        mock_user_config.return_value = str(xdg_dir)

        # Ensure no local config
        local_config = Path("agent_config.yaml")
        if local_config.exists():
            local_config.unlink()

        path = get_config_path()
        self.assertEqual(path, xdg_config)

    def test_load_config_from_file_valid(self):
        config_file = self.test_dir / "config.yaml"
        data = {"test_key": "test_value"}
        with open(config_file, "w") as f:
            yaml.dump(data, f)

        config = load_config_from_file(config_file)
        self.assertEqual(config["test_key"], "test_value")

    def test_load_config_from_file_missing(self):
        config = load_config_from_file(Path("non_existent.yaml"))
        self.assertEqual(config, {})

    @patch("shared.config_loader.get_config_path")
    @patch("platformdirs.user_config_dir")
    def test_ensure_config_exists_creates_default(self, mock_user_config, mock_get_path):
        # Simulate no config found
        mock_get_path.return_value = None

        xdg_dir = self.test_dir / "xdg_config"
        xdg_dir.mkdir()
        mock_user_config.return_value = str(xdg_dir)

        ensure_config_exists()

        expected_path = xdg_dir / "agent_config.yaml"
        self.assertTrue(expected_path.exists())

        # Verify content
        with open(expected_path) as f:
            content = f.read()
            self.assertIn("notification_settings:", content)


if __name__ == "__main__":
    unittest.main()

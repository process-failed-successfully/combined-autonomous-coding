import unittest
from pathlib import Path
import tempfile
import yaml
import os
from unittest.mock import patch, MagicMock
from shared.config_loader import load_config_from_file

class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "agent_config.yaml"

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("shared.config_loader.user_config_dir")
    @patch("pathlib.Path.home")
    def test_get_config_path_priority(self, mock_home, mock_user_config_dir):
        """Test XDG path resolution priority."""
        
        # Setup paths
        mock_home.return_value = Path(self.temp_dir.name)
        mock_user_config_dir.return_value = str(Path(self.temp_dir.name) / ".config" / "combined-autonomous-coding")
        
        # 1. Local path exists
        local_config = Path("agent_config.yaml")
        with open(local_config, "w") as f:
            f.write("local: true")
            
        try:
            # Should find local
            from shared.config_loader import get_config_path
            path = get_config_path()
            self.assertEqual(path, local_config)
            
            # 2. Remove local, mock XDG
            local_config.unlink()
            
            xdg_dir = Path(mock_user_config_dir.return_value)
            xdg_dir.mkdir(parents=True, exist_ok=True)
            xdg_config = xdg_dir / "agent_config.yaml"
            with open(xdg_config, "w") as f:
                f.write("xdg: true")
                
            path = get_config_path()
            self.assertEqual(path, xdg_config)
            
            # 3. Remove XDG, mock Legacy
            xdg_config.unlink()
            
            legacy_dir = mock_home.return_value / ".gemini"
            legacy_dir.mkdir(parents=True, exist_ok=True)
            legacy_config = legacy_dir / "agent_config.yaml"
            with open(legacy_config, "w") as f:
                f.write("legacy: true")
                
            path = get_config_path()
            self.assertEqual(path, legacy_config)
            
            # 4. Remove Legacy, return None
            legacy_config.unlink()
            path = get_config_path()
            self.assertIsNone(path)

        finally:
            if local_config.exists():
                local_config.unlink()

    @patch("shared.config_loader.create_default_config")
    @patch("shared.config_loader.get_config_path")
    @patch("shared.config_loader.user_config_dir")
    def test_ensure_config_exists_creates_if_none(self, mock_user_dirs, mock_get_path, mock_create):
        """Test that default config is created if no config exists."""
        # Setup: No existing config
        mock_get_path.return_value = None
        mock_user_dirs.return_value = "/tmp/fake_xdg"
        
        from shared.config_loader import ensure_config_exists
        ensure_config_exists()
        
        # Should have called create with path constructed from user config dir
        mock_create.assert_called_once()
        expected_path = Path("/tmp/fake_xdg/agent_config.yaml")
        mock_create.assert_called_with(expected_path)

    @patch("shared.config_loader.create_default_config")
    @patch("shared.config_loader.get_config_path")
    def test_ensure_config_exists_noop_if_exists(self, mock_get_path, mock_create):
        """Test that no action is taken if config already exists."""
        # Setup: Existing config
        mock_get_path.return_value = Path("/some/path.yaml")
        
        from shared.config_loader import ensure_config_exists
        ensure_config_exists()
        
        mock_create.assert_not_called()

    def test_load_valid_config(self):
        """Test loading a valid YAML configuration file."""
        config_data = {
            "slack_webhook_url": "https://hooks.slack.com/test",
            "manager_frequency": 5,
            "notification_settings": {
                "manager": True,
                "iteration": False
            }
        }
        with open(self.config_path, "w") as f:
            yaml.dump(config_data, f)

        loaded_config = load_config_from_file(self.config_path)
        self.assertEqual(loaded_config["slack_webhook_url"], "https://hooks.slack.com/test")
        self.assertEqual(loaded_config["manager_frequency"], 5)
        self.assertEqual(loaded_config["notification_settings"]["manager"], True)

    def test_load_non_existent_file(self):
        """Test loading a file that doesn't exist."""
        loaded_config = load_config_from_file(Path("/non/existent/path.yaml"))
        self.assertEqual(loaded_config, {})

    def test_load_invalid_yaml(self):
        """Test loading an invalid YAML file."""
        with open(self.config_path, "w") as f:
            f.write("invalid: yaml: content: [")

        # Keeping it simple, should catch exception and return empty or partial
        # Based on implementation, it logs error and returns {}
        loaded_config = load_config_from_file(self.config_path)
        self.assertEqual(loaded_config, {})

if __name__ == "__main__":
    unittest.main()

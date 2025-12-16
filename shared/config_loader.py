import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import platformdirs

logger = logging.getLogger(__name__)


def get_config_path() -> Optional[Path]:
    """
    Resolve configuration file path with priority:
    1. Current Directory: ./agent_config.yaml
    2. XDG Config Home: ~/.config/combined-autonomous-coding/agent_config.yaml
    3. Legacy Config: ~/.gemini/agent_config.yaml

    Returns:
        Path object if a config file is found, else None.
    """
    # 1. Current Directory
    local_config = Path("agent_config.yaml")
    if local_config.exists():
        logger.debug(f"Found config in current directory: {local_config.absolute()}")
        return local_config

    # 2. XDG Config Home
    # App Name: combined-autonomous-coding
    xdg_config_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding"))
    xdg_config = xdg_config_dir / "agent_config.yaml"
    if xdg_config.exists():
        logger.debug(f"Found config in XDG path: {xdg_config}")
        return xdg_config

    # 3. Legacy Fallback
    legacy_config = Path.home() / ".gemini" / "agent_config.yaml"
    if legacy_config.exists():
        logger.warning(f"Found legacy config at {legacy_config}. Please move to {xdg_config}.")
        return legacy_config

    return None


def create_default_config(path: Path) -> None:
    """Create a default configuration file with comments."""
    path.parent.mkdir(parents=True, exist_ok=True)

    default_content = """# Combined Autonomous Coding Agent Configuration
# ============================================

# --- Webhook URLs ---
# Uncomment and set these to receive notifications
# slack_webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK"
# discord_webhook_url: "https://discord.com/api/webhooks/YOUR/WEBHOOK"

# --- Notification Preferences ---
# Enable or disable notifications for specific events
notification_settings:
  iteration: false          # Summary of every iteration (can be noisy)
  manager: true             # Manager agent updates (Highly Recommended)
  human_in_loop: true       # When human intervention is requested (Highly Recommended)
  project_completion: true  # When the project is signed off (Recommended)
  error: true               # On agent errors or crashes

# --- Agent Settings ---
# login_mode: false         # Set to true to run in login/auth mode
# sprint_mode: false        # Set to true to enable Sprint mode
    """

    try:
        path.write_text(default_content)
        logger.info(f"Created default configuration at {path}")
    except Exception as e:
        logger.error(f"Failed to create default config at {path}: {e}")


def ensure_config_exists() -> None:
    """
    Ensure a configuration file exists.
    If no config is found in Local, XDG, or Legacy locations,
    create a default one in the XDG Config Home.
    """
    current_config = get_config_path()
    if current_config:
        return

    # No config found, create one in XDG path
    xdg_config_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding"))
    target_path = xdg_config_dir / "agent_config.yaml"

    logger.info("No configuration found. Creating default at XDG location.")

    create_default_config(target_path)


def load_config_from_file(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Specific path to load. If None, resolves using get_config_path().

    Returns:
        Dict containing configuration values, or empty dict if file not found/error.
    """
    if config_path is None:
        config_path = get_config_path()

    if not config_path or not config_path.exists():
        logger.debug("No configuration file found.")
        return {}

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            if not config:
                return {}
            logger.info(f"Loaded configuration from {config_path}")
            return config
    except Exception as e:
        logger.error(f"Error loading config file {config_path}: {e}")
        return {}

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple, Any, Callable, Dict
try:
    import platformdirs
except ImportError:
    platformdirs = None

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.plugins: Dict[str, Any] = {}
        self.loaded = False

    def load_plugins(self) -> None:
        """Loads plugins from configured directories."""
        if self.loaded:
            return

        plugin_dirs = []

        # 1. Bundled plugins (repo_root/plugins)
        # Assuming shared/plugin_manager.py -> repo_root/shared/plugin_manager.py
        repo_root = Path(__file__).parent.parent
        plugin_dirs.append(repo_root / "plugins")

        # 2. User plugins (XDG)
        if platformdirs:
            user_plugin_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding")) / "plugins"
            plugin_dirs.append(user_plugin_dir)

        # 3. Project plugins
        plugin_dirs.append(self.project_dir / ".agent_plugins")

        for p_dir in plugin_dirs:
            if not p_dir.exists():
                continue

            logger.debug(f"Scanning for plugins in: {p_dir}")
            try:
                for item in p_dir.iterdir():
                    if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
                        self._load_plugin(item)
            except OSError as e:
                logger.error(f"Error reading plugin directory {p_dir}: {e}")

        self.loaded = True

    def _load_plugin(self, path: Path) -> None:
        # Use a unique module name to avoid conflicts
        module_name = f"agent_plugin_{path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                self.plugins[path.stem] = module
                logger.info(f"Loaded plugin: {path.stem}")
        except Exception as e:
            logger.error(f"Failed to load plugin {path}: {e}")

    def register_cli(self, subparsers) -> None:
        """Calls register_cli(subparsers) on all loaded plugins."""
        for name, module in self.plugins.items():
            if hasattr(module, "register_cli"):
                try:
                    module.register_cli(subparsers)
                    logger.debug(f"Registered CLI commands for {name}")
                except Exception as e:
                    logger.error(f"Error registering CLI for {name}: {e}")

    def get_tui_tabs(self) -> List[Tuple[str, Any]]:
        """Collects TUI tabs from plugins."""
        tabs = []
        for name, module in self.plugins.items():
            if hasattr(module, "register_tui"):
                try:
                    # register_tui should return a list of (title, widget_instance) or just one
                    result = module.register_tui()
                    if isinstance(result, list):
                        tabs.extend(result)
                    elif isinstance(result, tuple):
                        tabs.append(result)
                except Exception as e:
                    logger.error(f"Error getting TUI tabs for {name}: {e}")
        return tabs

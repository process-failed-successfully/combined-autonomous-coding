import importlib.util
import sys
import os
import shutil
import inspect
from pathlib import Path
from typing import List, Tuple, Any, Dict, Optional
import requests

class PluginManager:
    """
    Manages the discovery, loading, and registration of plugins.
    Plugins are Python modules that can define:
    - register_cli(subparsers): To add CLI commands.
    - register_tui() -> (Title, Widget): To add TUI tabs.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.plugins: Dict[str, Any] = {}
        self.plugin_paths: List[Path] = []

    def discover_plugins(self) -> None:
        """
        Scans for plugins in:
        1. Repo 'plugins/' directory (bundled)
        2. User config directory '~/.config/combined-autonomous-coding/plugins/'
        3. Project '.agent_plugins/' directory
        """
        # 1. Bundled Plugins
        repo_root = Path(__file__).parent.parent
        bundled_plugins = repo_root / "plugins"
        if bundled_plugins.exists():
            self._scan_dir(bundled_plugins)

        # 2. User Config Plugins
        try:
            import platformdirs
            user_config_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding")) / "plugins"
            if user_config_dir.exists():
                self._scan_dir(user_config_dir)
        except ImportError:
            pass # platformdirs might not be installed, skip

        # 3. Project Local Plugins
        local_plugins = self.project_dir / ".agent_plugins"
        if local_plugins.exists():
            self._scan_dir(local_plugins)

    def _scan_dir(self, directory: Path) -> None:
        """Helper to scan a directory for .py files."""
        for file in directory.glob("*.py"):
            if file.name.startswith("__"):
                continue
            if file not in self.plugin_paths:
                self.plugin_paths.append(file)

    def load_plugins(self) -> None:
        """Imports discovered plugin modules."""
        for path in self.plugin_paths:
            module_name = f"plugin_{path.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    self.plugins[path.stem] = module
            except Exception as e:
                print(f"❌ Error loading plugin {path.name}: {e}", file=sys.stderr)

    def register_cli(self, subparsers) -> None:
        """Calls register_cli on all loaded plugins."""
        for name, module in self.plugins.items():
            if hasattr(module, "register_cli"):
                try:
                    module.register_cli(subparsers)
                except Exception as e:
                    print(f"❌ Error registering CLI for plugin {name}: {e}", file=sys.stderr)

    def get_tui_tabs(self) -> List[Tuple[str, Any]]:
        """Returns a list of (Title, WidgetInstance) from plugins."""
        tabs = []
        for name, module in self.plugins.items():
            if hasattr(module, "register_tui"):
                try:
                    result = module.register_tui()
                    if result:
                        if isinstance(result, list):
                            tabs.extend(result)
                        else:
                            tabs.append(result)
                except Exception as e:
                    print(f"❌ Error registering TUI for plugin {name}: {e}", file=sys.stderr)
        return tabs

    def install_plugin(self, source: str) -> bool:
        """Installs a plugin from a URL or local path to .agent_plugins/."""
        target_dir = self.project_dir / ".agent_plugins"
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            if source.startswith("http"):
                # URL
                response = requests.get(source)
                response.raise_for_status()
                filename = source.split("/")[-1]
                if not filename.endswith(".py"):
                    filename = "downloaded_plugin.py"

                target_path = target_dir / filename
                target_path.write_text(response.text)
                print(f"✅ Plugin installed to {target_path}")
            else:
                # Local Path
                src_path = Path(source)
                if not src_path.exists():
                    print(f"❌ Source not found: {source}")
                    return False

                shutil.copy(src_path, target_dir)
                print(f"✅ Plugin copied to {target_dir}")

            return True
        except Exception as e:
            print(f"❌ Error installing plugin: {e}")
            return False

    def create_plugin(self, name: str) -> Path:
        """Creates a scaffold plugin file."""
        target_dir = self.project_dir / ".agent_plugins"
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{name}.py" if not name.endswith(".py") else name
        target_path = target_dir / filename

        content = """
import argparse
from textual.widgets import Label

def register_cli(subparsers):
    \"\"\"Registers a CLI command.\"\"\"
    parser = subparsers.add_parser("my-command", help="My custom plugin command")
    parser.set_defaults(func=run_my_command)

def run_my_command(args):
    print("Hello from my custom plugin!")

def register_tui():
    \"\"\"Registers a TUI tab. Returns (Title, WidgetInstance).\"\"\"
    return ("My Tab", Label("Hello from Plugin TUI!"))
"""
        target_path.write_text(content.strip())
        return target_path

    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())

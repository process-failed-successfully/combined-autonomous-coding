import yaml
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from shared.config_loader import get_config_path
import platformdirs

console = Console()

CONFIG_KEYS: Dict[str, Dict[str, Any]] = {
    "agent_type": {"description": "Agent backend to use (gemini, cursor, local, openrouter)", "default": "gemini"},
    "model": {"description": "Model to use (e.g., gemini-2.0-flash-exp)", "default": "auto"},
    "max_iterations": {"description": "Maximum number of iterations", "default": 50},
    "timeout": {"description": "Timeout in seconds", "default": 600.0},
    "auto_continue_delay": {"description": "Delay before auto-continue", "default": 3},
    "verbose": {"description": "Enable verbose logging", "default": False},
    "stream_output": {"description": "Stream LLM output to console", "default": True},
    "slack_webhook_url": {"description": "Slack Webhook URL", "default": None},
    "discord_webhook_url": {"description": "Discord Webhook URL", "default": None},
    "login_mode": {"description": "Enable login/auth mode", "default": False},
    "sprint_mode": {"description": "Enable sprint mode", "default": False},
}

KNOWN_MODELS = {
    "gemini": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
    "cursor": ["gpt-4o", "claude-3-5-sonnet", "o1-mini"],
    "local": ["Qwen2.5-Coder-14B-Instruct", "llama3.2"],
    "openrouter": ["deepseek/deepseek-v3.2"]
}


class ConfigManager:
    def __init__(self):
        self.config_path = get_config_path()
        if not self.config_path:
            # Default to XDG if not found
            xdg_config_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding"))
            self.config_path = xdg_config_dir / "agent_config.yaml"

    def _load_config(self) -> Dict[str, Any]:
        assert self.config_path is not None
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _save_config(self, config: Dict[str, Any]):
        assert self.config_path is not None
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    def list_keys(self):
        """Display a table of available configuration keys."""
        table = Table(title="Configuration Keys")
        table.add_column("Key", style="cyan")
        table.add_column("Description", style="magenta")
        table.add_column("Default", style="green")
        table.add_column("Current Value", style="yellow")

        current_config = self._load_config()

        for key, info in CONFIG_KEYS.items():
            current_val = current_config.get(key, "Not Set")
            table.add_row(key, info["description"], str(info["default"]), str(current_val))

        console.print(table)
        console.print(f"\n[dim]Config file: {self.config_path}[/dim]")

    def set_value(self, key: str, value: str):
        """Set a configuration value."""
        if key not in CONFIG_KEYS:
            console.print(f"[red]Error: Unknown key '{key}'.[/red]")
            matches = difflib.get_close_matches(key, CONFIG_KEYS.keys(), n=1, cutoff=0.6)
            if matches:
                console.print(f"[yellow]Did you mean '{matches[0]}'? [/yellow]")
            else:
                self.list_keys()
            return

        # Special Validation for 'agent_type'
        if key == "agent_type":
            if value not in KNOWN_MODELS:
                console.print(f"[red]Error: Invalid agent_type '{value}'. Must be one of: {', '.join(KNOWN_MODELS.keys())}[/red]")
                return

        # Special Validation for 'model'
        if key == "model" and value != "auto":
            # Check against all known models, or specific to current agent if set?
            # For simplicity, check if it exists in any list
            all_models = []
            for m_list in KNOWN_MODELS.values():
                all_models.extend(m_list)

            if value not in all_models:
                console.print(f"[yellow]Warning: Model '{value}' is not in the known list. Setting anyway.[/yellow]")
                matches = difflib.get_close_matches(value, all_models, n=1, cutoff=0.6)
                if matches:
                    console.print(f"[dim]Did you mean '{matches[0]}'? [/dim]")

        config = self._load_config()

        # Type conversion
        info = CONFIG_KEYS[key]
        default = info["default"]
        val: Any
        try:
            if isinstance(default, bool):
                if value.lower() in ("true", "yes", "1"):
                    val = True
                elif value.lower() in ("false", "no", "0"):
                    val = False
                else:
                    raise ValueError("Must be boolean")
            elif isinstance(default, int):
                val = int(value)
            elif isinstance(default, float):
                val = float(value)
            else:
                val = value
        except ValueError:
            console.print(f"[red]Error: Invalid value for {key}. Expected type matching default.[/red]")
            return

        config[key] = val
        self._save_config(config)
        console.print(f"[green]Set '{key}' to '{val}'[/green]")

    def list_models(self, agent_type: Optional[str] = None):
        """List available models."""
        table = Table(title="Available Models")
        table.add_column("Agent", style="cyan")
        table.add_column("Model", style="magenta")

        if agent_type:
            target_agents: List[str] = [agent_type]
        else:
            target_agents = list(KNOWN_MODELS.keys())

        for agent in target_agents:
            for model in KNOWN_MODELS.get(agent, []):
                table.add_row(agent, model)

        console.print(table)

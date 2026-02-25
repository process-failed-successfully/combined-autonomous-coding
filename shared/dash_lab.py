import yaml
import asyncio
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class WidgetConfig:
    type: str  # "metric", "log", "chart"
    title: str
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    source: str = "command"  # "command", "file"
    command: str = ""
    file_path: str = ""
    refresh_interval: int = 5  # seconds

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DashboardConfig:
    title: str = "My Dashboard"
    widgets: List[WidgetConfig] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "widgets": [w.to_dict() for w in self.widgets]
        }


class DashLabManager:
    """Manages dashboard configuration and data execution."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config_path = self.project_dir / "dashboard.yaml"

    def load_config(self) -> DashboardConfig:
        if not self.config_path.exists():
            return self.create_default_config()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            title = data.get("title", "My Dashboard")
            widgets_data = data.get("widgets", [])
            widgets = []
            for w in widgets_data:
                widgets.append(WidgetConfig(**w))

            return DashboardConfig(title=title, widgets=widgets)
        except Exception as e:
            print(f"Error loading dashboard config: {e}")
            return self.create_default_config()

    def create_default_config(self) -> DashboardConfig:
        # Example default dashboard
        return DashboardConfig(
            title="Default Dashboard",
            widgets=[
                WidgetConfig(
                    type="metric",
                    title="File Count",
                    command="ls -1 | wc -l",
                    row=0, col=0
                ),
                WidgetConfig(
                    type="metric",
                    title="Disk Usage",
                    command="df -h . | tail -1 | awk '{print $5}'",
                    row=0, col=1
                )
            ]
        )

    def save_config(self, config: DashboardConfig) -> None:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config.to_dict(), f, sort_keys=False, indent=2)
        except Exception as e:
            print(f"Error saving dashboard config: {e}")

    async def execute_source(self, widget: WidgetConfig) -> str:
        """Executes the data source for a widget."""
        if widget.source == "command":
            if not widget.command:
                return "No command"
            return await self._run_command(widget.command)
        elif widget.source == "file":
            if not widget.file_path:
                return "No file path"
            return await self._read_file(widget.file_path)
        return "Unknown source"

    async def _run_command(self, cmd: str) -> str:
        try:
            # Run asynchronously
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_dir
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                return f"Error: {stderr.decode().strip()}"
            return stdout.decode().strip()
        except Exception as e:
            return f"Exec Error: {e}"

    async def _read_file(self, path_str: str) -> str:
        try:
            # Handle relative paths
            path = Path(path_str)
            if not path.is_absolute():
                path = self.project_dir / path

            if not path.exists():
                return "File not found"

            # Read last few lines for "log" type, or content for "metric"
            # For simplicity, just read content (truncated if too large)
            content = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="replace")
            return content
        except Exception as e:
            return f"Read Error: {e}"

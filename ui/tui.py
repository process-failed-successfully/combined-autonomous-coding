"""
Text User Interface (TUI) for the Autonomous Agent
=================================================

A Textual-based UI to display logs and agent status.
"""

import asyncio
import logging
from typing import Callable, Any, Dict

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, Label, Static, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual.logging import TextualHandler
from textual.binding import Binding

from shared.agent_client import AgentClient
from shared.config import Config


class AgentStatus(Static):
    """Widget to display key agent metrics."""

    def compose(self) -> ComposeResult:
        yield Label("Status: Idle", id="status_label")
        yield DataTable(id="metrics_table")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Metric", "Value")
        table.add_rows([
            ("Iteration", "0"),
            ("Tokens", "0"),
            ("Cost", "$0.00"),
            ("Task", "Initializing..."),
        ])

    def update_metrics(self, data: Dict[str, Any]):
        table = self.query_one(DataTable)

        # Helper to update or add row
        def update_row(key, value):
            # Scan for key
            row_key = None
            for i in range(table.row_count):
                if table.get_cell_at((i, 0)) == key:
                    table.update_cell_at((i, 1), str(value))
                    return
            # If not found (shouldn't happen with fixed rows)
            table.add_row(key, str(value))

        if "iteration" in data:
            update_row("Iteration", data["iteration"])

        if "stats" in data:
            stats = data["stats"]
            if "total_tokens" in stats:
                update_row("Tokens", stats["total_tokens"])
            if "total_cost" in stats:
                update_row("Cost", f"${stats['total_cost']:.4f}")

        if "current_step" in data:
            update_row("Task", data["current_step"])

        status_label = self.query_one("#status_label", Label)
        # Maybe color code status
        status_label.update(f"Status: Active")


class TextualLogHandler(logging.Handler):
    """Logging handler that writes to a Textual Log widget."""

    def __init__(self, log_widget: Log):
        super().__init__()
        self.log_widget = log_widget
        self.formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")

    def emit(self, record):
        msg = self.format(record)
        self.log_widget.write_line(msg)


class AgentTui(App):
    """The main TUI Application."""

    CSS = """
    AgentStatus {
        dock: right;
        width: 40;
        height: 100%;
        border-left: solid green;
        background: $surface;
        padding: 1;
    }

    #metrics_table {
        height: auto;
        margin-top: 1;
    }

    Log {
        height: 100%;
        border: solid $accent;
        background: $surface;
    }

    Header {
        dock: top;
        height: 1;
        background: $primary;
        color: white;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self, config: Config, client: AgentClient, runner: Callable, logger: logging.Logger):
        super().__init__()
        self.config = config
        self.client = client
        self.runner = runner
        self.logger = logger
        self.title = f"Agent TUI - {config.agent_id}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Log(id="log_view", highlight=True),
            AgentStatus(id="status_panel"),
        )
        yield Footer()

    def on_mount(self) -> None:
        # Setup Logging
        log_view = self.query_one("#log_view", Log)
        handler = TextualLogHandler(log_view)
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)

        # Setup Status Updates
        self.client.add_state_listener(self.on_state_update)

        # Start Agent in Background
        self.run_worker(self.run_agent(), name="agent_runner", exit_on_error=False)

    def on_state_update(self, data: Dict[str, Any]):
        """Callback from AgentClient."""
        # This might come from a different thread, so use call_from_thread
        self.call_from_thread(self._update_ui, data)

    def _update_ui(self, data: Dict[str, Any]):
        try:
            status_panel = self.query_one(AgentStatus)
            status_panel.update_metrics(data)
        except Exception:
            pass

    async def run_agent(self):
        try:
            self.logger.info("Starting Agent Runner...")
            await self.runner
            self.logger.info("Agent execution completed.")
        except Exception as e:
            self.logger.exception(f"Agent crashed: {e}")
            self.notify(f"Agent Error: {e}", severity="error")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

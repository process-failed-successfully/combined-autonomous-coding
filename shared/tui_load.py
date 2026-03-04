from textual.app import ComposeResult
from textual.widgets import TabPane, Label, Input, Button, Static, DataTable
from textual.containers import Vertical, Horizontal
from textual import work
from typing import Dict, Any, List

from shared.load_lab import LoadLabManager
import sys

class LoadLabTab(TabPane):
    """A tab for running HTTP load tests."""

    def __init__(self, project_dir):
        super().__init__("Load Lab", id="tab-load")
        self.project_dir = project_dir
        # Only instantiate manager if we actually have it.
        # This prevents breaking the entire AgentTUI if aiohttp is missing.
        try:
            self.manager = LoadLabManager()
        except SystemExit:
            self.manager = None

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-2"):
            yield Label("HTTP Load Testing", classes="text-xl text-bold mb-2")

            if not self.manager:
                yield Label("Error: aiohttp is required. Run 'pip install aiohttp'", classes="text-red")
            else:
                with Horizontal(classes="mb-2 h-auto"):
                    u = Input(placeholder="URL (e.g. http://localhost:8080)", id="url-input")
                    u.styles.width = "50%"
                    yield u

                    m = Input(placeholder="Method", value="GET", id="method-input")
                    m.styles.width = "25%"
                    yield m

                with Horizontal(classes="mb-2 h-auto"):
                    ui = Input(placeholder="Users (Concurrency)", value="10", id="users-input")
                    ui.styles.width = "25%"
                    yield ui

                    di = Input(placeholder="Duration (Seconds)", value="5", id="duration-input")
                    di.styles.width = "25%"
                    yield di

                    yield Button("Start Load Test", id="start-btn", variant="primary", classes="ml-2")

                yield Label("Results:", classes="text-bold mt-4")
                yield DataTable(id="results-table")

                yield Static(id="status-area", classes="mt-2 text-italic")

    def on_mount(self):
        if self.manager:
            table = self.query_one("#results-table", DataTable)
            table.add_columns("Metric", "Value")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "start-btn" and self.manager:
            url = self.query_one("#url-input", Input).value
            if not url:
                self.query_one("#status-area", Static).update("Error: URL is required")
                return

            method = self.query_one("#method-input", Input).value or "GET"
            users = int(self.query_one("#users-input", Input).value or "10")
            duration = int(self.query_one("#duration-input", Input).value or "5")

            self.query_one("#status-area", Static).update("Running test...")
            event.button.disabled = True

            self.run_test_worker(url, method, users, duration)

    @work(exclusive=True, thread=True)
    def run_test_worker(self, url: str, method: str, users: int, duration: int):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.manager.run_load_test(url=url, users=users, duration=duration, method=method))
            self.app.call_from_thread(self.update_results, results)
        except Exception as e:
            self.app.call_from_thread(self.show_error, str(e))
        finally:
            loop.close()

    def update_results(self, results: Dict[str, Any]):
        try:
            table = self.query_one("#results-table", DataTable)
            table.clear()

            table.add_row("Total Requests", str(results.get("total_requests", 0)))
            table.add_row("Duration (s)", f"{results.get('duration', 0):.2f}")
            table.add_row("Requests / Sec", f"{results.get('rps', 0):.2f}")
            table.add_row("Successful", str(results.get("success_count", 0)))
            table.add_row("Errors", str(results.get("error_count", 0)))

            latency = results.get("latency", {})
            if latency:
                table.add_row("Min Latency (s)", f"{latency.get('min', 0):.4f}")
                table.add_row("Max Latency (s)", f"{latency.get('max', 0):.4f}")
                table.add_row("Avg Latency (s)", f"{latency.get('avg', 0):.4f}")
                table.add_row("p95 Latency (s)", f"{latency.get('p95', 0):.4f}")
                table.add_row("p99 Latency (s)", f"{latency.get('p99', 0):.4f}")

            self.query_one("#status-area", Static).update("Test Complete!")
            self.query_one("#start-btn", Button).disabled = False
        except Exception:
            pass

    def show_error(self, message: str):
        try:
            self.query_one("#status-area", Static).update(f"Error: {message}")
            self.query_one("#start-btn", Button).disabled = False
        except Exception:
            pass

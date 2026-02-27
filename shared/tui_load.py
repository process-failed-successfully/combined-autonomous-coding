from textual.app import ComposeResult
from textual.widgets import Label, Input, Button, DataTable, Select, RichLog
from textual.containers import Container, Vertical, Horizontal
from textual import on
import asyncio
from shared.load_lab import LoadLabManager
from shared.charts import draw_ascii_bar_chart

class LoadLabTab(Container):
    """Tab for running HTTP load tests."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = LoadLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Load Lab[/bold]", classes="welcome-text")

            # Configuration
            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Target URL:")
                    yield Input(placeholder="http://localhost:8080", id="load-url")

                with Vertical():
                    yield Label("Method:")
                    yield Select.from_values(["GET", "POST", "PUT", "DELETE"], id="load-method", value="GET")

                with Vertical():
                    yield Label("Concurrent Users:")
                    yield Input(placeholder="10", id="load-users", type="integer")

                with Vertical():
                    yield Label("Duration (s):")
                    yield Input(placeholder="5", id="load-duration", type="integer")

            yield Button("Run Load Test", id="btn-run-load", variant="primary")

            # Results
            with Horizontal():
                with Vertical(classes="stat-box", id="load-stats-container"):
                    yield Label("[bold]Statistics[/bold]")
                    yield DataTable(id="load-stats-table")

                with Vertical(classes="stat-box", id="load-chart-container"):
                    yield Label("[bold]Latency Distribution[/bold]")
                    yield RichLog(id="load-chart-log", wrap=False, highlight=False)

    def on_mount(self) -> None:
        table = self.query_one("#load-stats-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Metric", "Value")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run-load":
            await self.run_test()

    async def run_test(self) -> None:
        url = self.query_one("#load-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        method = self.query_one("#load-method", Select).value or "GET"

        users_str = self.query_one("#load-users", Input).value
        users = int(users_str) if users_str else 10

        duration_str = self.query_one("#load-duration", Input).value
        duration = int(duration_str) if duration_str else 5

        self.notify(f"Starting load test on {url}...")
        self.query_one("#btn-run-load").disabled = True

        log = self.query_one("#load-chart-log", RichLog)
        log.clear()
        log.write("Running test...")

        try:
            # LoadLabManager.run_load_test is async and uses aiohttp
            # We can await it directly in Textual's event loop
            results = await self.manager.run_load_test(url, users, duration, method)
            self._update_ui(results)
            self.notify("Load test complete.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            log.write(f"[red]Error: {e}[/red]")
        finally:
            self.query_one("#btn-run-load").disabled = False

    def _update_ui(self, results: dict) -> None:
        # Update Table
        table = self.query_one("#load-stats-table", DataTable)
        table.clear()

        table.add_row("Total Requests", str(results["total_requests"]))
        table.add_row("RPS", f"{results['rps']:.2f}")
        table.add_row("Success", str(results["success_count"]))
        table.add_row("Errors", str(results["error_count"]))

        l = results["latency"]
        if l:
            table.add_row("Avg Latency", f"{l['avg']:.4f}s")
            table.add_row("Median", f"{l['median']:.4f}s")
            table.add_row("P95", f"{l['p95']:.4f}s")
            table.add_row("P99", f"{l['p99']:.4f}s")
            table.add_row("Max", f"{l['max']:.4f}s")

        # Update Chart
        log = self.query_one("#load-chart-log", RichLog)
        log.clear()

        if l:
            # Create a simple distribution for the chart
            chart_data = {
                "Min": l["min"],
                "Avg": l["avg"],
                "Median": l["median"],
                "P95": l["p95"],
                "Max": l["max"]
            }
            chart = draw_ascii_bar_chart(chart_data, "Latency (s)")
            log.write(chart)

        # Status Codes
        if results["status_codes"]:
            log.write("\n[bold]Status Codes:[/bold]")
            for code, count in results["status_codes"].items():
                log.write(f"  {code}: {count}")

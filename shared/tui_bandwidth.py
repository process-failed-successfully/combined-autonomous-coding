import time
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, DataTable, Select, Header, Footer
from textual import on
from shared.bandwidth_lab import BandwidthManager, _bytes_to_human

class BandwidthLabTab(Container):
    """Tab for Bandwidth Monitoring."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = BandwidthManager()
        self.monitoring = False
        self.timer = None
        self.prev_counters = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Bandwidth Monitor[/bold]", classes="welcome-text")

            if self.manager.error:
                yield Label(f"[bold red]{self.manager.error}[/bold red]")
                return

            with Horizontal(classes="stat-box"):
                yield Button("Start Monitoring", id="btn-bw-start", variant="primary")
                yield Button("Stop", id="btn-bw-stop", variant="error", disabled=True)
                yield Label("Interval: 1s", classes="label")

            yield DataTable(id="bw-table")

    def on_mount(self) -> None:
        if self.manager.error:
            return

        table = self.query_one("#bw-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Interface", "Upload Speed", "Download Speed", "Total Sent", "Total Recv")
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one("#bw-table", DataTable)

        # If not monitoring, just show totals or empty speeds
        curr_counters = self.manager.get_io_counters()
        if "error" in curr_counters:
            self.notify(f"Error: {curr_counters['error']}", severity="error")
            return

        # If we are monitoring, calculate speeds
        if self.monitoring and self.prev_counters:
            # We update existing rows
            for iface, curr in curr_counters.items():
                prev = self.prev_counters.get(iface)
                if prev:
                    # Calculate speed (assuming ~1s interval)
                    bytes_sent_diff = curr.bytes_sent - prev.bytes_sent
                    bytes_recv_diff = curr.bytes_recv - prev.bytes_recv

                    up_speed = _bytes_to_human(bytes_sent_diff, per_second=True)
                    down_speed = _bytes_to_human(bytes_recv_diff, per_second=True)
                else:
                    up_speed = "0 B/s"
                    down_speed = "0 B/s"

                total_sent = _bytes_to_human(curr.bytes_sent, per_second=False)
                total_recv = _bytes_to_human(curr.bytes_recv, per_second=False)

                # Update row
                if iface in table.rows:
                    table.update_cell(iface, "Upload Speed", up_speed)
                    table.update_cell(iface, "Download Speed", down_speed)
                    table.update_cell(iface, "Total Sent", total_sent)
                    table.update_cell(iface, "Total Recv", total_recv)
                else:
                    table.add_row(iface, up_speed, down_speed, total_sent, total_recv, key=iface)

        elif not self.monitoring:
            # Just show totals, speed 0 or N/A
            table.clear()
            for iface, curr in curr_counters.items():
                total_sent = _bytes_to_human(curr.bytes_sent, per_second=False)
                total_recv = _bytes_to_human(curr.bytes_recv, per_second=False)
                table.add_row(iface, "-", "-", total_sent, total_recv, key=iface)

        self.prev_counters = curr_counters

    @on(Button.Pressed, "#btn-bw-start")
    def on_start(self) -> None:
        self.monitoring = True
        self.query_one("#btn-bw-start").disabled = True
        self.query_one("#btn-bw-stop").disabled = False

        # Reset prev counters so we don't calculate speed against old data
        self.prev_counters = self.manager.get_io_counters()

        # Set timer
        self.timer = self.set_interval(1.0, self.refresh_table)
        self.notify("Monitoring started.")

    @on(Button.Pressed, "#btn-bw-stop")
    def on_stop(self) -> None:
        self.monitoring = False
        self.query_one("#btn-bw-start").disabled = False
        self.query_one("#btn-bw-stop").disabled = True

        if self.timer:
            self.timer.stop()
            self.timer = None

        self.refresh_table() # One last refresh to clear speeds or update totals
        self.notify("Monitoring stopped.")

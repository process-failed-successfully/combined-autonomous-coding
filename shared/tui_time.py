from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Select, DataTable, RichLog, TabbedContent, TabPane, Static
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from datetime import datetime, timezone
import zoneinfo
from shared.time_lab import TimeLabManager

class TimerWidget(Container):
    """A countdown timer and stopwatch widget."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="stat-box"):
            yield Label("[bold]Timer & Stopwatch[/bold]")

            # Display
            yield Label("00:00:00", id="lbl-timer-display", classes="timer-display")

            # Controls
            with Horizontal():
                yield Input(placeholder="Duration (e.g. 5m, 10s)", id="input-timer-duration")
                yield Button("Set", id="btn-timer-set", variant="primary")

            with Horizontal():
                yield Button("Start", id="btn-timer-start", variant="success")
                yield Button("Stop", id="btn-timer-stop", variant="error", disabled=True)
                yield Button("Reset", id="btn-timer-reset", variant="warning")

            with Horizontal():
                yield Button("Pomodoro (25m)", id="btn-timer-pomo", variant="default")
                yield Button("Short Break (5m)", id="btn-timer-short", variant="default")
                yield Button("Stopwatch Mode", id="btn-timer-mode", variant="default")

    def on_mount(self) -> None:
        self.timer_active = False
        self.timer_mode = "countdown" # or "stopwatch"
        self.start_time = 0.0
        self.end_time = 0.0
        self.paused_at = 0.0
        self.duration = 0
        self.remaining = 0

        self.manager = TimeLabManager()
        self.set_interval(0.1, self.update_timer)

    def update_timer(self) -> None:
        if not self.timer_active:
            return

        now = datetime.now(timezone.utc).timestamp()

        if self.timer_mode == "countdown":
            left = self.end_time - now
            if left <= 0:
                self.timer_active = False
                self.query_one("#lbl-timer-display", Label).update("[bold red]00:00:00[/bold red]")
                self.query_one("#btn-timer-start").disabled = False
                self.query_one("#btn-timer-stop").disabled = True
                self.notify("Timer Finished!", severity="warning")
                return

            self.display_time(left)

        elif self.timer_mode == "stopwatch":
            elapsed = now - self.start_time
            self.display_time(elapsed)

    def display_time(self, seconds: float) -> None:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        # Show deciseconds? No, simple seconds is fine.
        text = f"{h:02d}:{m:02d}:{s:02d}"

        if self.timer_mode == "countdown" and seconds < 10:
             text = f"[red]{text}[/red]"

        self.query_one("#lbl-timer-display", Label).update(text)

    @on(Button.Pressed, "#btn-timer-set")
    def on_set(self) -> None:
        val = self.query_one("#input-timer-duration", Input).value
        if not val:
            return

        seconds = self.manager.parse_duration(val)
        if seconds > 0:
            self.duration = seconds
            self.remaining = seconds
            self.timer_mode = "countdown"
            self.display_time(seconds)
            self.stop_timer()
        else:
            self.notify("Invalid duration.", severity="error")

    @on(Button.Pressed, "#btn-timer-start")
    def on_start(self) -> None:
        if self.timer_active:
            return

        now = datetime.now(timezone.utc).timestamp()

        if self.timer_mode == "countdown":
            if self.remaining <= 0:
                self.notify("Set duration first.", severity="warning")
                return

            self.end_time = now + self.remaining

        elif self.timer_mode == "stopwatch":
            if self.start_time == 0:
                self.start_time = now
            else:
                if self.paused_at > 0:
                    pause_duration = now - self.paused_at
                    self.start_time += pause_duration
                    self.paused_at = 0

        self.timer_active = True
        self.query_one("#btn-timer-start").disabled = True
        self.query_one("#btn-timer-stop").disabled = False
        self.query_one("#input-timer-duration").disabled = True

    @on(Button.Pressed, "#btn-timer-stop")
    def on_stop(self) -> None:
        self.stop_timer()
        self.paused_at = datetime.now(timezone.utc).timestamp()

        if self.timer_mode == "countdown":
            self.remaining = self.end_time - self.paused_at

    def stop_timer(self) -> None:
        self.timer_active = False
        self.query_one("#btn-timer-start").disabled = False
        self.query_one("#btn-timer-stop").disabled = True
        self.query_one("#input-timer-duration").disabled = False

    @on(Button.Pressed, "#btn-timer-reset")
    def on_reset(self) -> None:
        self.stop_timer()
        self.paused_at = 0
        self.start_time = 0
        if self.timer_mode == "countdown":
            self.remaining = self.duration
            self.display_time(self.duration)
        else:
            self.display_time(0)

    @on(Button.Pressed, "#btn-timer-pomo")
    def on_pomo(self) -> None:
        self.set_preset(25 * 60)

    @on(Button.Pressed, "#btn-timer-short")
    def on_short(self) -> None:
        self.set_preset(5 * 60)

    def set_preset(self, seconds: int) -> None:
        self.duration = seconds
        self.remaining = seconds
        self.timer_mode = "countdown"
        self.display_time(seconds)
        self.stop_timer()

    @on(Button.Pressed, "#btn-timer-mode")
    def on_switch_mode(self) -> None:
        self.stop_timer()
        if self.timer_mode == "countdown":
            self.timer_mode = "stopwatch"
            self.query_one("#btn-timer-mode", Button).label = "Countdown Mode"
            self.display_time(0)
            self.start_time = 0
        else:
            self.timer_mode = "countdown"
            self.query_one("#btn-timer-mode", Button).label = "Stopwatch Mode"
            self.display_time(self.duration)

class TimeLabTab(Container):
    """Tab for Time operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = TimeLabManager()
        self.common_zones = self.manager.get_common_timezones()
        # Ensure UTC is in the list
        if "UTC" not in self.common_zones:
            self.common_zones.insert(0, "UTC")

        # Default watch list for World Clock
        self.watch_list = ["UTC", "America/Los_Angeles", "America/New_York", "Europe/London", "Asia/Tokyo"]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Time Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # World Clock
                with TabPane("World Clock"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Button("Refresh", id="btn-time-refresh", variant="primary")
                            yield Select.from_values(self.common_zones, id="select-time-add-zone", prompt="Add Zone")
                            yield Button("Add", id="btn-time-add-zone", variant="success")

                        yield DataTable(id="time-world-table")

                # Converter
                with TabPane("Converter"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Time Converter[/bold]")

                        with Horizontal():
                            with Vertical():
                                yield Label("Source Time (ISO or Timestamp):")
                                yield Input(placeholder="Now (leave empty)", id="input-time-source")
                                yield Label("Source Zone (if not in string):")
                                yield Select.from_values(self.common_zones, id="select-time-src-zone", value="UTC")

                            with Vertical():
                                yield Label("Target Zone:")
                                yield Select.from_values(self.common_zones, id="select-time-dst-zone", value="America/Los_Angeles")

                        yield Button("Convert", id="btn-time-convert", variant="primary")

                        yield Label("[bold]Result:[/bold]")
                        yield Static(id="lbl-time-convert-result", classes="result-box")

                # Timestamp
                with TabPane("Timestamp"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Unix Timestamp Converter[/bold]")

                        yield Label("Input (ISO Date or Unix Timestamp):")
                        yield Input(placeholder="e.g. 1672531200 or 2023-01-01...", id="input-time-epoch")

                        with Horizontal():
                            yield Button("To Date", id="btn-time-to-date", variant="primary")
                            yield Button("To Timestamp", id="btn-time-to-epoch", variant="warning")
                            yield Button("Now", id="btn-time-epoch-now", variant="success")

                        yield Label("[bold]Result:[/bold]")
                        yield Static(id="lbl-time-epoch-result", classes="result-box")

                # Duration
                with TabPane("Duration"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Duration Calculator[/bold]")

                        yield Label("Start Time:")
                        yield Input(placeholder="ISO Date...", id="input-time-start")

                        yield Label("End Time:")
                        yield Input(placeholder="ISO Date...", id="input-time-end")

                        yield Button("Calculate Difference", id="btn-time-diff", variant="primary")

                        yield Label("[bold]Difference:[/bold]")
                        yield Static(id="lbl-time-diff-result", classes="result-box")

                # Timer
                with TabPane("Timer"):
                    yield TimerWidget()

    def on_mount(self) -> None:
        table = self.query_one("#time-world-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Zone", "Time", "Offset")
        self.update_world_clock()

    def update_world_clock(self) -> None:
        table = self.query_one("#time-world-table", DataTable)
        table.clear()

        for zone_name in self.watch_list:
            try:
                # Get time
                t_str = self.manager.get_current_time(zone_name)
                # Parse to get offset
                dt = datetime.fromisoformat(t_str)
                offset = dt.strftime("%z")
                # Format time nicely
                time_display = dt.strftime("%Y-%m-%d %H:%M:%S")

                table.add_row(zone_name, time_display, offset, key=zone_name)
            except Exception:
                table.add_row(zone_name, "Error", "?")

    @on(Button.Pressed, "#btn-time-refresh")
    def on_refresh(self) -> None:
        self.update_world_clock()
        self.notify("Clocks updated.")

    @on(Button.Pressed, "#btn-time-add-zone")
    def on_add_zone(self) -> None:
        select = self.query_one("#select-time-add-zone", Select)
        if select.value and select.value not in self.watch_list:
            self.watch_list.append(select.value)
            self.update_world_clock()
            self.notify(f"Added {select.value}")

    @on(DataTable.RowSelected, "#time-world-table")
    def on_remove_zone(self, event: DataTable.RowSelected) -> None:
        zone = event.row_key.value
        if zone in self.watch_list:
            self.watch_list.remove(zone)
            self.update_world_clock()
            self.notify(f"Removed {zone}")

    @on(Button.Pressed, "#btn-time-convert")
    def on_convert(self) -> None:
        src_time = self.query_one("#input-time-source", Input).value
        dst_zone = self.query_one("#select-time-dst-zone", Select).value

        if not src_time:
            src_time = datetime.now(timezone.utc).isoformat()

        # If input doesn't have TZ info, we might need to attach the src zone
        # But convert_time logic handles some of this.
        # Ideally, if user inputs "12:00", we assume source zone.
        # But TimeLabManager.convert_time assumes UTC if not specified in ISO string.
        # Let's try to handle it.

        try:
            result = self.manager.convert_time(src_time, dst_zone)
            if result.startswith("Error"):
                 self.query_one("#lbl-time-convert-result", Static).update(f"[red]{result}[/red]")
            else:
                 # Format it nicely
                 dt = datetime.fromisoformat(result)
                 fmt = dt.strftime("%Y-%m-%d %H:%M:%S %Z %z")
                 self.query_one("#lbl-time-convert-result", Static).update(f"[green]{fmt}[/green]")
        except Exception as e:
            self.query_one("#lbl-time-convert-result", Static).update(f"[red]Error: {e}[/red]")

    @on(Button.Pressed, "#btn-time-to-date")
    def on_to_date(self) -> None:
        val = self.query_one("#input-time-epoch", Input).value
        if not val:
            self.notify("Input required.", severity="error")
            return

        try:
            # Try interpreting as timestamp
            ts = float(val)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            self.query_one("#lbl-time-epoch-result", Static).update(f"[green]{dt.isoformat()}[/green]")
        except ValueError:
             self.notify("Invalid timestamp.", severity="error")

    @on(Button.Pressed, "#btn-time-to-epoch")
    def on_to_epoch(self) -> None:
        val = self.query_one("#input-time-epoch", Input).value
        if not val:
            self.notify("Input required.", severity="error")
            return

        result = self.manager.get_epoch(val)
        if result.startswith("Error"):
             self.query_one("#lbl-time-epoch-result", Static).update(f"[red]{result}[/red]")
        else:
             self.query_one("#lbl-time-epoch-result", Static).update(f"[green]{result}[/green]")

    @on(Button.Pressed, "#btn-time-epoch-now")
    def on_epoch_now(self) -> None:
        now = datetime.now(timezone.utc)
        self.query_one("#input-time-epoch", Input).value = str(now.timestamp())
        self.query_one("#lbl-time-epoch-result", Static).update(f"[green]Now: {now.isoformat()}[/green]")

    @on(Button.Pressed, "#btn-time-diff")
    def on_diff(self) -> None:
        start = self.query_one("#input-time-start", Input).value
        end = self.query_one("#input-time-end", Input).value

        if not start or not end:
            self.notify("Both Start and End times are required.", severity="error")
            return

        result = self.manager.diff_time(start, end)
        if result.startswith("Error"):
             self.query_one("#lbl-time-diff-result", Static).update(f"[red]{result}[/red]")
        else:
             self.query_one("#lbl-time-diff-result", Static).update(f"[green]{result}[/green]")

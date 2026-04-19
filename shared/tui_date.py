import json
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Select, TabbedContent, TabPane
from textual import on
from shared.date_lab import DateLabManager

class DateLabTab(Container):
    """Tab for interactive date operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = DateLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Date Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Arithmetic Pane
                with TabPane("Arithmetic"):
                    with Vertical(classes="stat-box"):
                        yield Label("Base Date (YYYY-MM-DD or ISO 8601):")
                        yield Input(placeholder="e.g. 2023-10-25", id="date-arith-base")

                        with Horizontal():
                            yield Input(placeholder="0", id="date-arith-days", type="integer")
                            yield Label("Days")
                            yield Input(placeholder="0", id="date-arith-weeks", type="integer")
                            yield Label("Weeks")

                        with Horizontal():
                            yield Button("Add", id="btn-date-add", variant="success")
                            yield Button("Subtract", id="btn-date-sub", variant="error")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="date-arith-result", wrap=True, highlight=True, markup=True)

                # Diff Pane
                with TabPane("Difference"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            with Vertical():
                                yield Label("Date 1:")
                                yield Input(placeholder="e.g. 2023-10-01", id="date-diff-1")
                            with Vertical():
                                yield Label("Date 2:")
                                yield Input(placeholder="e.g. 2023-10-25", id="date-diff-2")

                        yield Button("Calculate Difference", id="btn-date-diff", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="date-diff-result", wrap=True, highlight=True, markup=True)

                # Info & Format Pane
                with TabPane("Info & Format"):
                    with Vertical(classes="stat-box"):
                        yield Label("Date:")
                        yield Input(placeholder="e.g. 2023-10-25", id="date-info-input")

                        yield Label("Format String (for Format):")
                        yield Input(placeholder="%A, %B %d, %Y", id="date-format-str")

                        with Horizontal():
                            yield Button("Get Info", id="btn-date-info", variant="primary")
                            yield Button("Format Date", id="btn-date-format", variant="warning")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="date-info-result", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-date-add":
            self.do_arithmetic("add")
        elif event.button.id == "btn-date-sub":
            self.do_arithmetic("sub")
        elif event.button.id == "btn-date-diff":
            self.do_diff()
        elif event.button.id == "btn-date-info":
            self.do_info()
        elif event.button.id == "btn-date-format":
            self.do_format()

    def do_arithmetic(self, op: str) -> None:
        base_date = self.query_one("#date-arith-base", Input).value
        days_str = self.query_one("#date-arith-days", Input).value or "0"
        weeks_str = self.query_one("#date-arith-weeks", Input).value or "0"
        result_log = self.query_one("#date-arith-result", RichLog)

        result_log.clear()

        if not base_date:
            self.notify("Base date required.", severity="error")
            return

        try:
            days = int(days_str)
            weeks = int(weeks_str)
        except ValueError:
            self.notify("Days and weeks must be integers.", severity="error")
            return

        if op == "add":
            res = self.manager.add_date(base_date, days, weeks)
        else:
            res = self.manager.sub_date(base_date, days, weeks)

        if res.startswith("Error"):
            result_log.write(f"[bold red]{res}[/bold red]")
            self.notify("Error in calculation.", severity="error")
        else:
            result_log.write(f"[bold green]Result:[/bold green] {res}")

    def do_diff(self) -> None:
        date1 = self.query_one("#date-diff-1", Input).value
        date2 = self.query_one("#date-diff-2", Input).value
        result_log = self.query_one("#date-diff-result", RichLog)

        result_log.clear()

        if not date1 or not date2:
            self.notify("Both dates required.", severity="error")
            return

        res = self.manager.diff_dates(date1, date2)
        if res.get("success"):
            result_log.write(f"[bold green]Days Difference:[/bold green] {res['days']}")
            result_log.write(f"[bold green]Business Days:[/bold green] {res['business_days']}")
            result_log.write(f"[bold green]Total Seconds:[/bold green] {res['total_seconds']}")
        else:
            result_log.write(f"[bold red]Error:[/bold red] {res.get('error')}")
            self.notify("Error calculating difference.", severity="error")

    def do_info(self) -> None:
        date_str = self.query_one("#date-info-input", Input).value
        result_log = self.query_one("#date-info-result", RichLog)

        result_log.clear()

        if not date_str:
            self.notify("Date required.", severity="error")
            return

        res = self.manager.get_info(date_str)
        if res.get("success"):
            # Remove success key for cleaner display
            display_data = {k: v for k, v in res.items() if k != "success"}
            result_log.write(json.dumps(display_data, indent=2))
        else:
            result_log.write(f"[bold red]Error:[/bold red] {res.get('error')}")
            self.notify("Error getting info.", severity="error")

    def do_format(self) -> None:
        date_str = self.query_one("#date-info-input", Input).value
        fmt_str = self.query_one("#date-format-str", Input).value
        result_log = self.query_one("#date-info-result", RichLog)

        result_log.clear()

        if not date_str or not fmt_str:
            self.notify("Date and format string required.", severity="error")
            return

        res = self.manager.format_date(date_str, fmt_str)
        if res.startswith("Error"):
            result_log.write(f"[bold red]{res}[/bold red]")
            self.notify("Error formatting date.", severity="error")
        else:
            result_log.write(f"[bold green]Formatted:[/bold green] {res}")

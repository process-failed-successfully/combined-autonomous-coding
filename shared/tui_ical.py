import json
import datetime
try:
    from textual.app import ComposeResult
    from textual.containers import Container, Horizontal, Vertical, VerticalScroll
    from textual.widgets import Button, Label, Input, TextArea, TabbedContent, TabPane, RichLog
except ImportError:
    Container = object

from shared.ical_lab import ICalManager

class ICalLabTab(Container):
    """Tab for iCalendar (iCal) Lab."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = ICalManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]iCalendar (iCal) Lab[/bold]", classes="welcome-text")

            with TabbedContent(id="ical-tabs"):
                with TabPane("Parse", id="tab-ical-parse"):
                    with Vertical(classes="stat-box"):
                        yield Label("Input iCalendar (.ics) Data:")
                        yield TextArea(id="ical-parse-input")
                        with Horizontal():
                            yield Button("Parse", id="btn-ical-parse", variant="primary")
                        yield Label("Parsed Events (JSON):")
                        yield RichLog(id="ical-parse-output", wrap=True, highlight=True, markup=True)

                with TabPane("Generate", id="tab-ical-generate"):
                    with Vertical(classes="stat-box"):
                        yield Label("Summary (Title):")
                        yield Input(id="ical-gen-summary", placeholder="Meeting with Team")

                        yield Label("Start Time (YYYY-MM-DD HH:MM):")
                        yield Input(id="ical-gen-start", placeholder="2024-01-01 10:00")

                        yield Label("End Time (YYYY-MM-DD HH:MM):")
                        yield Input(id="ical-gen-end", placeholder="2024-01-01 11:00")

                        yield Label("Location (Optional):")
                        yield Input(id="ical-gen-location", placeholder="Conference Room A")

                        yield Label("Description (Optional):")
                        yield TextArea(id="ical-gen-description", classes="small-textarea")

                        with Horizontal():
                            yield Button("Generate", id="btn-ical-generate", variant="primary")

                        yield Label("Generated iCalendar (.ics) Data:")
                        yield TextArea(id="ical-gen-output", read_only=True)

                with TabPane("Validate", id="tab-ical-validate"):
                    with Vertical(classes="stat-box"):
                        yield Label("Input iCalendar (.ics) Data:")
                        yield TextArea(id="ical-val-input")
                        with Horizontal():
                            yield Button("Validate", id="btn-ical-validate", variant="primary")
                        yield Label("Validation Result:", id="ical-val-result")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ical-parse":
            text = self.query_one("#ical-parse-input", TextArea).text
            if not text.strip():
                self.notify("Please enter iCalendar data.", severity="warning")
                return
            events = self.manager.parse_ics(text)
            log = self.query_one("#ical-parse-output", RichLog)
            log.clear()
            log.write(json.dumps(events, indent=2))

        elif event.button.id == "btn-ical-generate":
            summary = self.query_one("#ical-gen-summary", Input).value
            start_str = self.query_one("#ical-gen-start", Input).value
            end_str = self.query_one("#ical-gen-end", Input).value
            location = self.query_one("#ical-gen-location", Input).value
            description = self.query_one("#ical-gen-description", TextArea).text

            if not summary or not start_str or not end_str:
                self.notify("Summary, Start Time, and End Time are required.", severity="error")
                return

            try:
                dtstart = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M")
                dtend = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M")
            except ValueError:
                self.notify("Invalid date format. Use YYYY-MM-DD HH:MM.", severity="error")
                return

            output = self.manager.generate_ics(summary, dtstart, dtend, location, description)
            out_area = self.query_one("#ical-gen-output", TextArea)
            try:
                out_area.text = output
            except Exception:
                out_area.load_text(output)

        elif event.button.id == "btn-ical-validate":
            text = self.query_one("#ical-val-input", TextArea).text
            if not text.strip():
                self.notify("Please enter iCalendar data.", severity="warning")
                return
            is_valid = self.manager.validate_ics(text)
            result_label = self.query_one("#ical-val-result", Label)
            if is_valid:
                result_label.update("[bold green]Valid iCalendar format.[/bold green]")
            else:
                result_label.update("[bold red]Invalid iCalendar format.[/bold red]")

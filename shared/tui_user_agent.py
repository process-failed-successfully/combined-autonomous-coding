from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, Input, Select, TabbedContent, TabPane, RichLog, DataTable
from textual import on
from shared.user_agent_lab import UserAgentManager

class UserAgentLabTab(Container):
    """Tab for User Agent parsing and generation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = UserAgentManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]User Agent Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Parse Tab
                with TabPane("Parse", id="ua-tab-parse"):
                    with Vertical(classes="stat-box"):
                        yield Label("User Agent String:")
                        yield Input(placeholder="Paste UA string here...", id="ua-parse-input")
                        yield Button("Parse", id="btn-ua-parse", variant="primary")

                    yield Label("[bold]Parsed Details[/bold]")
                    yield DataTable(id="ua-parse-table")

                # Generate Tab
                with TabPane("Generate", id="ua-tab-gen"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            with Vertical():
                                yield Label("Operating System:")
                                yield Select.from_values(list(self.manager.templates.keys()), id="ua-gen-os")

                            with Vertical():
                                yield Label("Browser:")
                                yield Select([], id="ua-gen-browser", disabled=True)

                        yield Button("Generate", id="btn-ua-gen", variant="warning")

                    yield Label("[bold]Generated User Agent[/bold]")
                    yield Input(id="ua-gen-output", disabled=True)
                    yield RichLog(id="ua-gen-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#ua-parse-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Field", "Value")

    @on(Button.Pressed, "#btn-ua-parse")
    def on_parse(self) -> None:
        ua_string = self.query_one("#ua-parse-input", Input).value.strip()
        if not ua_string:
            self.notify("Please enter a User Agent string.", severity="error")
            return

        result = self.manager.parse(ua_string)
        table = self.query_one("#ua-parse-table", DataTable)
        table.clear()

        for k, v in result.items():
            table.add_row(k.capitalize(), str(v))

    @on(Select.Changed, "#ua-gen-os")
    def on_os_changed(self, event: Select.Changed) -> None:
        os_name = event.value
        browser_select = self.query_one("#ua-gen-browser", Select)

        if os_name == Select.BLANK:
            browser_select.set_options([])
            browser_select.disabled = True
            return

        browsers = list(self.manager.templates.get(str(os_name), {}).keys())
        browser_select.set_options([(b, b) for b in browsers])
        browser_select.disabled = False
        browser_select.clear()

    @on(Button.Pressed, "#btn-ua-gen")
    def on_generate(self) -> None:
        os_name = self.query_one("#ua-gen-os", Select).value
        browser = self.query_one("#ua-gen-browser", Select).value

        if os_name == Select.BLANK:
            self.notify("Please select an OS.", severity="error")
            return
        if browser == Select.BLANK:
            self.notify("Please select a Browser.", severity="error")
            return

        # Convert values to string to satisfy mypy
        os_str = str(os_name)
        browser_str = str(browser)

        ua = self.manager.generate(os_str, browser_str)

        out_input = self.query_one("#ua-gen-output", Input)
        out_input.value = ua or "Error generating UA"

        log = self.query_one("#ua-gen-log", RichLog)
        log.write(f"[bold green]Generated:[/bold green] {os_str} - {browser_str}")

import json
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal, Vertical
from textual.widgets import Button, Input, Label, TextArea, DataTable
from shared.cookie_lab import CookieLabManager


class CookieLabTab(VerticalScroll):
    """TUI Tab for Cookie Lab operations."""

    def __init__(self, project_dir=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CookieLabManager()

    def compose(self) -> ComposeResult:
        yield Label("Cookie Lab", classes="header-label")

        with Vertical(classes="panel"):
            yield Label("Parse Cookie", classes="section-label")
            yield Input(placeholder="Enter raw Cookie or Set-Cookie header string", id="cl-cookie-input")
            with Horizontal():
                yield Button("Parse", id="btn-cl-parse", variant="primary")
                yield Button("Clear", id="btn-cl-clear-parse", variant="error")

            # Using DataTable for parsed results
            yield DataTable(id="cl-parsed-table")

        with Vertical(classes="panel"):
            yield Label("Generate Cookie", classes="section-label")
            yield Label("Enter JSON array of cookie objects:")
            yield TextArea(
                text='[\n  {\n    "name": "session_id",\n    "value": "123456",\n    "domain": "example.com",\n    "path": "/",\n    "secure": true,\n    "httponly": true\n  }\n]',
                id="cl-json-input",
                language="json"
            )
            with Horizontal():
                yield Button("Generate", id="btn-cl-generate", variant="primary")
                yield Button("Clear", id="btn-cl-clear-gen", variant="error")
            yield TextArea(id="cl-gen-output", read_only=True)

    def on_mount(self) -> None:
        table = self.query_one("#cl-parsed-table", DataTable)
        table.add_columns("Property", "Value")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn-cl-parse":
            self.do_parse()
        elif button_id == "btn-cl-clear-parse":
            self.query_one("#cl-cookie-input", Input).value = ""
            table = self.query_one("#cl-parsed-table", DataTable)
            table.clear()
        elif button_id == "btn-cl-generate":
            self.do_generate()
        elif button_id == "btn-cl-clear-gen":
            self.query_one("#cl-gen-output", TextArea).text = ""

    def do_parse(self) -> None:
        cookie_str = self.query_one("#cl-cookie-input", Input).value.strip()
        table = self.query_one("#cl-parsed-table", DataTable)
        table.clear()

        if not cookie_str:
            table.add_row("Error", "Please enter a cookie string.")
            return

        parsed = self.manager.parse(cookie_str)
        if not parsed:
            table.add_row("Info", "No valid cookies found.")
            return

        if "error" in parsed[0]:
            table.add_row("Error", parsed[0]["error"])
            return

        for i, c in enumerate(parsed):
            table.add_row(f"--- Cookie {i+1} ---", "")
            for k, v in c.items():
                table.add_row(k, str(v))

    def do_generate(self) -> None:
        json_str = self.query_one("#cl-json-input", TextArea).text.strip()
        out_area = self.query_one("#cl-gen-output", TextArea)
        out_area.text = ""

        if not json_str:
            out_area.text = "Error: Input JSON is empty."
            return

        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                data = [data]

            results = self.manager.generate(data)
            out_area.text = "\n".join(results)
        except Exception as e:
            out_area.text = f"Error generating cookie: {str(e)}"

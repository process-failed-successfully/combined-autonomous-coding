from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, Select, DataTable, RichLog, TextArea, ListView, ListItem, TabbedContent, TabPane
from textual import on
from rich.syntax import Syntax
import json
import asyncio
from shared.http_lab import HttpLabManager

class HttpLabTab(Container):
    """Tab for HTTP Client (Postman-like)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = HttpLabManager()
        self.history = [] # List of dicts

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: History
            with Vertical(id="http-history-pane", classes="stat-box"):
                yield Label("[bold]History[/bold]")
                yield ListView(id="http-history-list")
                yield Button("Clear History", id="btn-http-clear", variant="error")

            # Right Pane: Workspace
            with Vertical(id="http-workspace-pane"):
                yield Label("[bold]HTTP Request Builder[/bold]", classes="welcome-text")

                # Request Line
                with Horizontal(classes="stat-box"):
                    yield Select.from_values(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], id="http-method", value="GET")
                    yield Input(placeholder="https://api.example.com/v1/...", id="http-url")
                    yield Button("Send", id="btn-http-send", variant="primary")

                with TabbedContent(id="http-tabs"):
                    with TabPane("Headers", id="http-tab-headers"):
                        yield Label("Key: Value (one per line)")
                        yield TextArea(id="http-headers", language="yaml") # yaml gives decent highlighting for key: value

                    with TabPane("Body", id="http-tab-body"):
                        yield Label("Request Body (JSON)")
                        yield TextArea(id="http-body", language="json")

                    with TabPane("Response", id="http-tab-response"):
                        with VerticalScroll():
                            with Horizontal(classes="stat-box"):
                                yield Label("Status: ", id="http-status-lbl")
                                yield Label("Time: ", id="http-time-lbl")

                            yield Label("[bold]Response Headers[/bold]")
                            yield DataTable(id="http-res-headers-table")

                            yield Label("[bold]Response Body[/bold]")
                            yield RichLog(id="http-res-body", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        # Init headers table
        table = self.query_one("#http-res-headers-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Header", "Value")

        # Adjust layout
        self.query_one("#http-url").styles.width = "1fr"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-http-send":
            await self.send_request()
        elif event.button.id == "btn-http-clear":
            self.clear_history()

    async def send_request(self) -> None:
        method = self.query_one("#http-method", Select).value
        url = self.query_one("#http-url", Input).value
        headers_text = self.query_one("#http-headers", TextArea).text
        body_text = self.query_one("#http-body", TextArea).text

        if not url:
            self.notify("URL is required.", severity="error")
            return

        # Parse headers
        headers = {}
        for line in headers_text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()

        # Parse body (if JSON)
        json_data = None
        data = None
        if body_text.strip():
            try:
                json_data = json.loads(body_text)
            except json.JSONDecodeError:
                data = body_text # Send as raw string if not valid JSON

        # Update UI state
        self.query_one("#btn-http-send").disabled = True
        self.notify(f"Sending {method} {url}...")

        # Clear previous response
        self.query_one("#http-res-body", RichLog).clear()
        self.query_one("#http-res-headers-table", DataTable).clear()
        self.query_one("#http-status-lbl").update("Status: ...")

        # Run request
        try:
            # We use HttpLabManager.request which handles exceptions and returns a dict
            kwargs = {
                "headers": headers,
                "timeout": 10.0
            }
            if json_data:
                kwargs["json"] = json_data
            elif data:
                kwargs["data"] = data

            # Run in thread
            result = await asyncio.to_thread(self.manager.request, method, url, **kwargs)

            self.display_response(result)
            self.add_to_history(method, url, result.get('status_code', 0))

        except Exception as e:
            self.notify(f"Request failed: {e}", severity="error")
        finally:
            self.query_one("#btn-http-send").disabled = False

    def display_response(self, result: dict) -> None:
        # Switch to Response tab
        self.query_one("#http-tabs", TabbedContent).active = "http-tab-response"

        status_code = result.get('status_code', 'Error')
        elapsed = result.get('elapsed', 0)

        color = "green" if result.get('ok') else "red"
        self.query_one("#http-status-lbl").update(f"Status: [bold {color}]{status_code}[/]")
        self.query_one("#http-time-lbl").update(f"Time: {elapsed:.2f}s")

        # Headers
        table = self.query_one("#http-res-headers-table", DataTable)
        table.clear()
        if 'headers' in result:
            for k, v in result['headers'].items():
                table.add_row(k, v)

        # Body
        log = self.query_one("#http-res-body", RichLog)
        log.clear()

        body = result.get('body', '')
        if result.get('json'):
            # Pretty print JSON
            log.write(Syntax(json.dumps(result['json'], indent=2), "json", theme="monokai"))
        else:
            log.write(body)

    def add_to_history(self, method: str, url: str, status: int) -> None:
        self.history.insert(0, {"method": method, "url": url, "status": status})
        self.refresh_history_list()

    def refresh_history_list(self) -> None:
        lst = self.query_one("#http-history-list", ListView)
        lst.clear()
        for item in self.history:
            status = item['status']
            color = "green" if 200 <= status < 300 else "red"
            label = f"[{color}]{status}[/] {item['method']} {item['url']}"
            lst.append(ListItem(Label(label)))

    def clear_history(self) -> None:
        self.history = []
        self.refresh_history_list()
        self.notify("History cleared.")

    @on(ListView.Selected, "#http-history-list")
    def on_history_selected(self, event: ListView.Selected) -> None:
        index = event.list_view.index
        if index is not None and 0 <= index < len(self.history):
            item = self.history[index]
            self.query_one("#http-method", Select).value = item['method']
            self.query_one("#http-url", Input).value = item['url']
            self.notify(f"Loaded {item['method']} {item['url']}")

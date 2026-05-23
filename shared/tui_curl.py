from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, TextArea, TabbedContent, TabPane
from textual.containers import ScrollableContainer

from shared.curl_lab import CurlLabManager


class CurlLabTab(ScrollableContainer):
    """TUI Tab for cURL Converter Lab."""

    def __init__(self, project_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CurlLabManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="tab-content"):
            yield Label("[bold]cURL Converter Lab[/bold] - Convert cURL commands to code", classes="tab-title")

            with Horizontal(classes="action-bar"):
                yield Button("Convert", id="btn-curl-convert", variant="primary")
                yield Button("Clear", id="btn-curl-clear", variant="warning")

            with Horizontal():
                with Vertical(classes="panel"):
                    yield Label("Input cURL Command:")
                    yield TextArea(id="curl-input-area", language="bash")

                with Vertical(classes="panel"):
                    yield Label("Generated Code:")
                    with TabbedContent(id="curl-output-tabs"):
                        with TabPane("Python (requests)"):
                            yield TextArea(id="curl-output-python", language="python", read_only=True)
                        with TabPane("JavaScript (fetch)"):
                            yield TextArea(id="curl-output-js", language="javascript", read_only=True)
                        with TabPane("Go (net/http)"):
                            yield TextArea(id="curl-output-go", language="go", read_only=True)
                        with TabPane("PowerShell (Invoke-WebRequest)"):
                            yield TextArea(id="curl-output-ps", disabled=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-curl-convert":
            self.convert_curl()
        elif event.button.id == "btn-curl-clear":
            self.clear_all()

    def convert_curl(self) -> None:
        input_area = self.query_one("#curl-input-area", TextArea)
        curl_cmd = input_area.text.strip()

        if not curl_cmd:
            self.app.notify("cURL command input is required.", severity="error")
            return

        try:
            parsed = self.manager.parse_curl(curl_cmd)

            py_code = self.manager.to_python_requests(parsed)
            js_code = self.manager.to_js_fetch(parsed)
            go_code = self.manager.to_go_http(parsed)
            ps_code = self.manager.to_powershell_iwr(parsed)

            self.query_one("#curl-output-python", TextArea).text = py_code
            self.query_one("#curl-output-js", TextArea).text = js_code
            self.query_one("#curl-output-go", TextArea).text = go_code
            self.query_one("#curl-output-ps", TextArea).text = ps_code

            self.app.notify("cURL command successfully converted.")
        except Exception as e:
            self.app.notify(f"Parsing Error: {e}", severity="error")

    def clear_all(self) -> None:
        self.query_one("#curl-input-area", TextArea).text = ""
        self.query_one("#curl-output-python", TextArea).text = ""
        self.query_one("#curl-output-js", TextArea).text = ""
        self.query_one("#curl-output-go", TextArea).text = ""
        self.query_one("#curl-output-ps", TextArea).text = ""
        self.app.notify("Fields cleared.")

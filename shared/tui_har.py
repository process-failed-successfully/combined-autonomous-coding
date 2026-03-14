import sys
import os
import json
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, ListView, ListItem, TextArea, RichLog
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual import on
from rich.syntax import Syntax

from shared.har_lab import HarLabManager

class HarLabTab(Container):
    """Tab for parsing and viewing HTTP Archive (.har) files."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = HarLabManager(project_dir)
        self.har_data = None
        self.entries = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]HAR Lab[/bold]", classes="welcome-text")

            # File Input & Actions
            with Horizontal(classes="stat-box", id="har-file-container"):
                yield Label("Load HAR File:", classes="label")
                from textual.widgets import Input
                yield Input(placeholder="Path to .har file...", id="har-file-input")
                yield Button("Load", id="btn-har-load", variant="primary")

            with Horizontal():
                # Left Pane: Request List
                with Vertical(id="har-requests-container", classes="stat-box"):
                    yield Label("[bold]Requests[/bold]")
                    yield DataTable(id="har-requests-table")

                # Right Pane: Request Details
                with VerticalScroll(id="har-details-container"):
                    yield Label("[bold]Request Details[/bold]")
                    from textual.widgets import TabbedContent, TabPane
                    with TabbedContent():
                        with TabPane("Headers", id="har-tab-headers"):
                            yield RichLog(id="har-headers-log", wrap=True, markup=True)
                        with TabPane("Request Body", id="har-tab-request"):
                            yield RichLog(id="har-request-log", wrap=True, markup=True)
                        with TabPane("Response Body", id="har-tab-response"):
                            yield RichLog(id="har-response-log", wrap=True, markup=True)
                        with TabPane("cURL", id="har-tab-curl"):
                            yield RichLog(id="har-curl-log", wrap=True, markup=True)

    def on_mount(self) -> None:
        # Initialize DataTable
        table = self.query_one("#har-requests-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Method", "Status", "Time", "URL")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-har-load":
            await self.load_har_file()

    async def load_har_file(self) -> None:
        from textual.widgets import Input
        inp = self.query_one("#har-file-input", Input)
        file_path = inp.value

        if not file_path:
            self.notify("Please enter a path to a HAR file.", severity="warning")
            return

        path = self.project_dir / file_path if not os.path.isabs(file_path) else Path(file_path)

        if not path.exists():
            self.notify(f"File not found: {path}", severity="error")
            return

        try:
            self.har_data = self.manager._parse_har(path)
            self.entries = self.har_data.get('log', {}).get('entries', [])

            table = self.query_one("#har-requests-table", DataTable)
            table.clear()

            for i, entry in enumerate(self.entries):
                req = entry.get('request', {})
                res = entry.get('response', {})

                method = req.get('method', 'UNKNOWN')
                status = res.get('status', 0)
                time_val = entry.get('time', 0.0)
                url = req.get('url', '')

                # Format time
                time_str = f"{time_val:.0f}ms"

                # Truncate URL for display
                display_url = url[:50] + "..." if len(url) > 50 else url

                # Add row with index as key
                table.add_row(method, str(status), time_str, display_url, key=str(i))

            self.notify(f"Loaded {len(self.entries)} requests from {path.name}")

        except Exception as e:
            self.notify(f"Error loading HAR file: {e}", severity="error")

    @on(DataTable.RowSelected, "#har-requests-table")
    def on_request_selected(self, event: DataTable.RowSelected) -> None:
        if not self.entries:
            return

        try:
            index = int(event.row_key.value)
            entry = self.entries[index]

            req = entry.get('request', {})
            res = entry.get('response', {})

            # Update Headers
            headers_log = self.query_one("#har-headers-log", RichLog)
            headers_log.clear()
            headers_log.write("[bold]Request Headers:[/bold]")
            for header in req.get('headers', []):
                headers_log.write(f"  {header.get('name')}: {header.get('value')}")

            headers_log.write("\n[bold]Response Headers:[/bold]")
            for header in res.get('headers', []):
                headers_log.write(f"  {header.get('name')}: {header.get('value')}")

            # Update Request Body
            req_log = self.query_one("#har-request-log", RichLog)
            req_log.clear()
            post_data = req.get('postData', {})
            req_text = post_data.get('text', '')
            if req_text:
                mime_type = post_data.get('mimeType', '')
                req_log.write(f"[bold]Content-Type: {mime_type}[/bold]\n")
                if 'json' in mime_type.lower():
                    try:
                        # Attempt to pretty-print JSON
                        parsed = json.loads(req_text)
                        pretty = json.dumps(parsed, indent=2)
                        req_log.write(Syntax(pretty, "json", theme="monokai"))
                    except json.JSONDecodeError:
                        req_log.write(req_text)
                else:
                    req_log.write(req_text)
            else:
                req_log.write("No request body.")

            # Update Response Body
            res_log = self.query_one("#har-response-log", RichLog)
            res_log.clear()
            res_content = res.get('content', {})
            res_text = res_content.get('text', '')
            if res_text:
                mime_type = res_content.get('mimeType', '')
                res_log.write(f"[bold]Content-Type: {mime_type}[/bold]\n")
                if 'json' in mime_type.lower():
                    try:
                        # Attempt to pretty-print JSON
                        parsed = json.loads(res_text)
                        pretty = json.dumps(parsed, indent=2)
                        res_log.write(Syntax(pretty, "json", theme="monokai"))
                    except json.JSONDecodeError:
                        res_log.write(res_text)
                else:
                    res_log.write(res_text)
            else:
                res_log.write("No response body.")

            # Update cURL
            curl_log = self.query_one("#har-curl-log", RichLog)
            curl_log.clear()

            # Generate curl string manually to not depend on a specific file path
            method = req.get('method', 'GET')
            url = req.get('url', '')
            curl_cmd = f"curl -X {method} '{url}'"

            for header in req.get('headers', []):
                name = header.get('name')
                value = header.get('value')
                if name and value:
                    value_escaped = value.replace("'", "'\\''")
                    curl_cmd += f" \\\n  -H '{name}: {value_escaped}'"

            if req_text:
                text_escaped = req_text.replace("'", "'\\''")
                curl_cmd += f" \\\n  -d '{text_escaped}'"

            curl_log.write(Syntax(curl_cmd, "bash", theme="monokai"))

        except Exception as e:
            self.notify(f"Error displaying request details: {e}", severity="error")

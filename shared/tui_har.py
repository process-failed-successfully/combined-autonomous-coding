from pathlib import Path
import json

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, RichLog, DirectoryTree, TabbedContent, TabPane
from textual import on

from shared.har_lab import HarLabManager

class HarLabTab(Container):
    """Tab for exploring HAR files."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = HarLabManager(project_dir)
        self.har_data = None
        self.selected_entry_index = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left pane: File explorer and Summary
            with Vertical(id="har-sidebar-container", classes="stat-box", style="width: 30%;"):
                yield Label("[bold]HAR Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="har-file-tree")

                yield Label("[bold]Summary[/bold]")
                yield RichLog(id="har-summary-log", wrap=True, highlight=True, markup=False)

            # Right pane: Requests table and details
            with Vertical(id="har-main-container"):
                yield Label("[bold]Requests[/bold]")
                yield DataTable(id="har-requests-table")

                with TabbedContent():
                    with TabPane("Details"):
                        yield RichLog(id="har-details-log", wrap=True, highlight=True, markup=False)
                    with TabPane("cURL"):
                        yield RichLog(id="har-curl-log", wrap=True, highlight=True, markup=False)
                        with Horizontal():
                             yield Button("Copy to Clipboard", id="btn-har-copy-curl", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#har-requests-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Index", "Method", "Status", "URL", "Time (ms)", "Size (B)")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        if event.path.suffix.lower() == ".har":
            self.load_har_file(event.path)
        else:
            self.notify("Please select a .har file.", severity="warning")

    def load_har_file(self, filepath: Path) -> None:
        self.notify(f"Loading {filepath.name}...")
        try:
            self.har_data = self.manager.load_har(filepath)
            self.update_summary()
            self.update_requests_table()
            self.notify("HAR file loaded.")

            # Clear details logs
            self.query_one("#har-details-log", RichLog).clear()
            self.query_one("#har-curl-log", RichLog).clear()
            self.query_one("#btn-har-copy-curl", Button).disabled = True

        except Exception as e:
            self.notify(f"Error loading HAR: {e}", severity="error")

    def update_summary(self) -> None:
        log = self.query_one("#har-summary-log", RichLog)
        log.clear()

        if not self.har_data:
            return

        summary = self.manager.summarize(self.har_data)

        log.write(f"Total Requests: {summary['total_requests']}")
        log.write(f"Total Size: {summary['total_size_bytes']} bytes")

        log.write("\n[bold]Methods:[/bold]")
        for method, count in summary['methods'].items():
            log.write(f"  {method}: {count}")

        log.write("\n[bold]Statuses:[/bold]")
        for status, count in summary['statuses'].items():
            log.write(f"  {status}: {count}")

    def update_requests_table(self) -> None:
        table = self.query_one("#har-requests-table", DataTable)
        table.clear()

        if not self.har_data:
            return

        entries = self.har_data.get("log", {}).get("entries", [])
        for i, entry in enumerate(entries):
            req = entry.get("request", {})
            res = entry.get("response", {})

            method = req.get("method", "")
            url = req.get("url", "")

            # Truncate URL if too long
            if len(url) > 60:
                url = url[:57] + "..."

            status = res.get("status", "")

            # Colorize status
            status_str = str(status)
            if 200 <= status < 300:
                status_str = f"[green]{status}[/green]"
            elif 300 <= status < 400:
                status_str = f"[yellow]{status}[/yellow]"
            elif 400 <= status < 600:
                status_str = f"[red]{status}[/red]"

            time_val = round(entry.get("time", 0))
            size = res.get("bodySize", 0)

            table.add_row(str(i), method, status_str, url, str(time_val), str(size), key=str(i))

    @on(DataTable.RowSelected, "#har-requests-table")
    def on_request_selected(self, event: DataTable.RowSelected) -> None:
        if not self.har_data:
            return

        index = int(event.row_key.value)
        self.selected_entry_index = index
        entries = self.har_data.get("log", {}).get("entries", [])

        if index < 0 or index >= len(entries):
            return

        entry = entries[index]
        self.show_details(entry)
        self.show_curl(entry)

    def show_details(self, entry: dict) -> None:
        log = self.query_one("#har-details-log", RichLog)
        log.clear()

        req = entry.get("request", {})
        res = entry.get("response", {})

        log.write(f"[bold blue]Request:[/bold blue] {req.get('method')} {req.get('url')}")
        log.write("\n[bold]Request Headers:[/bold]")
        for h in req.get("headers", []):
            log.write(f"  {h.get('name')}: {h.get('value')}")

        if req.get("postData"):
            log.write("\n[bold]Request Body:[/bold]")
            text = req.get("postData", {}).get("text", "")
            try:
                # Try pretty printing if JSON
                parsed = json.loads(text)
                log.write(json.dumps(parsed, indent=2))
            except Exception:
                log.write(text)

        log.write("\n" + "="*40 + "\n")

        log.write(f"[bold green]Response:[/bold green] Status {res.get('status')} {res.get('statusText')}")
        log.write("\n[bold]Response Headers:[/bold]")
        for h in res.get("headers", []):
            log.write(f"  {h.get('name')}: {h.get('value')}")

        if res.get("content"):
            log.write("\n[bold]Response Body:[/bold]")
            text = res.get("content", {}).get("text", "")
            if not text:
                 log.write("(No body or empty)")
            else:
                 try:
                     parsed = json.loads(text)
                     log.write(json.dumps(parsed, indent=2))
                 except Exception:
                     # Truncate if it's too long and not JSON
                     if len(text) > 1000:
                         log.write(text[:1000] + "\n...[truncated]")
                     else:
                         log.write(text)

    def show_curl(self, entry: dict) -> None:
        log = self.query_one("#har-curl-log", RichLog)
        log.clear()

        curl_cmd = self.manager.entry_to_curl(entry)
        log.write(curl_cmd)

        # Enable copy button
        self.query_one("#btn-har-copy-curl", Button).disabled = False

    @on(Button.Pressed, "#btn-har-copy-curl")
    def on_copy_curl(self) -> None:
        if self.har_data and self.selected_entry_index is not None:
             entries = self.har_data.get("log", {}).get("entries", [])
             if 0 <= self.selected_entry_index < len(entries):
                  entry = entries[self.selected_entry_index]
                  curl_cmd = self.manager.entry_to_curl(entry)

                  # Hacky way to copy to clipboard in a terminal environment (if pbcopy/xclip exist)
                  # But textual has no built-in clipboard support yet. Let's just notify.
                  # A real implementation would use pyperclip or similar if available.
                  import subprocess
                  try:
                      # Try xclip (Linux)
                      subprocess.run(["xclip", "-selection", "c"], input=curl_cmd.encode('utf-8'), check=True, stderr=subprocess.DEVNULL)
                      self.notify("Copied to clipboard (xclip)!")
                  except Exception:
                      try:
                          # Try pbcopy (Mac)
                          subprocess.run(["pbcopy"], input=curl_cmd.encode('utf-8'), check=True, stderr=subprocess.DEVNULL)
                          self.notify("Copied to clipboard (pbcopy)!")
                      except Exception:
                           self.notify("Clipboard copy not supported on this system.", severity="warning")

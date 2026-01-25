from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, RichLog, Select
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from rich.syntax import Syntax
from pathlib import Path
import asyncio

from shared.security import SecurityAuditor

class SecurityTab(Container):
    """Tab for interactive security auditing."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.auditor = SecurityAuditor(project_dir)
        self.findings = []
        self.selected_finding = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Controls & List
            with Vertical(id="sec-controls-container", classes="stat-box"):
                yield Label("[bold]Security Scanner[/bold]")

                with Vertical(classes="stat-box"):
                    yield Label("Run Scan:")
                    yield Button("Full Scan", id="btn-sec-scan-all", variant="primary")
                    yield Button("Secrets Only", id="btn-sec-scan-secrets", variant="default")
                    yield Button("SAST Only", id="btn-sec-scan-sast", variant="default")
                    yield Button("Deps Only", id="btn-sec-scan-deps", variant="default")

                yield Label("[bold]Findings[/bold]")
                yield DataTable(id="sec-findings-table")

            # Right Pane: Details & Actions
            with Vertical(id="sec-details-container"):
                yield Label("[bold]Finding Details[/bold]")
                yield RichLog(id="sec-details-log", wrap=True, highlight=True, markup=True)

                with Horizontal(classes="stat-box"):
                    yield Button("Ignore File", id="btn-sec-ignore-file", variant="warning", disabled=True)
                    yield Button("Ignore Pattern", id="btn-sec-ignore-pattern", variant="error", disabled=True)

                yield Label("", id="sec-status-lbl")

    def on_mount(self) -> None:
        table = self.query_one("#sec-findings-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Severity", "Type", "File", "Line")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-sec-scan-all":
            await self.run_scan("all")
        elif event.button.id == "btn-sec-scan-secrets":
            await self.run_scan("secrets")
        elif event.button.id == "btn-sec-scan-sast":
            await self.run_scan("sast")
        elif event.button.id == "btn-sec-scan-deps":
            await self.run_scan("deps")
        elif event.button.id == "btn-sec-ignore-file":
            self.ignore_file()
        elif event.button.id == "btn-sec-ignore-pattern":
            self.ignore_pattern()

    async def run_scan(self, scan_type: str) -> None:
        table = self.query_one("#sec-findings-table", DataTable)
        table.clear()
        self.query_one("#sec-details-log", RichLog).clear()
        self.query_one("#sec-status-lbl").update(f"Scanning ({scan_type})...")
        self.notify(f"Starting {scan_type} scan...")

        # Disable buttons
        self.query_one("#btn-sec-ignore-file").disabled = True

        try:
            # Run in thread
            self.findings = await asyncio.to_thread(self.auditor.run_all, scan_type=scan_type)

            # Sort findings by severity
            severity_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "UNKNOWN": 3}
            self.findings.sort(key=lambda x: severity_map.get(str(x.get("severity", "UNKNOWN")).upper(), 3))

            for i, f in enumerate(self.findings):
                sev = str(f.get("severity", "UNKNOWN")).upper()
                if sev == "HIGH":
                    sev_fmt = f"[red]{sev}[/red]"
                elif sev == "MEDIUM":
                    sev_fmt = f"[yellow]{sev}[/yellow]"
                else:
                    sev_fmt = f"[blue]{sev}[/blue]"

                file_path = f.get("file", "N/A")
                line = str(f.get("line", 0))

                table.add_row(sev_fmt, f.get("type", "unknown"), file_path, line, key=str(i))

            self.query_one("#sec-status-lbl").update(f"Scan complete. Found {len(self.findings)} issues.")
            self.notify(f"Found {len(self.findings)} issues.")

        except Exception as e:
            self.query_one("#sec-status-lbl").update(f"Error: {e}")
            self.notify(f"Scan error: {e}", severity="error")

    @on(DataTable.RowSelected, "#sec-findings-table")
    def on_finding_selected(self, event: DataTable.RowSelected) -> None:
        try:
            index = int(event.row_key.value)
            self.selected_finding = self.findings[index]
            self.update_details()
            self.query_one("#btn-sec-ignore-file").disabled = False
            # self.query_one("#btn-sec-ignore-pattern").disabled = False # Not impl yet
        except (ValueError, IndexError):
            pass

    def update_details(self) -> None:
        log = self.query_one("#sec-details-log", RichLog)
        log.clear()

        f = self.selected_finding
        if not f:
            return

        log.write(f"[bold]Type:[/bold] {f.get('type')}")
        log.write(f"[bold]Severity:[/bold] {f.get('severity')}")
        log.write(f"[bold]File:[/bold] {f.get('file')}:{f.get('line')}")
        log.write(f"\n[bold]Description:[/bold]\n{f.get('description')}")

        snippet = f.get("snippet")
        if snippet:
            log.write("\n[bold]Snippet:[/bold]")
            # Try to guess language or default to python/text
            lang = "python"
            if str(f.get("file")).endswith(".json"): lang = "json"
            elif str(f.get("file")).endswith(".js"): lang = "javascript"

            log.write(Syntax(snippet, lang, theme="monokai"))

    def ignore_file(self) -> None:
        if not self.selected_finding:
            return

        file_path = self.selected_finding.get("file")
        if not file_path or file_path == "N/A":
            self.notify("Cannot ignore this finding (no file path).", severity="warning")
            return

        self.auditor.add_ignore_pattern(file_path)
        self.notify(f"Added {file_path} to .secretignore")

        # Refresh current scan
        # Ideally we'd just remove from table, but re-scanning ensures state consistency
        # But re-scanning might be slow. For now, let's just notify and user can re-scan.
        self.query_one("#sec-status-lbl").update("File ignored. Re-scan to update list.")

    def ignore_pattern(self) -> None:
        # TODO: Implement interactive pattern entry
        self.notify("Custom pattern ignore not implemented yet.", severity="warning")

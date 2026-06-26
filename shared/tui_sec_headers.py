from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual import on

from shared.sec_headers_lab import SecHeadersManager

class SecHeadersLabTab(Container):
    """
    Interactive Security Headers Lab Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SecHeadersManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Security Headers Analyzer[/bold]", classes="header text-bold")

            with Horizontal(id="sec-headers-input-row", classes="mb-1"):
                yield Input(placeholder="Enter URL (e.g., https://example.com)", id="sec-headers-url-input")
                yield Button("Analyze", id="btn-sec-headers-analyze", variant="primary")

            with Horizontal(id="sec-headers-summary-row", classes="mb-1 stat-box"):
                yield Label("Grade: -", id="lbl-sec-headers-grade", classes="text-bold")
                yield Label("Score: -", id="lbl-sec-headers-score")
                yield Label("Status: Ready", id="lbl-sec-headers-status")

            yield DataTable(id="sec-headers-table", cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one("#sec-headers-table", DataTable)
        table.add_columns("Header", "Status", "Value", "Description")

    @on(Button.Pressed, "#btn-sec-headers-analyze")
    async def on_analyze(self) -> None:
        url_input = self.query_one("#sec-headers-url-input", Input).value.strip()
        if not url_input:
            self.notify("Please enter a valid URL.", severity="warning")
            return

        status_label = self.query_one("#lbl-sec-headers-status", Label)
        grade_label = self.query_one("#lbl-sec-headers-grade", Label)
        score_label = self.query_one("#lbl-sec-headers-score", Label)
        table = self.query_one("#sec-headers-table", DataTable)
        analyze_btn = self.query_one("#btn-sec-headers-analyze", Button)

        status_label.update("Status: Analyzing...")
        analyze_btn.disabled = True
        table.clear()

        # We need to run the analysis in a separate thread so we don't block the UI
        import asyncio
        result = await asyncio.to_thread(self.manager.analyze_url, url_input)

        analyze_btn.disabled = False

        if "error" in result:
            status_label.update(f"[red]Error: {result['error']}[/red]")
            grade_label.update("Grade: -")
            score_label.update("Score: -")
            self.notify(f"Error fetching headers: {result['error']}", severity="error")
            return

        status_label.update("Status: Complete")

        # Update Grade and Score
        grade = result["grade"]
        score = result["score"]

        # Color coding for Grade
        grade_color = "green"
        if grade == "C" or grade == "D":
            grade_color = "yellow"
        elif grade == "F":
            grade_color = "red"

        grade_label.update(f"Grade: [{grade_color}][bold]{grade}[/bold][/{grade_color}]")
        score_label.update(f"Score: {score}/100")

        # Populate Table
        for header, details in result["details"].items():
            status = details["status"]
            val = details["value"] if details["value"] else "N/A"
            desc = details["description"]

            # Color coding for Status
            status_text = status
            if status == "Present":
                status_text = f"[green]{status}[/green]"
            elif status == "Missing":
                status_text = f"[red]{status}[/red]"
            elif status == "Warning":
                status_text = f"[yellow]{status}[/yellow]"

            table.add_row(header, status_text, val, desc)

    def notify(self, message: str, severity: str = "information", timeout: float = 3.0) -> None:
        if self.app:
            self.app.notify(message, severity=severity, timeout=timeout)

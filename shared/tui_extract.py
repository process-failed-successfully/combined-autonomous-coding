from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, TextArea, RichLog, TabPane
from shared.extract_lab import ExtractLabManager

class ExtractLabTab(TabPane):
    """TUI Tab for Extract Lab."""

    def __init__(self, **kwargs):
        super().__init__("Extract Lab", id="tab-extract", **kwargs)
        self.manager = ExtractLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Extract Lab (IoC Extractor)[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("Input Text:")
                yield TextArea(id="extract-input", placeholder="Paste text containing IPs, URLs, emails, hashes...", text="")

                with Horizontal():
                    yield Button("Extract IoCs", id="btn-extract", variant="primary")
                    yield Button("Clear", id="btn-extract-clear", variant="warning")

            with Vertical(classes="stat-box"):
                yield Label("[bold]Extracted Data[/bold]")
                yield RichLog(id="extract-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-extract-clear":
            self.query_one("#extract-input", TextArea).text = ""
            self.query_one("#extract-log", RichLog).clear()
        elif event.button.id == "btn-extract":
            await self.run_extraction()

    async def run_extraction(self) -> None:
        text_input = self.query_one("#extract-input", TextArea).text
        log_widget = self.query_one("#extract-log", RichLog)

        if not text_input.strip():
            log_widget.write("[red]Error: Input text cannot be empty.[/red]")
            return

        results = self.manager.extract_iocs(text_input)

        log_widget.clear()
        log_widget.write("[bold]Extraction Results:[/bold]")

        if results["ips"]:
            log_widget.write(f"\n[bold cyan]IPs ({len(results['ips'])}):[/bold cyan]")
            for ip in results["ips"]:
                log_widget.write(f"  - {ip}")

        if results["urls"]:
            log_widget.write(f"\n[bold green]URLs ({len(results['urls'])}):[/bold green]")
            for url in results["urls"]:
                log_widget.write(f"  - {url}")

        if results["emails"]:
            log_widget.write(f"\n[bold yellow]Emails ({len(results['emails'])}):[/bold yellow]")
            for email in results["emails"]:
                log_widget.write(f"  - {email}")

        if results["hashes"]:
            log_widget.write(f"\n[bold magenta]Hashes ({len(results['hashes'])}):[/bold magenta]")
            for h in results["hashes"]:
                log_widget.write(f"  - {h}")

        if not any(results.values()):
            log_widget.write("\n[yellow]No IoCs found in the provided text.[/yellow]")

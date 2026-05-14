from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, Button, Input, RichLog
from textual import on

try:
    from shared.favicon_lab import FaviconManager
    HAS_FAVICON_DEPS = True
except ImportError:
    HAS_FAVICON_DEPS = False


class FaviconLabTab(Container):
    """Tab for Favicon Generator Lab operations."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Favicon Lab[/bold]", classes="welcome-text")

            if not HAS_FAVICON_DEPS:
                yield Label("[red]Pillow library is missing. Please run `pip install Pillow` to use this feature.[/red]")
                return

            with Vertical(classes="stat-box"):
                yield Label("Input Image Path (PNG, JPG, etc.):")
                yield Input(placeholder="e.g., assets/logo.png", id="fl-input-image")

                yield Label("Output Directory:")
                yield Input(placeholder="e.g., ./public", id="fl-output-dir", value="./public")

                yield Button("Generate Favicons", id="btn-fl-generate", variant="primary")
                yield RichLog(id="fl-result", wrap=True, highlight=False, markup=True)

    @on(Button.Pressed, "#btn-fl-generate")
    def on_generate(self) -> None:
        input_str = self.query_one("#fl-input-image", Input).value.strip()
        out_str = self.query_one("#fl-output-dir", Input).value.strip()
        log = self.query_one("#fl-result", RichLog)
        log.clear()

        if not input_str:
            log.write("[bold red]Please provide an input image path.[/bold red]")
            return
        if not out_str:
            log.write("[bold red]Please provide an output directory.[/bold red]")
            return

        try:
            manager = FaviconManager()
            result = manager.generate(Path(input_str), Path(out_str))

            if result.get("success"):
                log.write(f"[bold green]Successfully generated favicons in '{result['output_dir']}'![/bold green]")
                for f in result.get("generated_files", []):
                    log.write(f"  - {f}")

                log.write("\n[bold]HTML Tags:[/bold]")
                html_tags = manager.get_html_tags()
                log.write(html_tags)
            else:
                log.write(f"[bold red]Error: {result.get('error')}[/bold red]")

        except Exception as e:
            log.write(f"[bold red]Unexpected Error: {e}[/bold red]")

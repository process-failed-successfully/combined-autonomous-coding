from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on

try:
    from shared.pdf_lab import PDFLabManager
except ImportError:
    PDFLabManager = None

class PdfLabTab(Container):
    """Tab for PDF operations."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = None
        self.error_msg = None
        try:
            if PDFLabManager:
                self.manager = PDFLabManager()
            else:
                self.error_msg = "PDFLabManager could not be imported."
        except ImportError as e:
            self.error_msg = str(e)
        except Exception as e:
            self.error_msg = f"Error initializing PDF Lab: {e}"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]PDF Lab[/bold]", classes="welcome-text")

            if self.error_msg:
                yield Label(f"[red]{self.error_msg}[/red]")
                return

            with Horizontal(classes="stat-box"):
                yield Label("PDF File:", classes="label")
                yield Input(placeholder="Path to PDF...", id="pdf-input")

            with Horizontal(classes="stat-box"):
                yield Button("Info", id="btn-pdf-info", variant="primary")
                yield Button("Extract Text", id="btn-pdf-text", variant="default")
                yield Button("Split", id="btn-pdf-split", variant="warning")

            yield Label("[bold]Output[/bold]")
            yield RichLog(id="pdf-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.manager:
            return

        file_path = self.query_one("#pdf-input", Input).value
        log = self.query_one("#pdf-log", RichLog)

        if not file_path:
            self.notify("Please enter a PDF file path.", severity="error")
            return

        path = self.project_dir / file_path
        if not path.exists():
             self.notify(f"File not found: {path}", severity="error")
             return

        if event.button.id == "btn-pdf-info":
            log.clear()
            log.write(f"[bold]Metadata for {path.name}[/bold]")
            try:
                info = self.manager.get_info(str(path))
                if info:
                    for k, v in info.items():
                        key = k[1:] if k.startswith('/') else k
                        log.write(f"{key}: {v}")
                else:
                    log.write("No metadata found.")
            except Exception as e:
                log.write(f"[red]Error: {e}[/red]")

        elif event.button.id == "btn-pdf-text":
            log.clear()
            log.write(f"[bold]Extracting text from {path.name}...[/bold]")
            try:
                text = self.manager.extract_text(str(path))
                log.write(text)
            except Exception as e:
                log.write(f"[red]Error: {e}[/red]")

        elif event.button.id == "btn-pdf-split":
            log.clear()
            log.write(f"[bold]Splitting {path.name}...[/bold]")
            output_dir = path.parent / f"{path.stem}_pages"
            try:
                files = self.manager.split_pdf(str(path), str(output_dir))
                log.write(f"[green]Split into {len(files)} pages in {output_dir}[/green]")
                for f in files:
                    log.write(f"  - {Path(f).name}")
            except Exception as e:
                log.write(f"[red]Error: {e}[/red]")

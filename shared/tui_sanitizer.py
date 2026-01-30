from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, DirectoryTree, RichLog, TabbedContent, TabPane, TextArea
from textual.containers import Container, Horizontal, Vertical
from textual import on
from rich.syntax import Syntax
import difflib

from shared.sanitizer import Sanitizer

class SanitizerTab(Container):
    """Tab for sanitizing PII from files and text."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.sanitizer = Sanitizer()
        self.selected_file = None
        self.sanitized_content = None

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("File Scan"):
                with Horizontal():
                    # Left: File Tree
                    with Vertical(id="san-tree-container", classes="stat-box"):
                        yield Label("[bold]Select File[/bold]")
                        yield DirectoryTree(str(self.project_dir), id="san-file-tree")

                    # Right: Preview & Actions
                    with Vertical(id="san-preview-container"):
                        yield Label("[bold]Sanitization Preview[/bold]")
                        yield RichLog(id="san-diff-log", wrap=True, highlight=True, markup=True)

                        with Horizontal(classes="stat-box"):
                            yield Button("Sanitize & Save", id="btn-san-save", variant="error", disabled=True)
                            yield Label("", id="san-status-lbl")

            with TabPane("Text Check"):
                with Vertical():
                    yield Label("Paste text to check for PII:")
                    yield TextArea(id="san-text-input")
                    with Horizontal(classes="stat-box"):
                        yield Button("Check Text", id="btn-san-check-text", variant="primary")
                        yield Button("Clear", id="btn-san-clear-text", variant="default")
                    yield Label("[bold]Result:[/bold]")
                    yield RichLog(id="san-text-result", wrap=True, highlight=True, markup=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        if event.path.is_file():
            self.selected_file = event.path
            self.check_file(event.path)
        else:
            self.selected_file = None
            self.query_one("#btn-san-save").disabled = True

    def check_file(self, path: Path) -> None:
        log = self.query_one("#san-diff-log", RichLog)
        log.clear()
        lbl = self.query_one("#san-status-lbl", Label)
        lbl.update("Checking...")

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            sanitized = self.sanitizer.sanitize_text(content)

            if content == sanitized:
                log.write("[green]No PII detected.[/green]")
                lbl.update("Clean.")
                self.query_one("#btn-san-save").disabled = True
                self.sanitized_content = None
            else:
                lbl.update("[red]PII Detected![/red]")
                self.sanitized_content = sanitized
                self.query_one("#btn-san-save").disabled = False

                # Generate diff
                diff = difflib.unified_diff(
                    content.splitlines(),
                    sanitized.splitlines(),
                    fromfile="Original",
                    tofile="Sanitized",
                    lineterm=""
                )
                diff_text = "\n".join(diff)
                log.write(Syntax(diff_text, "diff", theme="monokai"))

        except Exception as e:
            log.write(f"[red]Error reading file: {e}[/red]")
            lbl.update("Error.")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-san-save":
            self.save_file()
        elif event.button.id == "btn-san-check-text":
            self.check_text()
        elif event.button.id == "btn-san-clear-text":
            self.query_one("#san-text-input", TextArea).text = ""
            self.query_one("#san-text-result", RichLog).clear()

    def save_file(self) -> None:
        if not self.selected_file or self.sanitized_content is None:
            return

        try:
            self.selected_file.write_text(self.sanitized_content, encoding="utf-8")
            self.notify(f"Sanitized {self.selected_file.name}")
            # Re-check to confirm clean
            self.check_file(self.selected_file)
        except Exception as e:
            self.notify(f"Error saving file: {e}", severity="error")

    def check_text(self) -> None:
        text = self.query_one("#san-text-input", TextArea).text
        log = self.query_one("#san-text-result", RichLog)
        log.clear()

        if not text:
            log.write("No text provided.")
            return

        detected = self.sanitizer.check_text(text)
        if detected:
            log.write(f"[bold red]PII Detected:[/bold red] {', '.join(detected)}\n")
            sanitized = self.sanitizer.sanitize_text(text)
            log.write("[bold]Sanitized Version:[/bold]\n")
            log.write(sanitized)
        else:
            log.write("[green]No PII detected.[/green]")

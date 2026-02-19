from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Button, RichLog, Markdown, TabbedContent, TabPane, TextArea
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from shared.markdown_lab import MarkdownLabManager


class MarkdownLabTab(Container):
    """
    Interactive Markdown Editor Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = MarkdownLabManager()
        self.current_file: Optional[Path] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="md-sidebar", classes="stat-box"):
                yield Label("[bold]Markdown Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="md-file-tree")

            # Center: Editor
            with Vertical(id="md-editor-pane", classes="stat-box"):
                yield Label("[bold]Editor[/bold]")
                yield TextArea(id="md-editor", language="markdown")
                with Horizontal():
                    yield Button("Save", id="btn-md-save", variant="success", disabled=True)
                    yield Button("Preview >>", id="btn-md-preview", variant="primary", disabled=True)

            # Right: Tools & Preview
            with Vertical(id="md-tools-pane", classes="stat-box"):
                 with TabbedContent():
                    with TabPane("Preview"):
                        with VerticalScroll(id="md-preview-scroll"):
                            yield Markdown(id="md-preview")
                    with TabPane("Tools"):
                        yield Label("[bold]Markdown Tools[/bold]")
                        yield Button("Generate TOC", id="btn-md-toc", disabled=True)
                        yield Button("Format Tables", id="btn-md-table", disabled=True)
                        yield Button("Get Stats", id="btn-md-stats", disabled=True)
                        yield Button("Lint", id="btn-md-lint", variant="warning", disabled=True)
                        yield RichLog(id="md-tool-output", wrap=True, markup=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() == ".md":
            self.load_file(path)
        else:
            self.notify("Please select a .md file.", severity="warning")

    def load_file(self, path: Path) -> None:
        self.current_file = path
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            self.query_one("#md-editor", TextArea).text = content
            self.update_preview()
            self.enable_controls(True)
            self.log_message(f"Loaded {path.name}")
        except Exception as e:
            self.log_message(f"[red]Error loading file: {e}[/red]")
            self.enable_controls(False)

    def enable_controls(self, enable: bool) -> None:
        disabled = not enable
        self.query_one("#btn-md-save").disabled = disabled
        self.query_one("#btn-md-preview").disabled = disabled
        self.query_one("#btn-md-toc").disabled = disabled
        self.query_one("#btn-md-table").disabled = disabled
        self.query_one("#btn-md-stats").disabled = disabled
        self.query_one("#btn-md-lint").disabled = disabled

    def update_preview(self) -> None:
        content = self.query_one("#md-editor", TextArea).text
        self.query_one("#md-preview", Markdown).update(content)

    @on(Button.Pressed, "#btn-md-save")
    def on_save(self) -> None:
        if not self.current_file:
            return

        content = self.query_one("#md-editor", TextArea).text
        try:
            self.current_file.write_text(content, encoding="utf-8")
            self.log_message(f"[green]Saved {self.current_file.name}[/green]")
        except Exception as e:
            self.log_message(f"[red]Error saving file: {e}[/red]")

    @on(Button.Pressed, "#btn-md-preview")
    def on_preview_click(self) -> None:
        self.update_preview()
        self.log_message("Preview updated.")

    @on(Button.Pressed, "#btn-md-toc")
    def on_toc(self) -> None:
        editor = self.query_one("#md-editor", TextArea)
        text = editor.text
        toc = self.manager.generate_toc(text)
        if not toc:
            self.log_message("No headers found for TOC.")
            return

        # Insert TOC
        new_text = self.manager.insert_toc(text, toc)
        editor.text = new_text
        self.update_preview()
        self.log_message("TOC inserted/updated.")

    @on(Button.Pressed, "#btn-md-table")
    def on_table(self) -> None:
        editor = self.query_one("#md-editor", TextArea)
        text = editor.text
        formatted = self.manager.format_table(text)
        if formatted != text:
            editor.text = formatted
            self.update_preview()
            self.log_message("Tables formatted.")
        else:
            self.log_message("No table changes needed.")

    @on(Button.Pressed, "#btn-md-stats")
    def on_stats(self) -> None:
        text = self.query_one("#md-editor", TextArea).text
        stats = self.manager.get_stats(text)

        log = self.query_one("#md-tool-output", RichLog)
        log.write("[bold]Markdown Stats:[/bold]")
        for k, v in stats.items():
            log.write(f"  {k}: {v}")

    @on(Button.Pressed, "#btn-md-lint")
    def on_lint(self) -> None:
        text = self.query_one("#md-editor", TextArea).text
        # Pass file parent as root if available, else project dir
        root = self.current_file.parent if self.current_file else self.project_dir

        issues = self.manager.lint(text, root_dir=root)

        log = self.query_one("#md-tool-output", RichLog)
        log.clear()
        if not issues:
            log.write("[green]No linting issues found.[/green]")
        else:
            log.write(f"[red]Found {len(issues)} issues:[/red]")
            for issue in issues:
                log.write(f"  Line {issue['line']}: [{issue['type']}] {issue['message']}")

    def log_message(self, message: str) -> None:
        log = self.query_one("#md-tool-output", RichLog)
        log.write(message)

    def notify(self, message: str, severity: str = "information", timeout: float = 3.0) -> None:
        # Check if parent app supports notifications (standard textual App does)
        if self.app:
            self.app.notify(message, severity=severity, timeout=timeout)

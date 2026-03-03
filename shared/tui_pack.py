from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import TabPane, Button, Input, Select, TextArea, Label
from textual.containers import Vertical, Horizontal
from textual import on
from shared.pack_lab import PackManager


class PackLabTab(TabPane):
    """Tab for packing the codebase into a single text format."""

    def __init__(self, project_dir: Path, *args, **kwargs):
        super().__init__("Pack Lab", id="tab-pack", *args, **kwargs)
        self.project_dir = project_dir
        self.manager = PackManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical(classes="tab-content"):
            yield Label("Pack the codebase into a single file for LLM context.", classes="section-header")

            with Horizontal(classes="controls-row"):
                yield Label("Include (glob patterns, comma-separated):")
                yield Input(id="input-include", placeholder="e.g. *.py, *.md", value="")

            with Horizontal(classes="controls-row"):
                yield Label("Exclude (glob patterns, comma-separated):")
                yield Input(id="input-exclude", placeholder="e.g. tests/*", value="*.git*,node_modules/*,venv/*,.venv/*,env/*,__pycache__/*,*.egg-info/*")

            with Horizontal(classes="controls-row"):
                yield Label("Format:")
                yield Select(
                    [("Markdown", "markdown"), ("XML", "xml")],
                    value="markdown",
                    id="select-format"
                )

            with Horizontal(classes="button-row"):
                yield Button("Pack", id="btn-pack", variant="primary")
                yield Button("Copy to Clipboard", id="btn-copy", variant="success")
                yield Button("Clear", id="btn-clear", variant="error")

            yield Label("Preview:", classes="section-header")
            yield TextArea(id="text-preview", read_only=True, classes="tall-textarea")

    @on(Button.Pressed, "#btn-pack")
    def on_pack_pressed(self) -> None:
        include_str = self.query_one("#input-include", Input).value
        exclude_str = self.query_one("#input-exclude", Input).value
        format_val = self.query_one("#select-format", Select).value

        include_patterns = [p.strip() for p in include_str.split(",")] if include_str else None
        exclude_patterns = [p.strip() for p in exclude_str.split(",")] if exclude_str else None

        try:
            files = self.manager.get_files(include_patterns=include_patterns, exclude_patterns=exclude_patterns)

            if not files:
                self.app.notify("No files found to pack.", severity="warning")
                self.query_one("#text-preview", TextArea).text = "No files found."
                return

            packed_content = self.manager.pack(files, format=format_val)
            self.query_one("#text-preview", TextArea).text = packed_content
            self.app.notify(f"Successfully packed {len(files)} files.", severity="information")
        except Exception as e:
            self.app.notify(f"Error packing codebase: {e}", severity="error")

    @on(Button.Pressed, "#btn-copy")
    def on_copy_pressed(self) -> None:
        content = self.query_one("#text-preview", TextArea).text
        if not content:
            self.app.notify("Nothing to copy.", severity="warning")
            return

        try:
            self.app.copy_to_clipboard(content)
            self.app.notify("Packed content copied to clipboard!", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to copy to clipboard: {e}", severity="error")

    @on(Button.Pressed, "#btn-clear")
    def on_clear_pressed(self) -> None:
        self.query_one("#text-preview", TextArea).text = ""
        self.app.notify("Preview cleared.", severity="information")

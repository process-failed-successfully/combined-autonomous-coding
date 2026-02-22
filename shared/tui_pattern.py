from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Label, ListView, ListItem, Select, Static
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from rich.syntax import Syntax

from shared.pattern_lab import PatternLabManager

class PatternLabTab(Container):
    """Tab for Design Patterns."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = PatternLabManager()
        self.selected_pattern = None
        self.selected_language = "python" # Default

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Pattern List
            with Vertical(id="pattern-list-container", classes="stat-box"):
                yield Label("[bold]Design Patterns[/bold]")
                yield ListView(id="pattern-list")

                yield Label("Language:")
                yield Select.from_values(self.manager.list_languages(), id="pattern-lang-select", value="python")

            # Right Pane: Preview & Actions
            with Vertical(id="pattern-details-container"):
                yield Label("[bold]Pattern Preview[/bold]", id="pattern-header")

                # Using VerticalScroll for code preview
                with VerticalScroll(id="pattern-preview-scroll"):
                    yield Static(id="pattern-code-preview")

                with Horizontal(id="pattern-actions", classes="stat-box"):
                    yield Button("Copy to Clipboard", id="btn-pattern-copy", variant="primary", disabled=True)
                    # Future: Save to file button (requires file dialog or input)

    def on_mount(self) -> None:
        self.load_patterns()

    def load_patterns(self) -> None:
        list_view = self.query_one("#pattern-list", ListView)
        list_view.clear()

        patterns = self.manager.list_patterns()
        for p in patterns:
            list_view.append(ListItem(Label(p), name=p))

    @on(ListView.Selected, "#pattern-list")
    def on_pattern_selected(self, event: ListView.Selected) -> None:
        # Get pattern name from ListItem name attribute (set in load_patterns)
        if event.item and hasattr(event.item, "name"):
            self.selected_pattern = event.item.name
            self.update_preview()
            self.query_one("#btn-pattern-copy").disabled = False

    @on(Select.Changed, "#pattern-lang-select")
    def on_language_changed(self, event: Select.Changed) -> None:
        self.selected_language = event.value
        self.update_preview()

    def update_preview(self) -> None:
        preview = self.query_one("#pattern-code-preview", Static)
        header = self.query_one("#pattern-header", Label)

        if not self.selected_pattern:
            preview.update("Select a pattern.")
            header.update("[bold]Pattern Preview[/bold]")
            return

        header.update(f"[bold]{self.selected_pattern} ({self.selected_language})[/bold]")

        code = self.manager.get_template(self.selected_pattern, self.selected_language)

        if code:
            syntax = Syntax(code, self.selected_language, theme="monokai", line_numbers=True)
            preview.update(syntax)
        else:
            preview.update(f"[yellow]Pattern not available in {self.selected_language}.[/yellow]")

    @on(Button.Pressed, "#btn-pattern-copy")
    def on_copy(self) -> None:
        if not self.selected_pattern:
            return

        code = self.manager.get_template(self.selected_pattern, self.selected_language)
        if code:
            # In a real desktop app we would put to clipboard.
            # In TUI/Remote, we just notify.
            self.notify(f"Copied {self.selected_pattern} to clipboard (simulated).")
            # Also printing to console could be useful if running locally?
            # No, user is in TUI.

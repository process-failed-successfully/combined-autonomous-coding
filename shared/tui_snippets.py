from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, ListView, ListItem, Input, Button, TextArea
from textual import on
from shared.snippets import SnippetManager

class SnippetsTab(Container):
    """Tab for managing code snippets."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SnippetManager(project_dir)
        self.selected_snippet = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane
            with Vertical(id="snippets-list-container", classes="stat-box"):
                yield Label("[bold]Snippets[/bold]")
                yield ListView(id="snippets-list")
                with Horizontal():
                    yield Input(placeholder="New snippet name...", id="snippet-new-name")
                    yield Button("Create", id="btn-snippet-create", variant="primary")
                yield Button("Refresh", id="btn-snippet-refresh", variant="default")

            # Right Pane
            with Vertical(id="snippet-details-container"):
                yield Label("[bold]Content[/bold]")
                yield TextArea(id="snippet-editor", language="python") # Default to python, maybe auto-detect later

                with Horizontal(id="snippet-actions"):
                    yield Button("Save", id="btn-snippet-save", variant="success", disabled=True)
                    yield Button("Apply to File", id="btn-snippet-apply", variant="warning", disabled=True)
                    yield Button("Delete", id="btn-snippet-delete", variant="error", disabled=True)

                with Horizontal():
                     yield Input(placeholder="Target file path...", id="snippet-target-file")

    def on_mount(self) -> None:
        self.load_snippets()

    def load_snippets(self) -> None:
        list_view = self.query_one("#snippets-list", ListView)
        list_view.clear()

        snippets = self.manager.list_snippets()
        for name in snippets:
            # We must monkey-patch the name onto the item because standard ListItem doesn't hold data
            item = ListItem(Label(name))
            item.name = name
            list_view.append(item)

    @on(ListView.Selected, "#snippets-list")
    def on_snippet_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "name"):
            self.selected_snippet = event.item.name
            self.load_content(self.selected_snippet)

            # Enable buttons
            self.query_one("#btn-snippet-save").disabled = False
            self.query_one("#btn-snippet-apply").disabled = False
            self.query_one("#btn-snippet-delete").disabled = False

    def load_content(self, name: str) -> None:
        content = self.manager.get_snippet(name)
        editor = self.query_one("#snippet-editor", TextArea)
        if content is not None:
            editor.text = content
        else:
            editor.text = ""

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-snippet-refresh":
            self.load_snippets()
        elif event.button.id == "btn-snippet-create":
            self.create_snippet()
        elif event.button.id == "btn-snippet-save":
            self.save_snippet()
        elif event.button.id == "btn-snippet-delete":
            self.delete_snippet()
        elif event.button.id == "btn-snippet-apply":
            self.apply_snippet()

    def create_snippet(self) -> None:
        inp = self.query_one("#snippet-new-name", Input)
        name = inp.value
        if not name:
            self.notify("Name required.", severity="error")
            return

        self.manager.create_snippet(name, "")
        self.notify(f"Snippet '{name}' created.")
        inp.value = ""
        self.load_snippets()

    def save_snippet(self) -> None:
        if not self.selected_snippet:
            return

        editor = self.query_one("#snippet-editor", TextArea)
        content = editor.text
        self.manager.create_snippet(self.selected_snippet, content)
        self.notify("Snippet saved.")

    def delete_snippet(self) -> None:
        if not self.selected_snippet:
            return

        self.manager.delete_snippet(self.selected_snippet)
        self.notify(f"Deleted '{self.selected_snippet}'")
        self.selected_snippet = None
        self.query_one("#snippet-editor", TextArea).text = ""
        self.load_snippets()

        self.query_one("#btn-snippet-save").disabled = True
        self.query_one("#btn-snippet-apply").disabled = True
        self.query_one("#btn-snippet-delete").disabled = True

    def apply_snippet(self) -> None:
        if not self.selected_snippet:
            return

        target_inp = self.query_one("#snippet-target-file", Input)
        target_path = target_inp.value
        if not target_path:
            self.notify("Target file path required.", severity="error")
            return

        full_path = self.project_dir / target_path

        if self.manager.apply_snippet(self.selected_snippet, full_path):
            self.notify(f"Applied to {target_path}")
        else:
            self.notify("Error applying snippet.", severity="error")

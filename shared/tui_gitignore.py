from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, ListView, ListItem, TextArea, Input, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.gitignore_lab import GitignoreManager

class GitignoreTab(Container):
    """Tab for managing .gitignore files."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = GitignoreManager(project_dir)

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Templates
            with Vertical(id="gitignore-templates-container", classes="stat-box"):
                yield Label("[bold]Templates[/bold]")
                yield ListView(id="gitignore-template-list")
                yield Button("Append Selected", id="btn-gitignore-append", variant="primary")

            # Center Pane: Editor
            with Vertical(id="gitignore-editor-container"):
                yield Label("[bold].gitignore Editor[/bold]")
                yield TextArea(id="gitignore-editor", language="bash") # bash syntax highlighting is close enough
                yield Button("Save File", id="btn-gitignore-save", variant="success")

            # Right Pane: Check
            with Vertical(id="gitignore-check-container", classes="stat-box"):
                yield Label("[bold]Check Ignore[/bold]")
                yield Input(placeholder="Path to check...", id="gitignore-check-input")
                yield Button("Check", id="btn-gitignore-check", variant="warning")
                yield Label("[bold]Result[/bold]")
                yield RichLog(id="gitignore-check-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.load_templates()
        self.load_file()

    def load_templates(self) -> None:
        list_view = self.query_one("#gitignore-template-list", ListView)
        list_view.clear()
        templates = self.manager.list_templates()
        for tpl in templates:
            # Storing template name in ListItem via monkey-patching or subclass is common in this repo's patterns
            item = ListItem(Label(tpl))
            item.template_name = tpl
            list_view.append(item)

    def load_file(self) -> None:
        editor = self.query_one("#gitignore-editor", TextArea)
        gitignore_path = self.project_dir / ".gitignore"
        if gitignore_path.exists():
            try:
                content = gitignore_path.read_text(encoding="utf-8")
                editor.text = content
            except Exception as e:
                self.notify(f"Error reading .gitignore: {e}", severity="error")
        else:
            editor.text = "# .gitignore\n"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-gitignore-append":
            self.append_template()
        elif event.button.id == "btn-gitignore-save":
            self.save_file()
        elif event.button.id == "btn-gitignore-check":
            await self.check_ignore()

    def append_template(self) -> None:
        list_view = self.query_one("#gitignore-template-list", ListView)
        if list_view.index is None:
            self.notify("No template selected.", severity="warning")
            return

        item = list_view.children[list_view.index]
        if not hasattr(item, "template_name"):
            return

        name = item.template_name
        content = self.manager.get_template(name)
        if content:
            editor = self.query_one("#gitignore-editor", TextArea)
            # Append to editor text
            current_text = editor.text
            if current_text and not current_text.endswith("\n"):
                current_text += "\n"

            editor.text = current_text + f"\n# Template: {name}\n{content}\n"
            self.notify(f"Appended '{name}' template.")
        else:
            self.notify(f"Template '{name}' not found.", severity="error")

    def save_file(self) -> None:
        editor = self.query_one("#gitignore-editor", TextArea)
        content = editor.text
        gitignore_path = self.project_dir / ".gitignore"
        try:
            gitignore_path.write_text(content, encoding="utf-8")
            self.notify(".gitignore saved.")
        except Exception as e:
            self.notify(f"Error saving .gitignore: {e}", severity="error")

    async def check_ignore(self) -> None:
        path = self.query_one("#gitignore-check-input", Input).value
        if not path:
            self.notify("Path required.", severity="error")
            return

        log = self.query_one("#gitignore-check-log", RichLog)
        log.clear()
        log.write(f"Checking '{path}'...")

        import asyncio
        # Run in thread since it calls subprocess
        result = await asyncio.to_thread(self.manager.check_ignore, path)

        if result["ignored"] == "yes":
            log.write(f"[bold red]IGNORED[/bold red]")
            log.write(result["details"])
        elif result["ignored"] == "no":
            log.write(f"[bold green]NOT IGNORED[/bold green]")
        else:
            log.write(f"[bold orange]ERROR[/bold orange]: {result['message']}")

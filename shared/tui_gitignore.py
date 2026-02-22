from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, ListView, ListItem, TextArea, Input
from textual import on
from shared.gitignore_lab import GitignoreManager

class GitignoreLabTab(Container):
    """Tab for managing .gitignore files."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = GitignoreManager(project_dir)
        self.selected_template = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Template List
            with Vertical(id="gitignore-list-container", classes="stat-box"):
                yield Label("[bold]Templates[/bold]")
                yield ListView(id="gitignore-template-list")
                yield Button("Refresh", id="btn-gitignore-refresh", variant="default")

            # Center Pane: Preview & Actions
            with Vertical(id="gitignore-preview-container"):
                yield Label("[bold]Template Preview[/bold]")
                yield TextArea(id="gitignore-preview", language="gitignore", read_only=True)

                with Horizontal(classes="stat-box"):
                    yield Button("Append to .gitignore", id="btn-gitignore-append", variant="primary", disabled=True)
                    yield Button("Overwrite .gitignore", id="btn-gitignore-overwrite", variant="warning", disabled=True)

            # Right Pane: Check Ignore
            with Vertical(id="gitignore-check-container", classes="stat-box"):
                yield Label("[bold]Check Ignore Status[/bold]")
                yield Input(placeholder="Path to check...", id="gitignore-check-input")
                yield Button("Check", id="btn-gitignore-check", variant="primary")
                yield TextArea(id="gitignore-check-output", read_only=True)

    def on_mount(self) -> None:
        self.load_templates()

    def load_templates(self) -> None:
        list_view = self.query_one("#gitignore-template-list", ListView)
        list_view.clear()

        templates = self.manager.list_templates()
        for name in templates:
            list_view.append(ListItem(Label(name), name=name))

    @on(ListView.Selected, "#gitignore-template-list")
    def on_template_selected(self, event: ListView.Selected) -> None:
        if event.item and event.item.name:
            self.selected_template = event.item.name
            self.show_preview(self.selected_template)

            self.query_one("#btn-gitignore-append").disabled = False
            self.query_one("#btn-gitignore-overwrite").disabled = False

    def show_preview(self, name: str) -> None:
        content = self.manager.get_template(name)
        preview = self.query_one("#gitignore-preview", TextArea)
        if content:
            preview.text = content
        else:
            preview.text = "# Error: Template not found."

    @on(Button.Pressed, "#btn-gitignore-refresh")
    def on_refresh(self) -> None:
        self.load_templates()
        self.notify("Templates refreshed.")

    @on(Button.Pressed, "#btn-gitignore-append")
    def on_append(self) -> None:
        if not self.selected_template:
            return

        if self.manager.append([self.selected_template]):
            self.notify(f"Appended '{self.selected_template}' to .gitignore.")
        else:
            self.notify("Failed to append to .gitignore.", severity="error")

    @on(Button.Pressed, "#btn-gitignore-overwrite")
    def on_overwrite(self) -> None:
        if not self.selected_template:
            return

        btn = self.query_one("#btn-gitignore-overwrite", Button)

        # Two-step confirmation
        if str(btn.label) != "Confirm Overwrite?":
            btn.label = "Confirm Overwrite?"
            btn.variant = "error"
            self.set_timer(3.0, self.reset_overwrite_button)
            return

        # Overwrite logic is not directly in manager.append, let's implement it here manually or use generate
        content = self.manager.generate([self.selected_template])
        gitignore_path = self.project_dir / ".gitignore"
        try:
            with open(gitignore_path, "w") as f:
                f.write(content + "\n")
            self.notify(f"Overwritten .gitignore with '{self.selected_template}'.")
        except IOError as e:
            self.notify(f"Error overwriting .gitignore: {e}", severity="error")

        self.reset_overwrite_button()

    def reset_overwrite_button(self) -> None:
        try:
            btn = self.query_one("#btn-gitignore-overwrite", Button)
            btn.label = "Overwrite .gitignore"
            btn.variant = "warning"
        except Exception:
            pass  # Widget might be unmounted

    @on(Button.Pressed, "#btn-gitignore-check")
    async def on_check(self) -> None:
        await self.check_ignore()

    @on(Input.Submitted, "#gitignore-check-input")
    async def on_check_submit(self) -> None:
        await self.check_ignore()

    async def check_ignore(self) -> None:
        path = self.query_one("#gitignore-check-input", Input).value
        output_area = self.query_one("#gitignore-check-output", TextArea)

        if not path:
            self.notify("Path required.", severity="warning")
            return

        import asyncio
        # Run in thread as check_ignore uses subprocess
        result = await asyncio.to_thread(self.manager.check_ignore, path)

        msg = result["message"]
        details = result["details"]

        output_text = f"{msg}\n\n{details}" if details else msg
        output_area.text = output_text

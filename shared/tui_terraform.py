import json
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, RichLog, ListView, ListItem, Tree, TabbedContent, TabPane
from textual.screen import Screen
from textual import on
from shared.terraform_lab import TerraformManager

class ConfirmationScreen(Screen):
    """A screen for confirming destructive actions."""

    CSS = """
    ConfirmationScreen {
        align: center middle;
    }
    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }
    #question {
        column-span: 2;
        height: 1fr;
        content-align: center middle;
    }
    .buttons {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Are you sure you want to DESTROY all infrastructure?", id="question")
            with Horizontal(classes="buttons"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Destroy", variant="error", id="confirm")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

class TerraformTab(Container):
    """Tab for Terraform operations."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TerraformManager(working_dir=project_dir)

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Files & Actions
            with Vertical(id="tf-controls-container", classes="stat-box"):
                yield Label("[bold]Terraform Files[/bold]")
                yield ListView(id="tf-file-list")

                yield Label("[bold]Actions[/bold]")
                with Vertical():
                    yield Button("Init", id="btn-tf-init", variant="primary")
                    yield Button("Plan", id="btn-tf-plan", variant="warning")
                    yield Button("Apply", id="btn-tf-apply", variant="success")
                    yield Button("Destroy", id="btn-tf-destroy", variant="error")
                    yield Button("Validate", id="btn-tf-validate", variant="default")
                    yield Button("Fmt", id="btn-tf-fmt", variant="default")
                    yield Button("Refresh State", id="btn-tf-refresh", variant="primary")

            # Center Pane: Output & State
            with Vertical(id="tf-output-container"):
                with TabbedContent():
                    with TabPane("Output"):
                        yield RichLog(id="tf-log", wrap=True, highlight=True, markup=True)
                    with TabPane("State Explorer"):
                        yield Tree("Resources", id="tf-state-tree")

    def on_mount(self) -> None:
        self.load_files()
        self.load_state()

    def load_files(self) -> None:
        list_view = self.query_one("#tf-file-list", ListView)
        list_view.clear()

        # List .tf files
        tf_files = sorted(list(self.project_dir.glob("*.tf")))
        if not tf_files:
            list_view.append(ListItem(Label("No .tf files found")))
        else:
            for f in tf_files:
                list_view.append(ListItem(Label(f.name)))

    def log(self, message: str) -> None:
        log_view = self.query_one("#tf-log", RichLog)
        log_view.write(message)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-tf-init":
            await self.run_command("init", self.manager.init)
        elif event.button.id == "btn-tf-plan":
            await self.run_command("plan", self.manager.plan)
        elif event.button.id == "btn-tf-apply":
            await self.run_command("apply", self.manager.apply, auto_approve=True)
        elif event.button.id == "btn-tf-destroy":
            # Push confirmation screen
            self.app.push_screen(ConfirmationScreen(), self.on_destroy_confirmed)
        elif event.button.id == "btn-tf-validate":
            await self.run_command("validate", self.manager.validate)
        elif event.button.id == "btn-tf-fmt":
            await self.run_command("fmt", self.manager.fmt)
        elif event.button.id == "btn-tf-refresh":
            self.load_state()

    async def on_destroy_confirmed(self, confirmed: bool) -> None:
        if confirmed:
            await self.run_command("destroy", self.manager.destroy, auto_approve=True)
        else:
            self.log("Destroy cancelled.")

    async def run_command(self, name: str, func, **kwargs) -> None:
        self.log(f"[bold]Running terraform {name}...[/bold]")
        import asyncio

        try:
            success = await asyncio.to_thread(func, **kwargs)

            if success:
                self.log(f"[green]terraform {name} succeeded.[/green]")
                self.notify(f"terraform {name} succeeded.")
                if name in ["apply", "destroy", "init"]:
                    self.load_state()
            else:
                self.log(f"[red]terraform {name} failed.[/red]")
                self.notify(f"terraform {name} failed.", severity="error")

        except Exception as e:
            self.log(f"[red]Error: {e}[/red]")

    def load_state(self) -> None:
        tree = self.query_one("#tf-state-tree", Tree)
        tree.clear()
        tree.root.expand()

        import asyncio
        asyncio.create_task(self._load_state_async(tree))

    async def _load_state_async(self, tree: Tree) -> None:
        import asyncio
        try:
            output = await asyncio.to_thread(self.manager.show, json_format=True)
            if not output:
                tree.root.add("No state or terraform not initialized.")
                return

            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                tree.root.add("[red]Invalid JSON output from terraform show[/red]")
                return

            values = data.get("values", {})
            if not values:
                tree.root.add("State is empty.")
                return

            root_module = values.get("root_module", {})
            self._add_resources_to_tree(tree.root, root_module)

        except Exception as e:
            tree.root.add(f"[red]Error loading state: {e}[/red]")

    def _add_resources_to_tree(self, parent_node, module_data) -> None:
        # Add resources
        resources = module_data.get("resources", [])
        for res in resources:
            name = res.get("name", "unknown")
            rtype = res.get("type", "unknown")

            node_label = f"[blue]{rtype}[/blue] [bold]{name}[/bold]"
            res_node = parent_node.add(node_label, expand=False)

            # Add attributes as children
            values = res.get("values", {})
            for k, v in values.items():
                if isinstance(v, (str, int, bool, float)) or v is None:
                    res_node.add(f"[dim]{k}: {v}[/dim]")
                elif isinstance(v, dict):
                    res_node.add(f"[dim]{k}: {{...}}[/dim]")
                elif isinstance(v, list):
                    res_node.add(f"[dim]{k}: [[...]][/dim]")

        # Recurse into child modules
        child_modules = module_data.get("child_modules", [])
        for child in child_modules:
            addr = child.get("address", "module")
            child_node = parent_node.add(f"[magenta]Module: {addr}[/magenta]")
            self._add_resources_to_tree(child_node, child)

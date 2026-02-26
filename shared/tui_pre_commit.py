from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, RichLog, TextArea, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual import on
import asyncio

from shared.pre_commit_lab import PreCommitLabManager

class PreCommitLabTab(Container):
    """Tab for managing pre-commit hooks."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = PreCommitLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Pre-commit Lab[/bold]", classes="welcome-text")

            # Status Section
            with Container(classes="stat-box"):
                with Horizontal():
                    yield Label("Tool Status: ", id="pc-tool-status")
                    yield Button("Install pre-commit", id="btn-pc-install-tool", variant="warning", disabled=True)

                with Horizontal():
                    yield Label("Config Status: ", id="pc-config-status")
                    yield Button("Create Config", id="btn-pc-create-config", variant="primary", disabled=True)

            # Controls & Hooks
            with TabbedContent():
                with TabPane("Hooks"):
                    with Horizontal(classes="stat-box"):
                        yield Button("Install Hooks", id="btn-pc-install-hooks", variant="success")
                        yield Button("Run All Hooks", id="btn-pc-run-all", variant="primary")
                        yield Button("Autoupdate", id="btn-pc-autoupdate", variant="warning")
                        yield Button("Refresh", id="btn-pc-refresh", variant="default")

                    yield DataTable(id="pc-hooks-table")

                with TabPane("Configuration"):
                    with Vertical():
                        with Horizontal(classes="stat-box"):
                            yield Button("Save Config", id="btn-pc-save-config", variant="success")
                            yield Button("Reload Config", id="btn-pc-reload-config", variant="default")
                        yield TextArea(id="pc-config-editor", language="yaml")

                with TabPane("Output Log"):
                    yield RichLog(id="pc-output-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.check_status()

        # Init table
        table = self.query_one("#pc-hooks-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Hook ID", "Repository", "Revision")
        self.load_hooks()

    def check_status(self) -> None:
        # Tool Status
        tool_lbl = self.query_one("#pc-tool-status", Label)
        install_btn = self.query_one("#btn-pc-install-tool", Button)

        if self.manager.is_installed():
            tool_lbl.update("Tool Status: [green]Installed[/green]")
            install_btn.disabled = True
        else:
            tool_lbl.update("Tool Status: [red]Not Installed[/red]")
            install_btn.disabled = False

        # Config Status
        cfg_lbl = self.query_one("#pc-config-status", Label)
        create_btn = self.query_one("#btn-pc-create-config", Button)

        if self.manager.config_exists():
            cfg_lbl.update("Config Status: [green]Found[/green]")
            create_btn.disabled = True
            # Load config into editor
            self.load_config_editor()
        else:
            cfg_lbl.update("Config Status: [red]Missing[/red]")
            create_btn.disabled = False
            self.query_one("#pc-config-editor", TextArea).text = ""

    def load_hooks(self) -> None:
        table = self.query_one("#pc-hooks-table", DataTable)
        table.clear()

        hooks = self.manager.get_hooks()
        for hook in hooks:
            table.add_row(
                hook["id"],
                hook["repo"],
                hook["rev"]
            )

    def load_config_editor(self) -> None:
        content = self.manager.get_config_content()
        self.query_one("#pc-config-editor", TextArea).text = content

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pc-install-tool":
            await self.install_tool()
        elif event.button.id == "btn-pc-create-config":
            self.create_config()
        elif event.button.id == "btn-pc-install-hooks":
            await self.run_command("install_hooks", "Installing hooks...")
        elif event.button.id == "btn-pc-run-all":
            await self.run_command("run_all_hooks", "Running all hooks...")
        elif event.button.id == "btn-pc-autoupdate":
            await self.run_command("autoupdate_hooks", "Updating hooks...")
        elif event.button.id == "btn-pc-refresh":
            self.check_status()
            self.load_hooks()
            self.notify("Refreshed.")
        elif event.button.id == "btn-pc-save-config":
            self.save_config()
        elif event.button.id == "btn-pc-reload-config":
            self.load_config_editor()
            self.notify("Config reloaded.")

    async def install_tool(self) -> None:
        self.notify("Installing pre-commit...")
        success = await asyncio.to_thread(self.manager.install)
        if success:
            self.notify("pre-commit installed.")
            self.check_status()
        else:
            self.notify("Failed to install pre-commit.", severity="error")

    def create_config(self) -> None:
        if self.manager.create_default_config():
            self.notify("Config created.")
            self.check_status()
            self.load_hooks()
        else:
            self.notify("Failed to create config.", severity="error")

    def save_config(self) -> None:
        content = self.query_one("#pc-config-editor", TextArea).text
        if self.manager.save_config_content(content):
            self.notify("Config saved.")
            self.load_hooks()
        else:
            self.notify("Failed to save config.", severity="error")

    async def run_command(self, method_name: str, message: str) -> None:
        log = self.query_one("#pc-output-log", RichLog)
        log.clear()
        log.write(f"[bold]{message}[/bold]")
        self.notify(message)

        method = getattr(self.manager, method_name)

        success, output = await asyncio.to_thread(method)

        if success:
            log.write("[green]Success[/green]")
        else:
            log.write("[red]Failed[/red]")
            self.notify("Operation failed.", severity="error")

        log.write(output)

        # If autoupdate, refresh hooks
        if method_name == "autoupdate_hooks" and success:
            self.load_hooks()
            self.load_config_editor()

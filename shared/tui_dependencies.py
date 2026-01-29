import asyncio
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox, DataTable, Input, Label

from shared.dependencies import DependencyAnalyzer, DependencyUpdater


class DependenciesTab(Container):
    """Tab for managing dependencies."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.analyzer = DependencyAnalyzer(project_dir)
        self.updater = DependencyUpdater(project_dir)
        self.selected_pkg = None
        self.selected_ver = None
        self.selected_file_source = None
        self.selected_dep_type = "prod"
        self.selected_latest = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Project Dependencies[/bold]", classes="welcome-text")

            # Add Package Section
            with Horizontal(classes="stat-box"):
                yield Label("Add:")
                yield Input(placeholder="Name...", id="deps-input-name")
                yield Input(placeholder="Version...", id="deps-input-version")
                yield Checkbox("Dev", id="deps-chk-dev")
                yield Button("Install", id="btn-deps-add", variant="success")

            yield DataTable(id="deps-table")

            with Horizontal(classes="stat-box"):
                yield Button("Refresh", id="btn-deps-refresh", variant="default")
                yield Button("Check Updates", id="btn-deps-check", variant="primary")
                yield Button("Upgrade Selected", id="btn-deps-upgrade", variant="warning", disabled=True)
                yield Button("Remove Selected", id="btn-deps-remove", variant="error", disabled=True)

            yield Label("", id="deps-status")

    def on_mount(self) -> None:
        table = self.query_one("#deps-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Language", "Package", "Version", "Type", "Latest", "Status", "Source")
        self.load_deps()

    def load_deps(self) -> None:
        table = self.query_one("#deps-table", DataTable)
        table.clear()

        try:
            data = self.analyzer.scan()

            # Python
            for file_info in data.get("python", []):
                src = file_info["source"]
                for dep in file_info.get("dependencies", []):
                    table.add_row(
                        "Python",
                        dep["name"],
                        dep.get("version", ""),
                        "prod",
                        dep.get("latest", "-"),
                        "Outdated" if dep.get("outdated") else "OK",
                        src,
                        key=f"python|{dep['name']}|{src}"
                    )

            # Node
            for file_info in data.get("node", []):
                src = file_info["source"]
                for dep in file_info.get("dependencies", []):
                    table.add_row(
                        "Node",
                        dep["name"],
                        dep.get("version", ""),
                        dep.get("type", "prod"),
                        dep.get("latest", "-"),
                        "Outdated" if dep.get("outdated") else "OK",
                        src,
                        key=f"node|{dep['name']}|{src}"
                    )

            self.query_one("#deps-status", Label).update("Dependencies loaded.")
        except Exception as e:
            self.notify(f"Error loading dependencies: {e}", severity="error")

    @on(DataTable.RowSelected, "#deps-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        # Key format: lang|name|source
        key = event.row_key.value
        try:
            lang, name, src = key.split("|", 2)
            self.selected_pkg = name
            self.selected_file_source = src

            # Get row data to find current version and type
            row = self.query_one("#deps-table", DataTable).get_row(event.row_key)
            # row is [Language, Package, Version, Type, Latest, Status, Source]
            self.selected_ver = row[2]
            self.selected_dep_type = row[3]  # "prod" or "dev"

            latest = row[4]
            status = str(row[5])  # might contain markup

            self.query_one("#btn-deps-remove").disabled = False

            # Enable upgrade if outdated
            if "Outdated" in status and latest != "-":
                self.query_one("#btn-deps-upgrade").disabled = False
                self.query_one("#btn-deps-upgrade").label = f"Upgrade to {latest}"
                self.selected_latest = latest
            else:
                self.query_one("#btn-deps-upgrade").disabled = True
                self.query_one("#btn-deps-upgrade").label = "Upgrade Selected"

        except Exception:
            self.selected_pkg = None
            self.query_one("#btn-deps-remove").disabled = True
            self.query_one("#btn-deps-upgrade").disabled = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-deps-refresh":
            self.load_deps()
            self.notify("Dependencies refreshed.")
        elif event.button.id == "btn-deps-check":
            await self.check_updates()
        elif event.button.id == "btn-deps-add":
            await self.add_package()
        elif event.button.id == "btn-deps-remove":
            await self.remove_package()
        elif event.button.id == "btn-deps-upgrade":
            await self.upgrade_package()

    async def add_package(self) -> None:
        name = self.query_one("#deps-input-name", Input).value
        version = self.query_one("#deps-input-version", Input).value
        dev = self.query_one("#deps-chk-dev", Checkbox).value

        if not name:
            self.notify("Package name required.", severity="error")
            return

        self.notify(f"Installing {name}...", severity="information")
        self.query_one("#deps-status", Label).update(f"Installing {name}...")

        success = await asyncio.to_thread(
            self.updater.add_package,
            name,
            version if version else None,
            dev
        )

        if success:
            self.notify(f"Package '{name}' installed.")
            self.query_one("#deps-input-name", Input).value = ""
            self.query_one("#deps-input-version", Input).value = ""
            self.load_deps()
        else:
            self.notify(f"Failed to install '{name}'. Check logs.", severity="error")
            self.query_one("#deps-status", Label).update("Installation failed.")

    async def remove_package(self) -> None:
        if not self.selected_pkg:
            return

        name = self.selected_pkg
        dev = (self.selected_dep_type == "dev")

        self.notify(f"Removing {name}...", severity="information")
        self.query_one("#deps-status", Label).update(f"Removing {name}...")

        success = await asyncio.to_thread(self.updater.remove_package, name, dev)

        if success:
            self.notify(f"Package '{name}' removed.")
            self.load_deps()
            self.query_one("#btn-deps-remove").disabled = True
            self.query_one("#btn-deps-upgrade").disabled = True
        else:
            self.notify(f"Failed to remove '{name}'.", severity="error")
            self.query_one("#deps-status", Label).update("Removal failed.")

    async def upgrade_package(self) -> None:
        if not self.selected_pkg or not self.selected_latest:
            return

        name = self.selected_pkg
        target_ver = self.selected_latest
        source = self.selected_file_source

        self.notify(f"Upgrading {name} to {target_ver}...", severity="information")
        self.query_one("#deps-status", Label).update(f"Upgrading {name}...")

        # Find full path for source file
        # source is likely relative, e.g. "requirements.txt" or "package.json"
        # The analyzer stores it as string in 'source' but we need Path for updater
        file_path = self.project_dir / source

        success = await asyncio.to_thread(
            self.updater.update_dependency,
            file_path,
            name,
            target_ver,
            self.selected_dep_type
        )

        if success:
            self.notify(f"Upgraded {name}.")
            self.load_deps()
            self.query_one("#btn-deps-remove").disabled = True
            self.query_one("#btn-deps-upgrade").disabled = True
        else:
            self.notify(f"Failed to upgrade '{name}'.", severity="error")
            self.query_one("#deps-status", Label).update("Upgrade failed.")

    async def check_updates(self):
        self.query_one("#deps-status", Label).update("Checking for updates... (this may take a while)")
        self.notify("Checking updates...", severity="information")

        try:
            def do_check():
                data = self.analyzer.scan()
                return self.analyzer.check_updates(data)

            data = await asyncio.to_thread(do_check)

            table = self.query_one("#deps-table", DataTable)
            table.clear()

            # Python
            for file_info in data.get("python", []):
                src = file_info["source"]
                for dep in file_info.get("dependencies", []):
                    status = "[red]Outdated[/red]" if dep.get("outdated") else "[green]OK[/green]"
                    table.add_row(
                        "Python",
                        dep["name"],
                        dep.get("version", ""),
                        "prod",
                        dep.get("latest", "-"),
                        status,
                        src,
                        key=f"python|{dep['name']}|{src}"
                    )

            # Node
            for file_info in data.get("node", []):
                src = file_info["source"]
                for dep in file_info.get("dependencies", []):
                    status = "[red]Outdated[/red]" if dep.get("outdated") else "[green]OK[/green]"
                    table.add_row(
                        "Node",
                        dep["name"],
                        dep.get("version", ""),
                        dep.get("type", "prod"),
                        dep.get("latest", "-"),
                        status,
                        src,
                        key=f"node|{dep['name']}|{src}"
                    )

            self.query_one("#deps-status", Label).update("Update check complete.")
            self.notify("Update check complete.")

        except Exception as e:
            self.notify(f"Error checking updates: {e}", severity="error")
            self.query_one("#deps-status", Label).update("Error checking updates.")

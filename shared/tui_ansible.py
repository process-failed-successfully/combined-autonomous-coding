from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, Checkbox, DirectoryTree, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual import on

from shared.ansible_lab import AnsibleManager

class AnsibleLabTab(Container):
    """Tab for managing Ansible operations (Playbooks, Inventory, Lint)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = AnsibleManager(working_dir=project_dir)
        self.selected_playbook = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Configuration & Controls
            with Vertical(id="ansible-config-container", classes="stat-box"):
                yield Label("[bold]Ansible Lab[/bold]", classes="welcome-text")

                # Install Check
                if not self.manager.check_install():
                    yield Label("[bold red]Ansible not installed![/bold red]")
                    yield Label("Please install ansible-playbook.")

                with TabbedContent(id="ansible-tabs"):
                    with TabPane("Runner", id="tab-runner"):
                        yield Label("[bold]Select Playbook[/bold]")
                        # Restrict to current directory for safety/simplicity
                        yield DirectoryTree(str(self.project_dir), id="ansible-playbook-tree")

                        yield Label("Options:")
                        with Horizontal():
                            yield Checkbox("Check Mode", id="chk-ansible-check")
                            yield Checkbox("Diff Mode", id="chk-ansible-diff")

                        yield Label("Limit (Host pattern):")
                        yield Input(placeholder="e.g. webservers", id="ansible-limit")

                        yield Label("Inventory (optional path):")
                        yield Input(placeholder="inventory/hosts", id="ansible-inventory-path")

                        yield Label("Extra Vars (key=value):")
                        yield Input(placeholder="var=val", id="ansible-extra-vars")

                        yield Button("Run Playbook", id="btn-ansible-run", variant="primary", disabled=True)

                    with TabPane("Inventory", id="tab-inventory"):
                        yield Label("[bold]Inventory Explorer[/bold]")
                        yield Input(placeholder="Inventory path (default: implicit)", id="ansible-inv-list-path")
                        yield Button("List Inventory", id="btn-ansible-list-inv", variant="default")

                    with TabPane("Lint", id="tab-lint"):
                        yield Label("[bold]Ansible Lint[/bold]")
                        yield Button("Run Lint", id="btn-ansible-lint", variant="warning")

            # Right Pane: Output
            with Vertical(id="ansible-output-container"):
                yield Label("[bold]Output[/bold]")
                yield RichLog(id="ansible-log", wrap=True, highlight=True, markup=True)
                yield Button("Clear Log", id="btn-ansible-clear-log", variant="default")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        if event.path.is_file() and (event.path.suffix in [".yml", ".yaml"]):
            self.selected_playbook = event.path
            self.query_one("#btn-ansible-run").disabled = False
            self.notify(f"Selected: {event.path.name}")
        else:
            self.selected_playbook = None
            self.query_one("#btn-ansible-run").disabled = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        log = self.query_one("#ansible-log", RichLog)

        if btn_id == "btn-ansible-clear-log":
            log.clear()

        elif btn_id == "btn-ansible-run":
            await self.run_playbook()

        elif btn_id == "btn-ansible-list-inv":
            await self.list_inventory()

        elif btn_id == "btn-ansible-lint":
            await self.run_lint()

    async def run_playbook(self) -> None:
        if not self.selected_playbook:
            return

        log = self.query_one("#ansible-log", RichLog)
        log.write(f"\n[bold blue]Running Playbook: {self.selected_playbook.name}[/bold blue]")

        inventory = self.query_one("#ansible-inventory-path", Input).value
        limit = self.query_one("#ansible-limit", Input).value
        extra_vars = self.query_one("#ansible-extra-vars", Input).value
        check_mode = self.query_one("#chk-ansible-check", Checkbox).value
        diff_mode = self.query_one("#chk-ansible-diff", Checkbox).value

        self.query_one("#btn-ansible-run").disabled = True
        self.notify("Running playbook...")

        import asyncio

        def do_run():
            return self.manager.run_playbook(
                str(self.selected_playbook),
                inventory=inventory if inventory else None,
                check_mode=check_mode,
                diff_mode=diff_mode,
                limit=limit if limit else None,
                extra_vars=extra_vars if extra_vars else None,
                capture_output=True
            )

        try:
            success, output = await asyncio.to_thread(do_run)
            log.write(output)

            if success:
                log.write("[bold green]Playbook completed successfully.[/bold green]")
                self.notify("Playbook success.")
            else:
                log.write("[bold red]Playbook failed.[/bold red]")
                self.notify("Playbook failed.", severity="error")
        except Exception as e:
            log.write(f"[bold red]Error: {e}[/bold red]")
        finally:
            self.query_one("#btn-ansible-run").disabled = False

    async def list_inventory(self) -> None:
        log = self.query_one("#ansible-log", RichLog)
        inv_path = self.query_one("#ansible-inv-list-path", Input).value

        log.write("\n[bold blue]Listing Inventory...[/bold blue]")

        import asyncio

        try:
            output = await asyncio.to_thread(
                self.manager.list_inventory,
                inventory=inv_path if inv_path else None
            )
            if output:
                import json
                try:
                    data = json.loads(output)
                    from rich.syntax import Syntax
                    log.write(Syntax(json.dumps(data, indent=2), "json", theme="monokai"))
                except:
                    log.write(output)
            else:
                log.write("[red]Failed to list inventory.[/red]")
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

    async def run_lint(self) -> None:
        log = self.query_one("#ansible-log", RichLog)
        log.write("\n[bold blue]Running Ansible Lint...[/bold blue]")

        import asyncio

        def do_lint():
            return self.manager.lint(capture_output=True)

        try:
            success, output = await asyncio.to_thread(do_lint)
            log.write(output)

            if success:
                log.write("[bold green]Lint passed.[/bold green]")
            else:
                log.write("[bold red]Lint issues found.[/bold red]")
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

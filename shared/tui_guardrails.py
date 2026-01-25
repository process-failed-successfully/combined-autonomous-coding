from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Label, Button, DataTable, ListView, ListItem, RichLog
from textual import on

from shared.guardrails import GuardrailsManager

class GuardrailsTab(Container):
    """Tab for enforcing project guardrails (policies)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = GuardrailsManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Guardrails (Policy Enforcement)[/bold]", classes="welcome-text")

            # Status / Actions
            with Horizontal(classes="stat-box"):
                yield Button("Run Checks", id="btn-gr-check", variant="primary")
                yield Button("Reload Config", id="btn-gr-reload", variant="default")
                yield Button("Init Config", id="btn-gr-init", variant="warning")
                yield Label("", id="gr-status-lbl")

            with Horizontal():
                # Left Pane: Active Policies
                with Vertical(id="gr-policies-container", classes="stat-box"):
                    yield Label("[bold]Active Policies[/bold]")
                    yield ListView(id="gr-policy-list")

                # Right Pane: Violations
                with Vertical(id="gr-violations-container"):
                    yield Label("[bold]Violations[/bold]")
                    yield DataTable(id="gr-violations-table")

    def on_mount(self) -> None:
        self.load_policies()

        # Init table
        table = self.query_one("#gr-violations-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Policy", "Message", "Location")

    def load_policies(self) -> None:
        self.manager.load_config()

        list_view = self.query_one("#gr-policy-list", ListView)
        list_view.clear()

        if not self.manager.policies:
            list_view.append(ListItem(Label("[dim]No policies configured.[/dim]")))
            # Enable Init button only if no config exists
            has_config = (self.project_dir / "guardrails.yaml").exists() or \
                         (self.project_dir / "agent_config.yaml").exists()

            if not has_config:
                self.query_one("#btn-gr-init").disabled = False
            else:
                self.query_one("#btn-gr-init").disabled = True
            return

        self.query_one("#btn-gr-init").disabled = True

        for policy in self.manager.policies:
            p_type = policy.config.get("type", "unknown")
            list_view.append(ListItem(Label(f"[bold]{policy.name}[/bold] ({p_type})")))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-gr-check":
            await self.run_checks()
        elif event.button.id == "btn-gr-reload":
            self.manager = GuardrailsManager(self.project_dir) # Re-init
            self.load_policies()
            self.notify("Configuration reloaded.")
        elif event.button.id == "btn-gr-init":
            self.init_config()

    async def run_checks(self) -> None:
        self.query_one("#gr-status-lbl").update("Running checks...")
        self.notify("Running guardrails...")

        table = self.query_one("#gr-violations-table", DataTable)
        table.clear()

        import asyncio
        # Run in thread
        violations = await asyncio.to_thread(self.manager.run)

        if not violations:
            self.query_one("#gr-status-lbl").update("[green]All checks passed![/green]")
            self.notify("All checks passed.")
        else:
            self.query_one("#gr-status-lbl").update(f"[red]Found {len(violations)} violations.[/red]")
            self.notify(f"Found {len(violations)} violations.", severity="warning")

            for v in violations:
                location = v.file or "Project"
                if v.line:
                    location += f":{v.line}"
                table.add_row(v.policy_name, v.message, location)

    def init_config(self) -> None:
        try:
            path = self.manager.create_default_config()
            self.notify(f"Created {path.name}")
            self.manager.load_config()
            self.load_policies()
        except Exception as e:
            self.notify(f"Error creating config: {e}", severity="error")

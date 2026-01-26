from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, Input, Markdown, ListView, ListItem, Select, TextArea
from textual import on
from shared.adr import ADRManager

class ADRTab(Container):
    """Tab for managing Architecture Decision Records."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ADRManager(project_dir)
        self.selected_adr = None
        self.is_generating = False

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: List
            with Vertical(id="adr-list-container", classes="stat-box"):
                yield Label("[bold]Architecture Decisions[/bold]")
                yield ListView(id="adr-list")
                yield Button("Refresh", id="btn-adr-refresh", variant="default")

            # Right Pane: Details & Actions
            with Vertical(id="adr-details-container"):
                yield Label("[bold]ADR Details[/bold]")

                # Controls
                with Horizontal(classes="stat-box"):
                    yield Button("New Manual", id="btn-adr-create", variant="primary")
                    yield Button("New w/ AI", id="btn-adr-gen-start", variant="warning")
                    yield Select.from_values(["gemini", "cursor", "local"], id="adr-agent-select", value="gemini")
                    yield Button("Status: Accepted", id="btn-adr-accept", variant="success", disabled=True)
                    yield Button("Status: Deprecated", id="btn-adr-deprecate", variant="error", disabled=True)

                # Creation Pane (Hidden by default)
                with Vertical(id="adr-create-pane", classes="hidden stat-box"):
                    yield Label("New ADR", id="adr-create-lbl")
                    yield Input(placeholder="Title...", id="adr-new-title")
                    yield Label("Content / Context:")
                    yield TextArea(id="adr-new-context")
                    with Horizontal():
                        yield Button("Save / Generate", id="btn-adr-submit", variant="success")
                        yield Button("Cancel", id="btn-adr-cancel", variant="error")

                # Content Viewer
                with VerticalScroll(id="adr-content-pane"):
                    yield Markdown(id="adr-markdown")

    def on_mount(self) -> None:
        self.load_adrs()

    def load_adrs(self) -> None:
        list_view = self.query_one("#adr-list", ListView)
        list_view.clear()

        adrs = self.manager.list_adrs()
        if not adrs:
            list_view.append(ListItem(Label("No ADRs found.")))
            return

        for adr in adrs:
            title = adr["title"]
            status = adr["status"]
            filename = adr["filename"]

            # Formatting
            status_color = "white"
            if status == "Accepted": status_color = "green"
            elif status == "Proposed": status_color = "yellow"
            elif status in ["Deprecated", "Rejected"]: status_color = "red"

            # Escape the outer brackets so they appear literally, then open the color tag
            label = f"{title} \\[[{status_color}]{status}[/{status_color}]\\]"

            item = ListItem(Label(label))
            item.adr_filename = filename
            list_view.append(item)

    @on(ListView.Selected, "#adr-list")
    def on_adr_selected(self, event: ListView.Selected) -> None:
        if not hasattr(event.item, "adr_filename"):
            return

        filename = event.item.adr_filename
        self.selected_adr = filename
        self.load_content(filename)

        self.query_one("#btn-adr-accept").disabled = False
        self.query_one("#btn-adr-deprecate").disabled = False

    def load_content(self, filename: str) -> None:
        path = self.manager.adr_dir / filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
            self.query_one("#adr-markdown", Markdown).update(content)
        else:
            self.query_one("#adr-markdown", Markdown).update("File not found.")

    @on(Button.Pressed, "#btn-adr-refresh")
    def on_refresh(self) -> None:
        self.load_adrs()
        self.notify("ADR list refreshed.")

    @on(Button.Pressed, "#btn-adr-create")
    def on_create_manual(self) -> None:
        self.is_generating = False
        pane = self.query_one("#adr-create-pane")
        pane.remove_class("hidden")
        self.query_one("#adr-create-lbl", Label).update("New Manual ADR")
        self.query_one("#adr-new-title", Input).value = ""
        self.query_one("#adr-new-context", TextArea).text = ""
        self.query_one("#adr-new-title").focus()

    @on(Button.Pressed, "#btn-adr-gen-start")
    def on_generate_start(self) -> None:
        self.is_generating = True
        pane = self.query_one("#adr-create-pane")
        pane.remove_class("hidden")
        self.query_one("#adr-create-lbl", Label).update("Generate ADR with AI")
        self.query_one("#adr-new-title", Input).value = ""
        self.query_one("#adr-new-context", TextArea).text = "Describe the decision context here..."
        self.query_one("#adr-new-title").focus()

    @on(Button.Pressed, "#btn-adr-cancel")
    def on_cancel(self) -> None:
        self.query_one("#adr-create-pane").add_class("hidden")

    @on(Button.Pressed, "#btn-adr-submit")
    async def on_submit(self) -> None:
        title = self.query_one("#adr-new-title", Input).value
        content = self.query_one("#adr-new-context", TextArea).text

        if not title:
            self.notify("Title required.", severity="error")
            return

        if self.is_generating:
            # AI Generation
            agent_type = self.query_one("#adr-agent-select", Select).value or "gemini"
            self.notify(f"Generating ADR with {agent_type}...", severity="information")

            import asyncio
            try:
                # Run generation in thread
                generated_content = await self.manager.generate_adr_content(
                    title, content, agent_type=agent_type
                )
                # Create file
                self.manager.create_adr(title, content=generated_content)
                self.notify(f"ADR '{title}' generated and saved.")
            except Exception as e:
                self.notify(f"Generation failed: {e}", severity="error")
                return
        else:
            # Manual Creation
            try:
                self.manager.create_adr(title, content=content if content else None)
                self.notify(f"ADR '{title}' created.")
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
                return

        # Reset UI
        self.query_one("#adr-create-pane").add_class("hidden")
        self.load_adrs()

    @on(Button.Pressed, "#btn-adr-accept")
    def on_accept(self) -> None:
        if not self.selected_adr: return
        self.update_status("Accepted")

    @on(Button.Pressed, "#btn-adr-deprecate")
    def on_deprecate(self) -> None:
        if not self.selected_adr: return
        self.update_status("Deprecated")

    def update_status(self, new_status: str) -> None:
        try:
            if self.manager.update_status(self.selected_adr, new_status):
                self.notify(f"Status updated to {new_status}")
                self.load_adrs()
                self.load_content(self.selected_adr) # Reload content to show change
            else:
                self.notify("Failed to update status.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

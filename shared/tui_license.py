import datetime
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, Select, DataTable, TabbedContent, TabPane, Markdown, TextArea
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on

from shared.license_lab import LicenseLabManager

class LicenseLabTab(Container):
    """Tab for managing project licenses."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = LicenseLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]License Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Tab 1: Project License Generator
                with TabPane("Project License"):
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("License Type:")
                            yield Select([], id="lic-type-select", prompt="Select License")
                        with Vertical():
                            yield Label("Copyright Holder:")
                            yield Input(placeholder="Full Name or Organization", id="lic-holder-input")
                        with Vertical():
                            yield Label("Year:")
                            yield Input(str(datetime.datetime.now().year), id="lic-year-input")

                    with Horizontal(classes="stat-box"):
                        yield Button("Preview", id="btn-lic-preview", variant="primary")
                        yield Button("Save to LICENSE", id="btn-lic-save", variant="success")

                    with VerticalScroll(classes="stat-box"):
                        yield Label("[bold]Preview[/bold]")
                        yield TextArea(id="lic-preview-area", read_only=True)

                # Tab 2: Dependency Check
                with TabPane("Dependencies"):
                    with Horizontal(classes="stat-box"):
                        yield Button("Run Check", id="btn-lic-check", variant="primary")
                        # yield Input(placeholder="Allow List (comma sep)...", id="lic-allow-input") # TODO: Implement filtering later

                    yield DataTable(id="lic-deps-table")

                # Tab 3: Reference
                with TabPane("Reference"):
                    with Horizontal(classes="stat-box"):
                        yield Select([], id="lic-ref-select", prompt="Select License to View")

                    with VerticalScroll(classes="stat-box"):
                        yield Markdown("", id="lic-ref-markdown")

    def on_mount(self) -> None:
        # Populate License Selects
        licenses = self.manager.list_licenses()
        options = [(key, key) for key in licenses]

        self.query_one("#lic-type-select", Select).set_options(options)
        self.query_one("#lic-ref-select", Select).set_options(options)

        # Init DataTable
        table = self.query_one("#lic-deps-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Package", "Version", "License", "Status", "Message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-lic-preview":
            self.generate_preview()
        elif event.button.id == "btn-lic-save":
            self.save_license()
        elif event.button.id == "btn-lic-check":
            await self.check_dependencies()

    @on(Select.Changed, "#lic-ref-select")
    def on_ref_select(self, event: Select.Changed) -> None:
        if not event.value:
            return

        details = self.manager.get_license_details(event.value)
        if details:
            md_text = f"# {details['name']}\n\n"
            md_text += f"{details['description']}\n\n"

            md_text += "## Permissions\n"
            for p in details['permissions']:
                md_text += f"- ✅ {p}\n"

            md_text += "\n## Conditions\n"
            for c in details['conditions']:
                md_text += f"- ⚠️  {c}\n"

            md_text += "\n## Limitations\n"
            for l in details['limitations']:
                md_text += f"- ❌ {l}\n"

            self.query_one("#lic-ref-markdown", Markdown).update(md_text)

    def generate_preview(self) -> None:
        lic_type = self.query_one("#lic-type-select", Select).value
        holder = self.query_one("#lic-holder-input", Input).value
        year = self.query_one("#lic-year-input", Input).value

        if not lic_type:
            self.notify("Please select a license type.", severity="error")
            return

        if not holder:
            self.notify("Copyright holder is required.", severity="error")
            return

        content = self.manager.generate_license_content(lic_type, holder, year)
        if content:
            self.query_one("#lic-preview-area", TextArea).text = content
            self.notify("Preview generated.")
        else:
            self.notify("Error generating preview.", severity="error")

    def save_license(self) -> None:
        lic_type = self.query_one("#lic-type-select", Select).value
        holder = self.query_one("#lic-holder-input", Input).value
        year = self.query_one("#lic-year-input", Input).value

        if not lic_type or not holder:
            self.notify("License type and holder are required.", severity="error")
            return

        if self.manager.generate_license_file(lic_type, holder, year):
            self.notify("LICENSE file saved successfully!")
        else:
            self.notify("Failed to save LICENSE file.", severity="error")

    async def check_dependencies(self) -> None:
        table = self.query_one("#lic-deps-table", DataTable)
        table.clear()
        self.notify("Checking dependencies...")

        import asyncio
        # Run in thread
        results = await asyncio.to_thread(self.manager.check_dependencies)

        if not results:
            self.notify("No dependencies found or error checking.")
            return

        for item in results:
            status = item["status"]
            # Formatting
            status_style = "green" if status == "OK" else "red" if status == "VIOLATION" else "yellow"
            status_display = f"[{status_style}]{status}[/{status_style}]"

            table.add_row(
                item["package"],
                item["version"],
                item["license"],
                status_display,
                item["message"]
            )

        self.notify(f"Checked {len(results)} dependencies.")

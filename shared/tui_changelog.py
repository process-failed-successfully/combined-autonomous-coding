from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Static, Markdown
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on

from shared.changelog_lab import ChangelogManager

class ChangelogLabTab(Container):
    """
    Interactive Changelog Generator Tab.
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ChangelogManager(project_dir)

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: Controls
            with Vertical(id="changelog-controls", classes="stat-box"):
                yield Label("[bold]Changelog Settings[/bold]")

                yield Label("Base Ref (e.g. main, v1.0.0):")
                yield Input(placeholder="Leave empty for all history", id="changelog-base-input")

                yield Label("Head Ref (e.g. HEAD, feature-branch):")
                yield Input(value="HEAD", placeholder="HEAD", id="changelog-head-input")

                yield Label("Version Title:")
                yield Input(value="Next Release", placeholder="Version", id="changelog-version-input")

                yield Button("Generate", id="btn-changelog-generate", variant="primary")

            # Right: Preview
            with VerticalScroll(id="changelog-preview-pane", classes="stat-box"):
                yield Label("[bold]Preview[/bold]")
                yield Markdown(id="changelog-preview-md")
                yield Static(id="changelog-error-text", classes="error-text")

    def on_mount(self) -> None:
        self.query_one("#changelog-error-text").display = False

    @on(Button.Pressed, "#btn-changelog-generate")
    def on_generate(self) -> None:
        base_ref = self.query_one("#changelog-base-input", Input).value.strip()
        head_ref = self.query_one("#changelog-head-input", Input).value.strip() or "HEAD"
        version = self.query_one("#changelog-version-input", Input).value.strip() or "Next Release"

        preview = self.query_one("#changelog-preview-md", Markdown)
        error_text = self.query_one("#changelog-error-text", Static)

        preview.update("Generating...")
        error_text.display = False

        try:
            markdown_content = self.manager.generate_changelog(base_ref, head_ref, version)
            preview.update(markdown_content)
            self.notify("Changelog generated successfully.")
        except Exception as e:
            preview.update("")
            error_text.update(f"Error: {str(e)}")
            error_text.display = True
            self.notify(f"Generation failed: {e}", severity="error")

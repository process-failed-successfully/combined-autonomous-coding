from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, Input, Select, Markdown
from shared.presentation import PresentationGenerator


class PresentationTab(Container):
    """Tab for generating project presentations."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Presentation Generator[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Theme:")
                    yield Select.from_values(["default", "gaia", "uncover"], id="pres-theme", value="default")

                with Vertical():
                    yield Label("Output File:")
                    yield Input(value="presentation.md", placeholder="presentation.md", id="pres-output")

                with Vertical():
                    yield Label("Agent:")
                    yield Select.from_values(["gemini", "cursor", "local"], id="pres-agent", value="gemini")

                yield Button("Generate", id="btn-pres-generate", variant="primary")

            with VerticalScroll(id="pres-preview-container"):
                yield Label("[bold]Preview[/bold]")
                yield Markdown("Click Generate to create a presentation.", id="pres-preview")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pres-generate":
            await self.generate_presentation()

    async def generate_presentation(self) -> None:
        theme = str(self.query_one("#pres-theme", Select).value or "default")
        filename = str(self.query_one("#pres-output", Input).value or "presentation.md")
        agent_type = str(self.query_one("#pres-agent", Select).value or "gemini")

        output_path = self.project_dir / filename

        self.notify(f"Generating presentation with {agent_type}...", severity="information", timeout=5)

        # Update preview to show loading state
        preview = self.query_one("#pres-preview", Markdown)
        preview.update(f"Generating presentation using {agent_type}...\nThis may take a minute.")

        generator = PresentationGenerator(self.project_dir, agent_type=agent_type)

        import asyncio
        try:
            # Run generation in a thread to avoid blocking the UI
            success = await asyncio.to_thread(self._run_generation, generator, output_path, theme)

            if success:
                self.notify(f"Presentation saved to {filename}")
                if output_path.exists():
                    content = output_path.read_text(encoding="utf-8", errors="replace")
                    preview.update(content)
                else:
                    preview.update("Error: Output file not found after generation.")
            else:
                self.notify("Failed to generate presentation.", severity="error")
                preview.update("Generation failed. Check logs for details.")
        except Exception as e:
            self.notify(f"Error during generation: {e}", severity="error")
            preview.update(f"Error: {e}")

    def _run_generation(self, generator: PresentationGenerator, output_path: Path, theme: str) -> bool:
        """Helper to run the async generate method synchronously for to_thread."""
        import asyncio
        return asyncio.run(generator.generate(output_path, theme))

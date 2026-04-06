import asyncio
from pathlib import Path
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Select
from textual.message import Message

from shared.openapi import OpenAPIGenerator


class OpenAPILabTab(Container):
    """Tab for generating OpenAPI specifications."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]OpenAPI Generator Lab[/bold]", classes="welcome-text")
            yield Label("Use AI to automatically generate an OpenAPI 3.0 specification from your codebase routes.")

            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Output File Path:")
                    yield Input(value="openapi.yaml", id="openapi-output-input")
                with Vertical():
                    yield Label("Agent Type:")
                    yield Select.from_values(["gemini", "cursor", "local", "openrouter"], value="gemini", id="openapi-agent-select")
                with Vertical():
                    yield Label("Model (Optional):")
                    yield Input(placeholder="e.g. gpt-4o", id="openapi-model-input")

            with Horizontal(classes="stat-box"):
                yield Button("Generate OpenAPI Spec", id="btn-generate-openapi", variant="primary")

            with Vertical(classes="stat-box", id="openapi-log-container"):
                yield Label("[bold]Generator Log[/bold]")
                yield RichLog(id="openapi-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-generate-openapi":
            self.generate_spec()

    @work(exclusive=True, thread=True)
    def generate_spec(self) -> None:
        """Runs the generator in a worker thread."""
        log = self.app.query_one("#openapi-log", RichLog)

        # We need to dispatch UI updates back to the main thread safely
        def write_log(message: str) -> None:
            self.app.call_from_thread(log.write, message)

        self.app.call_from_thread(log.clear)
        write_log("[bold blue]Starting OpenAPI Generation...[/bold blue]")

        output_path_str = self.app.query_one("#openapi-output-input", Input).value
        if not output_path_str:
            write_log("[red]Error: Output path is required.[/red]")
            return

        output_path = Path(output_path_str)
        agent_type = self.app.query_one("#openapi-agent-select", Select).value or "gemini"
        model = self.app.query_one("#openapi-model-input", Input).value or None

        # Note: OpenAPIGenerator.generate is async, but we are inside a thread worker.
        # We must run it with a new event loop.
        async def run_gen():
            generator = OpenAPIGenerator(self.project_dir)
            framework = generator.detect_framework()
            write_log(f"Detected framework: [bold]{framework}[/bold]")

            route_files = generator.scan_routes(framework)
            write_log(f"Found {len(route_files)} relevant route files for analysis.")

            if not route_files:
                write_log("[yellow]No route files found. Cannot generate spec.[/yellow]")
                return

            write_log("Analyzing code and generating OpenAPI spec... (This may take a minute)")

            try:
                success = await generator.generate(output_path, agent_type=agent_type, model=model)
                if success:
                    write_log(f"[bold green]✅ OpenAPI spec successfully saved to {output_path}[/bold green]")

                    # Try to read and display a preview
                    if output_path.exists():
                        preview = output_path.read_text(encoding="utf-8", errors="ignore")
                        write_log("\n[bold]Preview (first 20 lines):[/bold]")
                        preview_lines = preview.splitlines()[:20]
                        write_log("\n".join(preview_lines))
                else:
                    write_log("[bold red]❌ Failed to generate OpenAPI spec.[/bold red]")
            except Exception as e:
                write_log(f"[bold red]Error during generation: {e}[/bold red]")

        try:
            asyncio.run(run_gen())
        except Exception as e:
            write_log(f"[bold red]Runtime Error: {e}[/bold red]")

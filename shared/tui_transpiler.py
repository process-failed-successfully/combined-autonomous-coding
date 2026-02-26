from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, TextArea, Select, RichLog
from textual import on
from shared.transpiler_lab import TranspilerManager

class TranspilerLabTab(Container):
    """Tab for Code Transpilation."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TranspilerManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Code Transpiler[/bold]", classes="welcome-text")

            # Controls
            with Horizontal(classes="stat-box"):
                yield Label("Source:", classes="label")
                yield Select.from_values(["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin", "Bash", "SQL"], id="transpile-source", value="Python")

                yield Label("Target:", classes="label")
                yield Select.from_values(["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin", "Bash", "SQL"], id="transpile-target", value="Go")

                yield Label("Agent:", classes="label")
                yield Select.from_values(["gemini", "cursor", "local"], id="transpile-agent", value="gemini")

                yield Button("Transpile", id="btn-transpile", variant="primary")

            # Main Editor Area
            with Horizontal(id="transpile-editor-area"):
                # Left: Input
                with Vertical(id="transpile-input-container"):
                    yield Label("[bold]Input Code[/bold]")
                    yield TextArea(id="transpile-input", language="python")

                # Right: Output
                with Vertical(id="transpile-output-container"):
                    yield Label("[bold]Output Code[/bold]")
                    yield TextArea(id="transpile-output", language="go", read_only=True)

            # Status Log
            yield RichLog(id="transpile-log", wrap=True, highlight=True, markup=True, max_lines=3)

    @on(Button.Pressed, "#btn-transpile")
    async def on_transpile(self) -> None:
        source_lang = self.query_one("#transpile-source", Select).value
        target_lang = self.query_one("#transpile-target", Select).value
        agent_type = self.query_one("#transpile-agent", Select).value or "gemini"

        input_area = self.query_one("#transpile-input", TextArea)
        output_area = self.query_one("#transpile-output", TextArea)
        log = self.query_one("#transpile-log", RichLog)

        content = input_area.text
        if not content.strip():
            self.notify("Input code required.", severity="error")
            return

        log.write(f"[italic]Transpiling {source_lang} to {target_lang} with {agent_type}...[/italic]")
        output_area.text = "Thinking..." # Placeholder

        # Transpilation can be slow (network call), so ideally we might run it in a thread.
        # However, `transpile` is async. If we run it in a thread, we need a new loop or use run_coroutine_threadsafe.
        # But Textual's event loop handles async handlers fine, although it might block the UI from redrawing if we don't yield.
        # `run_ask_logic` inside `transpile` does heavy network I/O.
        # Since we are in an async handler, simply awaiting it is the standard way,
        # provided the underlying network library (aiohttp/httpx) is non-blocking.

        try:
            result = await self.manager.transpile(content, source_lang, target_lang, agent_type)

            output_area.text = result

            # Try to update syntax highlighting
            try:
                output_area.language = target_lang.lower()
            except Exception:
                pass # Language might not be supported by TextArea

            log.write("[bold green]Success![/bold green]")
            self.notify("Transpilation complete.")

        except Exception as e:
            output_area.text = f"Error: {e}"
            log.write(f"[bold red]Error:[/bold red] {e}")

    @on(Select.Changed, "#transpile-source")
    def on_source_changed(self, event: Select.Changed) -> None:
        if event.value:
            try:
                self.query_one("#transpile-input", TextArea).language = event.value.lower()
            except Exception:
                pass

    @on(Select.Changed, "#transpile-target")
    def on_target_changed(self, event: Select.Changed) -> None:
        if event.value:
            try:
                self.query_one("#transpile-output", TextArea).language = event.value.lower()
            except Exception:
                pass

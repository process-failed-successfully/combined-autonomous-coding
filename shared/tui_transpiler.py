from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, Select, TextArea, Static
from textual import on
from shared.transpiler_lab import TranspilerManager

class TranspilerTab(Container):
    """Tab for transpiling code between languages."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TranspilerManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Code Transpiler Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Source Language:")
                    yield Select.from_values(
                        ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin"],
                        id="transpiler-source-lang",
                        value="Python"
                    )
                with Vertical():
                    yield Label("Target Language:")
                    yield Select.from_values(
                        ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin"],
                        id="transpiler-target-lang",
                        value="Go"
                    )
                with Vertical():
                    yield Label("Agent:")
                    yield Select.from_values(["gemini", "cursor", "local"], id="transpiler-agent", value="gemini")

                yield Button("Transpile", id="btn-transpile", variant="primary")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Source Code[/bold]")
                    yield TextArea(id="transpiler-source-code", language="python")

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Target Code[/bold]")
                    yield TextArea(id="transpiler-target-code", read_only=True)

    @on(Select.Changed, "#transpiler-source-lang")
    def on_source_lang_changed(self, event: Select.Changed) -> None:
        if event.value:
            lang_map = {
                "Python": "python", "JavaScript": "javascript", "TypeScript": "typescript",
                "Go": "go", "Rust": "rust", "Java": "java", "C++": "cpp", "C#": "csharp",
                "Ruby": "ruby", "PHP": "php", "Swift": "swift", "Kotlin": "kotlin"
            }
            editor = self.query_one("#transpiler-source-code", TextArea)
            # Textual TextArea languages are limited, map best effort
            mapped_lang = lang_map.get(str(event.value), "text")
            # Textual 0.64 might not support all, default to python if unknown or keep as is if supported
            # Actually TextArea tries to detect if not set, or we set explicitly.
            # We'll trust it handles standard ones or falls back gracefully.
            try:
                editor.language = mapped_lang
            except Exception:
                editor.language = "text"

    @on(Select.Changed, "#transpiler-target-lang")
    def on_target_lang_changed(self, event: Select.Changed) -> None:
        if event.value:
            lang_map = {
                "Python": "python", "JavaScript": "javascript", "TypeScript": "typescript",
                "Go": "go", "Rust": "rust", "Java": "java", "C++": "cpp", "C#": "csharp",
                "Ruby": "ruby", "PHP": "php", "Swift": "swift", "Kotlin": "kotlin"
            }
            editor = self.query_one("#transpiler-target-code", TextArea)
            mapped_lang = lang_map.get(str(event.value), "text")
            try:
                editor.language = mapped_lang
            except Exception:
                editor.language = "text"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-transpile":
            await self.run_transpilation()

    async def run_transpilation(self) -> None:
        source_code = self.query_one("#transpiler-source-code", TextArea).text
        source_lang = self.query_one("#transpiler-source-lang", Select).value
        target_lang = self.query_one("#transpiler-target-lang", Select).value
        agent = self.query_one("#transpiler-agent", Select).value or "gemini"

        if not source_code:
            self.notify("Source code is empty.", severity="warning")
            return

        self.notify(f"Transpiling {source_lang} to {target_lang}...", severity="information")
        target_editor = self.query_one("#transpiler-target-code", TextArea)
        target_editor.text = "Transpiling... please wait."

        result = await self.manager.transpile(
            source_code,
            source_lang=str(source_lang),
            target_lang=str(target_lang),
            agent_type=str(agent)
        )

        target_editor.text = result
        self.notify("Transpilation complete.")

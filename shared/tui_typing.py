import time
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, TextArea, Select, Static
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from rich.syntax import Syntax
from shared.typing_lab import TypingLabManager

class TypingLabTab(Container):
    """Tab for Typing Tutor."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = TypingLabManager(project_dir)
        self.start_time = None
        self.target_text = ""
        self.session_running = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Typing Lab[/bold]", classes="welcome-text")

            # Controls
            with Horizontal(classes="stat-box"):
                yield Select([], id="typing-select", prompt="Select Snippet")
                yield Button("Start", id="btn-typing-start", variant="primary", disabled=True)
                yield Button("Reset", id="btn-typing-reset", variant="error")

            # Stats
            with Horizontal(classes="stat-box", id="typing-stats"):
                yield Label("WPM: 0.0", id="lbl-wpm")
                yield Label("Accuracy: 100.0%", id="lbl-acc")
                yield Label("Progress: 0.0%", id="lbl-progress")

            # Display & Input
            with VerticalScroll():
                yield Label("[bold]Target Code:[/bold]")
                yield Static(id="typing-target", classes="box")

                yield Label("[bold]Type Here:[/bold]")
                yield TextArea(id="typing-input", language="python", disabled=True)

    def on_mount(self) -> None:
        self.load_options()

    def load_options(self) -> None:
        options = self.manager.list_options()
        select = self.query_one("#typing-select", Select)
        select.set_options([(f"{k} ({v})", k) for k, v in options.items()])

    @on(Select.Changed, "#typing-select")
    def on_snippet_selected(self, event: Select.Changed) -> None:
        name = event.value
        if not name:
            return

        self.target_text = self.manager.get_snippet(name)

        # Display target with syntax highlighting
        target_view = self.query_one("#typing-target", Static)
        target_view.update(Syntax(self.target_text, "python", theme="monokai", line_numbers=True))

        self.query_one("#btn-typing-start").disabled = False
        self.reset_session()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-typing-start":
            self.start_session()
        elif event.button.id == "btn-typing-reset":
            self.reset_session()

    def start_session(self) -> None:
        self.session_running = True
        self.start_time = time.time()

        inp = self.query_one("#typing-input", TextArea)
        inp.disabled = False
        inp.text = ""
        inp.focus()

        self.notify("Typing started! Go!", timeout=2)

    def reset_session(self) -> None:
        self.session_running = False
        self.start_time = None

        inp = self.query_one("#typing-input", TextArea)
        inp.text = ""
        inp.disabled = True

        self.update_stats(0, 100, 0)

    @on(TextArea.Changed, "#typing-input")
    def on_input_changed(self, event: TextArea.Changed) -> None:
        if not self.session_running:
            return

        typed = event.text_area.text

        if not self.start_time:
            self.start_time = time.time()

        duration = time.time() - self.start_time

        stats = self.manager.calculate_stats(self.target_text, typed, duration)
        self.update_stats(stats["wpm"], stats["accuracy"], stats["progress"])

        # Check completion
        if len(typed) >= len(self.target_text):
            if typed == self.target_text:
                self.session_running = False
                self.notify("Completed!", severity="information")
                event.text_area.disabled = True
            else:
                # Finished length but with errors
                pass

    def update_stats(self, wpm, acc, prog) -> None:
        self.query_one("#lbl-wpm", Label).update(f"WPM: {wpm}")
        self.query_one("#lbl-acc", Label).update(f"Accuracy: {acc}%")
        self.query_one("#lbl-progress", Label).update(f"Progress: {prog}%")

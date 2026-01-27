from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Button, Label, Markdown
from textual import on
from pathlib import Path
from shared.quiz import QuizGenerator, QuizQuestion

class QuizTab(Container):
    """Tab for the interactive Codebase Quiz."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.generator = QuizGenerator(project_dir)
        self.questions: list[QuizQuestion] = []
        self.current_index = 0
        self.score = 0
        self.answered = False

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="quiz-container"):
            yield Label("[bold]Codebase Quiz[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Score: 0/0", id="quiz-score")
                yield Button("New Game", id="btn-quiz-new", variant="primary")

            with Vertical(id="quiz-game-area", classes="stat-box"):
                yield Markdown("", id="quiz-question-text")

                with Vertical(id="quiz-options"):
                    # create 4 buttons
                    yield Button("Option A", id="btn-opt-0", classes="quiz-option")
                    yield Button("Option B", id="btn-opt-1", classes="quiz-option")
                    yield Button("Option C", id="btn-opt-2", classes="quiz-option")
                    yield Button("Option D", id="btn-opt-3", classes="quiz-option")

                yield Label("", id="quiz-feedback")
                yield Button("Next Question", id="btn-quiz-next", variant="success", disabled=True)

    def on_mount(self) -> None:
        self.start_game()

    def start_game(self) -> None:
        self.questions = self.generator.generate_questions(10)
        self.current_index = 0
        self.score = 0
        self.update_score()
        self.load_current_question()

        # Ensure UI is visible
        self.query_one("#quiz-options").display = True
        self.query_one("#btn-quiz-next").display = True

    def update_score(self) -> None:
        self.query_one("#quiz-score", Label).update(f"Score: {self.score}/{self.current_index}")

    def load_current_question(self) -> None:
        if not self.questions or self.current_index >= len(self.questions):
            self.show_game_over()
            return

        q = self.questions[self.current_index]
        self.answered = False

        # Reset UI
        self.query_one("#quiz-question-text", Markdown).update(f"**Q{self.current_index + 1}:** {q.text}")
        self.query_one("#quiz-feedback", Label).update("")
        self.query_one("#btn-quiz-next").disabled = True

        # Update options
        for i in range(4):
            try:
                btn = self.query_one(f"#btn-opt-{i}", Button)
                if i < len(q.options):
                    btn.label = q.options[i]
                    btn.disabled = False
                    btn.variant = "default"
                    btn.display = True
                else:
                    btn.display = False
            except Exception:
                pass

    def show_game_over(self) -> None:
        total = len(self.questions)
        self.query_one("#quiz-question-text", Markdown).update(f"# Game Over!\n\nFinal Score: {self.score}/{total}")
        self.query_one("#quiz-score", Label).update(f"Final Score: {self.score}/{total}")
        self.query_one("#quiz-options").display = False
        self.query_one("#quiz-feedback", Label).update("")
        self.query_one("#btn-quiz-next").display = False

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-quiz-new":
            self.start_game()

        elif event.button.id == "btn-quiz-next":
            self.current_index += 1
            self.update_score()
            self.load_current_question()

        elif event.button.id and event.button.id.startswith("btn-opt-"):
            if self.answered:
                return

            try:
                idx = int(event.button.id.split("-")[-1])
                self.check_answer(idx)
            except ValueError:
                pass

    def check_answer(self, selected_index: int) -> None:
        self.answered = True
        q = self.questions[self.current_index]

        feedback = self.query_one("#quiz-feedback", Label)

        if selected_index == q.correct_index:
            self.score += 1
            self.update_score()
            feedback.update(f"[bold green]Correct![/bold green] {q.explanation}")
            self.query_one(f"#btn-opt-{selected_index}", Button).variant = "success"
        else:
            feedback.update(f"[bold red]Incorrect.[/bold red] {q.explanation}")
            self.query_one(f"#btn-opt-{selected_index}", Button).variant = "error"
            # Highlight correct one
            self.query_one(f"#btn-opt-{q.correct_index}", Button).variant = "success"

        # Disable all options
        for i in range(4):
            self.query_one(f"#btn-opt-{i}", Button).disabled = True

        self.query_one("#btn-quiz-next").disabled = False

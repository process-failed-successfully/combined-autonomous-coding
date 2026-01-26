from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Label, Button, RichLog, Markdown, ProgressBar
from textual import on
from shared.quiz import QuizGenerator, Question

class QuizTab(Container):
    """Tab for interactive codebase quiz."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.generator = QuizGenerator(project_dir)
        self.current_question: Question = None
        self.score = 0
        self.total_questions = 0
        self.max_questions = 10
        self.is_answered = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Codebase Quiz[/bold]", classes="welcome-text")

            # Score Header
            with Horizontal(classes="stat-box"):
                yield Label("Score: 0/0", id="quiz-score-lbl")
                yield ProgressBar(total=self.max_questions, show_eta=False, id="quiz-progress")
                yield Button("New Game", id="btn-quiz-new", variant="primary")

            # Question Area
            with VerticalScroll(id="quiz-question-container", classes="stat-box"):
                yield Markdown("", id="quiz-question-text")

                # Options Container (Dynamic buttons)
                with Vertical(id="quiz-options-container"):
                    pass # Buttons added dynamically

            # Feedback Area
            with Vertical(classes="stat-box"):
                yield Label("[bold]Feedback[/bold]")
                yield RichLog(id="quiz-feedback-log", wrap=True, highlight=True, markup=True)

            with Horizontal(classes="stat-box"):
                yield Button("Next Question", id="btn-quiz-next", variant="default", disabled=True)

    async def on_mount(self) -> None:
        await self.start_new_game()

    async def start_new_game(self) -> None:
        self.score = 0
        self.total_questions = 0
        self.is_answered = False
        self.update_score()
        self.query_one("#quiz-progress", ProgressBar).update(progress=0)
        self.query_one("#quiz-feedback-log", RichLog).clear()

        # Load questions
        self.generator.load_data()
        await self.load_next_question()

    def update_score(self) -> None:
        lbl = self.query_one("#quiz-score-lbl", Label)
        lbl.update(f"Score: {self.score}/{self.total_questions}")

    async def load_next_question(self) -> None:
        if self.total_questions >= self.max_questions:
            self.finish_game()
            return

        self.is_answered = False

        # Generate 1 question at a time to keep it random/fresh
        questions = self.generator.generate_questions(count=1)
        if not questions:
            self.query_one("#quiz-question-text", Markdown).update("No questions could be generated.")
            return

        self.current_question = questions[0]

        # Update UI
        q_text = f"**Question {self.total_questions + 1}:**\n\n{self.current_question.text}"
        self.query_one("#quiz-question-text", Markdown).update(q_text)

        # Update Options
        opts_container = self.query_one("#quiz-options-container", Vertical)
        await opts_container.remove_children()

        for i, option in enumerate(self.current_question.options):
            btn = Button(option, id=f"quiz-opt-{i}", classes="quiz-option-btn")
            opts_container.mount(btn)

        self.query_one("#btn-quiz-next", Button).disabled = True

    @on(Button.Pressed)
    async def on_button_click(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-quiz-new":
            await self.start_new_game()
        elif event.button.id == "btn-quiz-next":
            await self.load_next_question()
        elif event.button.id and event.button.id.startswith("quiz-opt-"):
            self.check_answer(event.button)

    def check_answer(self, button: Button) -> None:
        if self.is_answered:
            return

        self.is_answered = True
        self.total_questions += 1

        selected_idx = int(button.id.split("-")[-1])
        correct_idx = self.current_question.correct_index

        log = self.query_one("#quiz-feedback-log", RichLog)

        if selected_idx == correct_idx:
            self.score += 1
            button.variant = "success"
            log.write("[bold green]Correct![/bold green]")
        else:
            button.variant = "error"
            # Highlight correct one
            opts = self.query_one("#quiz-options-container").children
            if 0 <= correct_idx < len(opts):
                opts[correct_idx].variant = "success"

            log.write(f"[bold red]Incorrect.[/bold red] The correct answer was: {self.current_question.options[correct_idx]}")

        if self.current_question.explanation:
            log.write(f"[italic]{self.current_question.explanation}[/italic]")

        self.update_score()
        self.query_one("#quiz-progress", ProgressBar).update(progress=self.total_questions)
        self.query_one("#btn-quiz-next", Button).disabled = False

    def finish_game(self) -> None:
        self.query_one("#quiz-question-text", Markdown).update(f"# Game Over!\n\nFinal Score: {self.score}/{self.max_questions}")
        self.query_one("#quiz-options-container", Vertical).remove_children()
        self.query_one("#btn-quiz-next", Button).disabled = True
        self.query_one("#quiz-feedback-log", RichLog).write("[bold]Great job! Click 'New Game' to play again.[/bold]")

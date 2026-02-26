from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Input, DataTable, Select, Markdown, ListView, ListItem, DirectoryTree, Static
from textual import on
from textual.reactive import reactive

from shared.flashcards_lab import FlashcardsManager, Flashcard

class FlashcardsTab(Container):
    """Tab for Spaced Repetition Learning (Flashcards)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = FlashcardsManager(project_dir)
        self.current_card: Flashcard | None = None
        self.is_answer_visible = False

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Sidebar: Navigation / Controls
            with Vertical(id="fc-sidebar", classes="stat-box"):
                yield Label("[bold]Flashcards[/bold]", classes="header")
                yield Button("Review Due", id="btn-fc-review", variant="primary")
                yield Button("Manage Cards", id="btn-fc-manage", variant="default")
                yield Button("Generate (AI)", id="btn-fc-generate", variant="warning")

                yield Label("\nStats:")
                yield Label("Total: 0", id="lbl-fc-total")
                yield Label("Due: 0", id="lbl-fc-due")

            # Main Content Area
            with Container(id="fc-content"):
                # 1. Review Container (Initially Hidden)
                with Vertical(id="fc-review-container", classes="hidden"):
                    yield Label("Review Session", classes="welcome-text")

                    with Container(id="card-display", classes="stat-box"):
                        yield Label("Question:", classes="label")
                        yield Markdown("", id="fc-question")

                        yield Static("", id="fc-answer-spacer") # Spacer

                        with Vertical(id="fc-answer-section", classes="hidden"):
                            yield Label("Answer:", classes="label")
                            yield Markdown("", id="fc-answer")

                    with Horizontal(id="fc-review-controls"):
                        yield Button("Show Answer", id="btn-fc-show-answer", variant="primary")

                        # Grading Buttons (Hidden initially)
                        with Horizontal(id="fc-grading-buttons", classes="hidden"):
                            yield Button("Again (1m)", id="btn-grade-0", variant="error")
                            yield Button("Hard (6m)", id="btn-grade-3", variant="warning")
                            yield Button("Good (10m)", id="btn-grade-4", variant="success")
                            yield Button("Easy (4d)", id="btn-grade-5", variant="primary")

                # 2. Manage Container (Initially Hidden)
                with Vertical(id="fc-manage-container", classes="hidden"):
                    yield Label("Manage Flashcards", classes="welcome-text")
                    yield DataTable(id="fc-table")
                    yield Button("Delete Selected", id="btn-fc-delete", variant="error", disabled=True)

                # 3. Generate Container (Initially Hidden)
                with Vertical(id="fc-generate-container", classes="hidden"):
                    yield Label("Generate Flashcards with AI", classes="welcome-text")
                    with Horizontal():
                        with Vertical(classes="stat-box"):
                            yield Label("Select File:")
                            yield DirectoryTree(str(self.project_dir), id="fc-file-tree")

                        with Vertical(classes="stat-box"):
                            yield Label("Configuration:")
                            yield Select.from_values(["gemini", "cursor", "local"], id="fc-agent-select", value="gemini")
                            yield Label("Selected File:")
                            yield Label("None", id="lbl-fc-selected-file")
                            yield Button("Generate", id="btn-fc-run-gen", variant="primary", disabled=True)
                            yield Label("", id="lbl-fc-gen-status")

    def on_mount(self) -> None:
        self.refresh_stats()
        # Default view
        self.show_manage()

    def refresh_stats(self) -> None:
        total = len(self.manager.cards)
        due = len(self.manager.get_due_cards())
        self.query_one("#lbl-fc-total", Label).update(f"Total: {total}")
        self.query_one("#lbl-fc-due", Label).update(f"Due: {due}")

    def hide_all_containers(self) -> None:
        for cid in ["fc-review-container", "fc-manage-container", "fc-generate-container"]:
            self.query_one(f"#{cid}").add_class("hidden")

    # --- Mode Switching ---

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-fc-review":
            self.start_review()
        elif bid == "btn-fc-manage":
            self.show_manage()
        elif bid == "btn-fc-generate":
            self.show_generate()
        elif bid == "btn-fc-show-answer":
            self.reveal_answer()
        elif bid.startswith("btn-grade-"):
            grade = int(bid.split("-")[-1])
            self.process_grade(grade)
        elif bid == "btn-fc-delete":
            self.delete_selected()
        elif bid == "btn-fc-run-gen":
            await self.run_generation()

    # --- Review Logic ---

    def start_review(self) -> None:
        self.hide_all_containers()
        self.query_one("#fc-review-container").remove_class("hidden")

        due_cards = self.manager.get_due_cards()
        if not due_cards:
            self.query_one("#fc-question", Markdown).update("**No cards due for review!** 🎉")
            self.query_one("#fc-review-controls").add_class("hidden")
            return

        self.query_one("#fc-review-controls").remove_class("hidden")
        self.load_card(due_cards[0])

    def load_card(self, card: Flashcard) -> None:
        self.current_card = card
        self.is_answer_visible = False

        self.query_one("#fc-question", Markdown).update(card.question)
        self.query_one("#fc-answer", Markdown).update(card.answer)

        # Hide answer section
        self.query_one("#fc-answer-section").add_class("hidden")

        # Show "Show Answer" button, hide grading buttons
        self.query_one("#btn-fc-show-answer").remove_class("hidden")
        self.query_one("#fc-grading-buttons").add_class("hidden")

    def reveal_answer(self) -> None:
        self.is_answer_visible = True
        self.query_one("#fc-answer-section").remove_class("hidden")
        self.query_one("#btn-fc-show-answer").add_class("hidden")
        self.query_one("#fc-grading-buttons").remove_class("hidden")

    def process_grade(self, grade: int) -> None:
        if not self.current_card:
            return

        self.manager.review_card(self.current_card.id, grade)
        self.notify(f"Card reviewed (Grade: {grade})")
        self.refresh_stats()

        # Next card
        self.start_review()

    # --- Manage Logic ---

    def show_manage(self) -> None:
        self.hide_all_containers()
        self.query_one("#fc-manage-container").remove_class("hidden")

        table = self.query_one("#fc-table", DataTable)
        table.clear()
        table.cursor_type = "row"
        if not table.columns:
            table.add_columns("Question", "Source", "Next Due", "Interval")

        for card in self.manager.cards:
            # Truncate question
            q = card.question.split("\n")[0]
            if len(q) > 50: q = q[:47] + "..."

            # Format date
            due = card.due_date[:10]

            table.add_row(q, card.source_file, due, str(card.interval), key=card.id)

    @on(DataTable.RowSelected, "#fc-table")
    def on_row_selected(self) -> None:
        self.query_one("#btn-fc-delete").disabled = False

    def delete_selected(self) -> None:
        table = self.query_one("#fc-table", DataTable)
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        card_id = row_key.value

        if self.manager.delete_card(card_id):
            self.notify("Card deleted.")
            self.show_manage() # Refresh
            self.refresh_stats()

    # --- Generate Logic ---

    def show_generate(self) -> None:
        self.hide_all_containers()
        self.query_one("#fc-generate-container").remove_class("hidden")

    @on(DirectoryTree.FileSelected, "#fc-file-tree")
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.query_one("#lbl-fc-selected-file", Label).update(event.path.name)
        self.query_one("#btn-fc-run-gen").disabled = False
        self.selected_gen_file = event.path

    async def run_generation(self) -> None:
        if not hasattr(self, "selected_gen_file"):
            return

        agent_type = self.query_one("#fc-agent-select", Select).value or "gemini"

        lbl = self.query_one("#lbl-fc-gen-status", Label)
        lbl.update(f"Generating with {agent_type}...")
        self.query_one("#btn-fc-run-gen").disabled = True

        import asyncio
        try:
            cards = await self.manager.generate_flashcards(self.selected_gen_file, agent_type=agent_type)
            lbl.update(f"[green]Generated {len(cards)} cards![/green]")
            self.notify(f"Generated {len(cards)} cards.")
            self.refresh_stats()
        except Exception as e:
            lbl.update(f"[red]Error: {e}[/red]")
            self.notify(f"Error: {e}", severity="error")
        finally:
            self.query_one("#btn-fc-run-gen").disabled = False

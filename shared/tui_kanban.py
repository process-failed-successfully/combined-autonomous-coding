from textual.widgets import Static, Button, Label
from textual.containers import VerticalScroll, Horizontal, Container
from textual.message import Message
from textual import on

class KanbanCard(Static):
    """A card representing a task in the Kanban board."""

    class Move(Message):
        """Message sent when a card move is requested."""
        def __init__(self, card, task_id: str, direction: str):
            self.card = card
            self.task_id = task_id
            self.direction = direction
            super().__init__()

    def __init__(self, task, **kwargs):
        super().__init__(**kwargs)
        self.kanban_task = task

    def compose(self):
        task = self.kanban_task

        # Status Color
        priority_color = "white"
        if task.priority.lower() == "high":
            priority_color = "red"
        elif task.priority.lower() == "medium":
            priority_color = "yellow"
        elif task.priority.lower() == "low":
            priority_color = "green"

        yield Label(f"[{priority_color}]{task.priority}[/{priority_color}] [bold]{task.title}[/bold]", classes="kanban-card-title")
        yield Label(f"[dim]{task.id} ({task.source})[/dim]", classes="kanban-card-meta")

        with Horizontal(classes="kanban-card-actions"):
            yield Button("Before", variant="default", classes="kanban-btn move-left")
            yield Button("Next", variant="default", classes="kanban-btn move-right")

    def on_button_pressed(self, event: Button.Pressed):
        event.stop()
        if "move-left" in event.button.classes:
            self.post_message(self.Move(self, self.kanban_task.id, "left"))
        elif "move-right" in event.button.classes:
            self.post_message(self.Move(self, self.kanban_task.id, "right"))


class KanbanColumn(VerticalScroll):
    """A column in the Kanban board."""
    def __init__(self, title: str, id: str, **kwargs):
        super().__init__(id=id, **kwargs)
        self.title = title

    def compose(self):
        yield Label(f"[bold]{self.title}[/bold]", classes="kanban-col-header")
        # Cards will be added here dynamically

class KanbanBoard(Container):
    """The Kanban Board widget."""

    class StatusChanged(Message):
        """Message sent when a task status changes."""
        def __init__(self, task_id: str, new_status: str, source: str):
            self.task_id = task_id
            self.new_status = new_status
            self.source = source
            super().__init__()

    def compose(self):
        with Horizontal(id="kanban-board-container"):
            yield KanbanColumn("To Do", id="col-todo", classes="kanban-col")
            yield KanbanColumn("In Progress", id="col-inprogress", classes="kanban-col")
            yield KanbanColumn("Done", id="col-done", classes="kanban-col")

    def clear_board(self):
        for col_id in ["col-todo", "col-inprogress", "col-done"]:
            col = self.query_one(f"#{col_id}", KanbanColumn)
            # Remove all KanbanCard instances
            for child in col.query(KanbanCard):
                child.remove()

    def add_task(self, task):
        # Determine column based on status
        # Normalize status
        status = str(task.status).lower().replace("_", " ")
        col_id = "col-todo"

        if status in ["in progress", "inprogress", "active", "review"]:
            col_id = "col-inprogress"
        elif status in ["done", "completed", "closed", "fixed", "resolved", "merged"]:
            col_id = "col-done"

        col = self.query_one(f"#{col_id}", KanbanColumn)
        col.mount(KanbanCard(task, classes="kanban-card"))

    @on(KanbanCard.Move)
    def handle_card_move(self, event: KanbanCard.Move):
        card = event.card
        task = card.kanban_task
        direction = event.direction

        cols = ["col-todo", "col-inprogress", "col-done"]
        statuses = ["To Do", "In Progress", "Done"]

        # Find current column ID
        current_col = card.parent
        if not current_col: return

        try:
            current_idx = cols.index(current_col.id)
        except ValueError:
            return

        new_idx = current_idx
        if direction == "right":
            new_idx = min(current_idx + 1, len(cols) - 1)
        elif direction == "left":
            new_idx = max(current_idx - 1, 0)

        if new_idx != current_idx:
            new_status = statuses[new_idx]
            self.post_message(self.StatusChanged(task.id, new_status, task.source))

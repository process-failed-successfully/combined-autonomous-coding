from textual.app import ComposeResult
from textual.widgets import Button, Label
from textual.containers import Horizontal, Container, VerticalScroll
from textual.message import Message
from textual import on
from shared.task_manager import Task

class KanbanCard(Container):
    class Move(Message):
        def __init__(self, card_id: str, direction: str) -> None:
            self.card_id = card_id
            self.direction = direction
            super().__init__()

    def __init__(self, task: Task, **kwargs) -> None:
        super().__init__(**kwargs)
        self.kanban_task = task
        self.add_class("kanban-card")

    def compose(self) -> ComposeResult:
        yield Label(f"{self.kanban_task.source.upper()} {self.kanban_task.id}", classes="card-header")
        yield Label(self.kanban_task.title, classes="card-title")
        yield Label(f"Priority: {self.kanban_task.priority}", classes=f"card-priority-{self.kanban_task.priority.lower()}")

        with Horizontal(classes="card-actions"):
            # Disable left button if in first column is handled by logic, but visually we can just have both
            yield Button("⬅", id="btn-move-left", variant="default", classes="btn-move")
            yield Button("➡", id="btn-move-right", variant="default", classes="btn-move")

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-move-left":
            self.post_message(self.Move(self.kanban_task.id, "left"))
        elif event.button.id == "btn-move-right":
            self.post_message(self.Move(self.kanban_task.id, "right"))

class KanbanColumn(VerticalScroll):
    def __init__(self, title: str, status_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.status_id = status_id
        self.add_class("kanban-column")

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="column-header")
        # Cards added dynamically

    def add_task(self, task: Task) -> None:
        self.mount(KanbanCard(task))

    def clear_tasks(self) -> None:
        for child in self.query(KanbanCard):
            child.remove()

class KanbanBoard(Horizontal):
    class StatusUpdate(Message):
        def __init__(self, task_id: str, new_status: str) -> None:
            self.task_id = task_id
            self.new_status = new_status
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.columns_map = {
            "todo": ["pending", "open", "to do", "todo", "new"],
            "in_progress": ["in_progress", "in progress", "active", "developing"],
            "done": ["completed", "done", "closed", "fixed", "resolved"]
        }
        self.col_todo = KanbanColumn("To Do", "todo", id="col-todo")
        self.col_prog = KanbanColumn("In Progress", "in_progress", id="col-prog")
        self.col_done = KanbanColumn("Done", "done", id="col-done")

    def compose(self) -> ComposeResult:
        yield self.col_todo
        yield self.col_prog
        yield self.col_done

    def load_tasks(self, tasks: list[Task]) -> None:
        self.col_todo.clear_tasks()
        self.col_prog.clear_tasks()
        self.col_done.clear_tasks()

        for task in tasks:
            status = str(task.status).lower().replace("-", "_")
            if status in self.columns_map["done"]:
                self.col_done.add_task(task)
            elif status in self.columns_map["in_progress"]:
                self.col_prog.add_task(task)
            else:
                self.col_todo.add_task(task)

    @on(KanbanCard.Move)
    def on_card_move(self, event: KanbanCard.Move) -> None:
        current_col_id = None

        # Find which column contains the card
        if any(c.kanban_task.id == event.card_id for c in self.col_todo.query(KanbanCard)):
            current_col_id = "todo"
        elif any(c.kanban_task.id == event.card_id for c in self.col_prog.query(KanbanCard)):
            current_col_id = "in_progress"
        elif any(c.kanban_task.id == event.card_id for c in self.col_done.query(KanbanCard)):
            current_col_id = "done"

        if not current_col_id:
            return

        new_group = None
        if current_col_id == "todo":
            if event.direction == "right": new_group = "in_progress"
        elif current_col_id == "in_progress":
            if event.direction == "left": new_group = "todo"
            elif event.direction == "right": new_group = "done"
        elif current_col_id == "done":
            if event.direction == "left": new_group = "in_progress"

        if new_group:
            # Map group to a specific status string appropriate for the task
            # This is tricky because different sources expect different strings.
            # We will send a generic canonical status, and TaskManager will translate.
            canonical_status = {
                "todo": "PENDING",
                "in_progress": "IN_PROGRESS",
                "done": "COMPLETED"
            }[new_group]

            self.post_message(self.StatusUpdate(event.card_id, canonical_status))

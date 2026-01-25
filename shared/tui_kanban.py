from textual.app import ComposeResult
from textual.widgets import Label, Static
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual import on
from shared.task_manager import Task

class KanbanCard(Static):
    """A card representing a task in the Kanban board."""

    class Move(Message):
        """Message sent when a card is moved."""
        def __init__(self, card: "KanbanCard", direction: str):
            self.card = card
            self.direction = direction
            super().__init__()

    def __init__(self, task: Task):
        super().__init__(classes="kanban-card")
        self.kanban_task = task
        self.can_focus = True

    def compose(self) -> ComposeResult:
        priority_class = f"priority-{self.kanban_task.priority.lower()}"

        yield Label(self.kanban_task.title, classes="card-title")
        yield Label(f"{self.kanban_task.id} | {self.kanban_task.source}", classes="card-meta")
        yield Label(self.kanban_task.priority, classes=f"card-priority {priority_class}")

    def on_key(self, event) -> None:
        if event.key == "h" or event.key == "left":
            self.post_message(self.Move(self, "left"))
        elif event.key == "l" or event.key == "right":
            self.post_message(self.Move(self, "right"))

class KanbanColumn(VerticalScroll):
    """A column in the Kanban board."""

    def __init__(self, title: str, id: str):
        super().__init__(id=id, classes="kanban-column")
        self.column_title = title

    def compose(self) -> ComposeResult:
        yield Label(self.column_title, classes="column-header")
        # Cards added dynamically

class KanbanBoard(Horizontal):
    """The Kanban board container."""

    class StatusUpdate(Message):
        """Message emitted when a task status changes."""
        def __init__(self, task_id: str, new_status: str, source: str):
            self.task_id = task_id
            self.new_status = new_status
            self.source = source
            super().__init__()

    def __init__(self):
        super().__init__(id="kanban-board")
        self.cols = {
            "todo": KanbanColumn("To Do", id="col-todo"),
            "inprogress": KanbanColumn("In Progress", id="col-inprogress"),
            "done": KanbanColumn("Done", id="col-done")
        }

    def compose(self) -> ComposeResult:
        yield self.cols["todo"]
        yield self.cols["inprogress"]
        yield self.cols["done"]

    def clear(self):
        for col in self.cols.values():
            # Remove all children except header (which is usually the first child)
            # Safe way: iterate children and remove if it's a KanbanCard
            to_remove = [child for child in col.children if isinstance(child, KanbanCard)]
            for child in to_remove:
                child.remove()

    def add_task(self, task: Task):
        status = task.status.lower()
        col = None

        # Normalize status
        if status in ["open", "to do", "pending", "todo", "new"]:
            col = self.cols["todo"]
        elif status in ["in progress", "in_progress", "active", "review"]:
            col = self.cols["inprogress"]
        elif status in ["done", "closed", "completed", "resolved"]:
            col = self.cols["done"]
        else:
            # Default to Todo
            col = self.cols["todo"]

        col.mount(KanbanCard(task))

    @on(KanbanCard.Move)
    def on_card_move(self, event: KanbanCard.Move) -> None:
        card = event.card
        current_col = card.parent
        if not isinstance(current_col, KanbanColumn):
            return

        target_col = None
        new_status = ""

        # Determine target column and status
        if current_col.id == "col-todo":
            if event.direction == "right":
                target_col = self.cols["inprogress"]
                new_status = "In Progress"
        elif current_col.id == "col-inprogress":
            if event.direction == "left":
                target_col = self.cols["todo"]
                new_status = "To Do"
            elif event.direction == "right":
                target_col = self.cols["done"]
                new_status = "Done"
        elif current_col.id == "col-done":
            if event.direction == "left":
                target_col = self.cols["inprogress"]
                new_status = "In Progress"

        if target_col:
            # Move card in UI
            card.remove()
            target_col.mount(card)
            card.focus() # Keep focus

            # Emit status update
            self.post_message(self.StatusUpdate(card.kanban_task.id, new_status, card.kanban_task.source))

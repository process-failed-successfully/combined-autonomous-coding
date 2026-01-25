from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Button, Label
from textual.message import Message
from textual import on
from textual.binding import Binding
from dataclasses import dataclass

@dataclass
class KanbanTask:
    id: str
    title: str
    status: str # "todo", "in_progress", "done"
    priority: str
    source: str

class TaskMoved(Message):
    """Message sent when a task is moved to another column."""
    def __init__(self, task_id: str, new_status: str, source_column: str):
        self.task_id = task_id
        self.new_status = new_status
        self.source_column = source_column
        super().__init__()

class KanbanCard(Static):
    """A card representing a task in the Kanban board."""

    DEFAULT_CSS = """
    KanbanCard {
        background: $panel;
        border: solid $primary;
        height: auto;
        margin-bottom: 1;
        padding: 1;
    }
    KanbanCard:focus {
        border: double $accent;
        background: $primary-darken-2;
    }
    KanbanCard .title {
        text-style: bold;
    }
    KanbanCard .meta {
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("left", "move_left", "Move Left"),
        Binding("right", "move_right", "Move Right"),
    ]

    def __init__(self, task: KanbanTask, **kwargs):
        super().__init__(**kwargs)
        self.kanban_task = task
        self.can_focus = True

    def compose(self) -> ComposeResult:
        priority_color = "green"
        if self.kanban_task.priority.lower() == "high":
            priority_color = "red"
        elif self.kanban_task.priority.lower() == "medium":
            priority_color = "yellow"

        yield Label(self.kanban_task.title, classes="title")
        yield Label(f"[{priority_color}]{self.kanban_task.priority}[/] | {self.kanban_task.source} | {self.kanban_task.id}", classes="meta")

    def action_move_left(self):
        self.post_message(TaskMoved(self.kanban_task.id, "prev", self.kanban_task.status))

    def action_move_right(self):
        self.post_message(TaskMoved(self.kanban_task.id, "next", self.kanban_task.status))


class KanbanColumn(Vertical):
    """A column in the Kanban board."""

    DEFAULT_CSS = """
    KanbanColumn {
        width: 1fr;
        height: 100%;
        border: solid $secondary;
        margin: 1;
        padding: 1;
    }
    KanbanColumn Label.header {
        text-align: center;
        width: 100%;
        background: $primary;
        color: $text;
        padding: 1;
        text-style: bold;
        margin-bottom: 1;
    }
    """

    def __init__(self, title: str, status_id: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.status_id = status_id

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="header")
        yield ScrollableContainer(id=f"col-{self.status_id}")

    def add_task(self, task: KanbanTask):
        container = self.query_one(ScrollableContainer)
        container.mount(KanbanCard(task))

    def clear_tasks(self):
        container = self.query_one(ScrollableContainer)
        container.remove_children()


class KanbanBoard(Horizontal):
    """The Kanban Board widget."""

    DEFAULT_CSS = """
    KanbanBoard {
        height: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.columns = {
            "todo": KanbanColumn("To Do", "todo"),
            "in_progress": KanbanColumn("In Progress", "in_progress"),
            "done": KanbanColumn("Done", "done"),
        }

    def compose(self) -> ComposeResult:
        for col in self.columns.values():
            yield col

    def clear(self):
        for col in self.columns.values():
            col.clear_tasks()

    def add_task(self, task: KanbanTask):
        # Map task status to column
        status = task.status.lower()
        target_col = "todo" # Default

        if "progress" in status:
            target_col = "in_progress"
        elif "done" in status or "completed" in status or "closed" in status:
            target_col = "done"
        elif "todo" in status or "pending" in status or "open" in status:
            target_col = "todo"

        # Override task status to match column for internal consistency
        task.status = target_col
        self.columns[target_col].add_task(task)

    @on(TaskMoved)
    def on_task_moved(self, event: TaskMoved):
        # Determine new status
        current_status = event.source_column
        new_status = current_status

        order = ["todo", "in_progress", "done"]
        try:
            idx = order.index(current_status)
            if event.new_status == "next":
                if idx < len(order) - 1:
                    new_status = order[idx + 1]
            elif event.new_status == "prev":
                if idx > 0:
                    new_status = order[idx - 1]
        except ValueError:
            pass # Unknown status

        if new_status != current_status:
            # Re-emit with the resolved new status for the parent to handle (update DB/API)
            # We create a new event type or reuse?
            # Ideally the parent (TasksTab) handles the actual update.
            # But we can optimistically move it in UI?
            # Better to let parent reload or confirm.

            # Update event with resolved status and let it bubble
            event.new_status = new_status
            # Propagate
        else:
            event.stop() # No change

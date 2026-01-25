from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, ListView, ListItem
from textual.message import Message
from textual.binding import Binding
from shared.task_manager import Task

class TaskItem(ListItem):
    """A list item representing a task."""
    def __init__(self, label: str, task_id: str, **kwargs):
        super().__init__(Label(label), **kwargs)
        self.task_id = task_id

class KanbanColumn(Vertical):
    """A single column in the Kanban board."""
    def __init__(self, title: str, id: str, **kwargs):
        super().__init__(id=id, **kwargs)
        self.title = title

    def compose(self) -> ComposeResult:
        yield Label(f"[bold]{self.title}[/bold]", classes="kanban-header")
        yield ListView(id=f"list-{self.id}")

class KanbanBoard(Horizontal):
    """The Kanban Board widget containing columns."""

    class StatusChange(Message):
        """Message emitted when a task status changes."""
        def __init__(self, task_id: str, new_status: str):
            self.task_id = task_id
            self.new_status = new_status
            super().__init__()

    BINDINGS = [
        Binding("l", "move_right", "Move Right"),
        Binding("right", "move_right", "Move Right"),
        Binding("h", "move_left", "Move Left"),
        Binding("left", "move_left", "Move Left"),
    ]

    def compose(self) -> ComposeResult:
        # We need classes for styling (e.g. width)
        yield KanbanColumn("To Do", id="col-todo", classes="kanban-col")
        yield KanbanColumn("In Progress", id="col-inprogress", classes="kanban-col")
        yield KanbanColumn("Done", id="col-done", classes="kanban-col")

    def load_tasks(self, tasks: list[Task]):
        col_todo = self.query_one("#col-todo", KanbanColumn).query_one(ListView)
        col_prog = self.query_one("#col-inprogress", KanbanColumn).query_one(ListView)
        col_done = self.query_one("#col-done", KanbanColumn).query_one(ListView)

        col_todo.clear()
        col_prog.clear()
        col_done.clear()

        for task in tasks:
            status = task.status.upper()

            # Create label with some info
            # [SOURCE] Title (Priority)
            prio_color = "white"
            if task.priority == "High": prio_color = "red"
            elif task.priority == "Low": prio_color = "green"

            label_text = f"[{task.source.upper()}] {task.title} ([{prio_color}]{task.priority}[/{prio_color}])"

            item = TaskItem(label_text, task.task_id if hasattr(task, 'task_id') else task.id)

            if status in ["PENDING", "TO DO", "OPEN", "NEW", "TODO"]:
                col_todo.append(item)
            elif status in ["IN_PROGRESS", "IN PROGRESS", "DOING"]:
                col_prog.append(item)
            elif status in ["COMPLETED", "DONE", "CLOSED", "RESOLVED"]:
                col_done.append(item)
            else:
                # Default to Todo
                col_todo.append(item)

    def action_move_right(self):
        self._move_selection(1)

    def action_move_left(self):
        self._move_selection(-1)

    def _move_selection(self, direction: int):
        # Find the focused widget. It should be a ListView or one of its children.
        focused = self.screen.focused

        # Traversing up to find the ListView if an Item is focused (Textual behavior varies by version)
        # But typically ListView handles focus.

        if not isinstance(focused, ListView):
            return

        if focused.index is None:
            return

        item = focused.children[focused.index]
        if not isinstance(item, TaskItem):
            return

        task_id = item.task_id

        # Determine current column based on ListView ID
        # list-col-todo, list-col-inprogress, list-col-done

        current_list_id = focused.id

        new_status = None

        if current_list_id == "list-col-todo":
            if direction == 1: new_status = "IN_PROGRESS"
        elif current_list_id == "list-col-inprogress":
            if direction == 1: new_status = "COMPLETED"
            elif direction == -1: new_status = "PENDING"
        elif current_list_id == "list-col-done":
            if direction == -1: new_status = "IN_PROGRESS"

        if new_status:
            self.post_message(self.StatusChange(task_id, new_status))

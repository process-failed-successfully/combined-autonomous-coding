import unittest
from textual.app import App, ComposeResult
from shared.tui_kanban import KanbanBoard, KanbanTask, KanbanCard, TaskMoved
from textual.containers import ScrollableContainer

class KanbanTestApp(App):
    def compose(self) -> ComposeResult:
        yield KanbanBoard()

class TestKanbanBoard(unittest.IsolatedAsyncioTestCase):
    async def test_add_task(self):
        app = KanbanTestApp()
        async with app.run_test() as pilot:
            board = app.query_one(KanbanBoard)

            task = KanbanTask(id="1", title="Task 1", status="todo", priority="High", source="jira")
            board.add_task(task)

            # Check if task is in "todo" column
            col_todo = board.query_one("#col-todo", ScrollableContainer)
            self.assertEqual(len(col_todo.children), 1)
            card = col_todo.children[0]
            self.assertIsInstance(card, KanbanCard)
            self.assertEqual(card.kanban_task.title, "Task 1")

    async def test_move_task_event(self):
        # Define app with handler
        class HandlingApp(App):
            def __init__(self):
                super().__init__()
                self.messages = []
            def compose(self) -> ComposeResult:
                yield KanbanBoard()
            def on_task_moved(self, event: TaskMoved):
                self.messages.append(event)

        app = HandlingApp()
        async with app.run_test() as pilot:
            board = app.query_one(KanbanBoard)
            task = KanbanTask(id="1", title="Task 1", status="todo", priority="High", source="jira")
            board.add_task(task)

            # Focus card
            card = board.query_one(KanbanCard)
            card.focus()

            # Press right
            await pilot.press("right")

            # Check message
            # Note: TUI tests can be flaky with timing, but run_test context usually handles it.
            # However, message posting is async. pilot.pause() might be needed.
            await pilot.pause()

            self.assertEqual(len(app.messages), 1)
            self.assertEqual(app.messages[0].task_id, "1")
            self.assertEqual(app.messages[0].new_status, "in_progress")

if __name__ == "__main__":
    unittest.main()

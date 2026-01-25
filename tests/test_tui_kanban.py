import unittest
from textual.app import App, ComposeResult
from textual import on
from shared.tui_kanban import KanbanBoard, KanbanCard, KanbanColumn
from shared.task_manager import Task

class KanbanTestApp(App):
    def __init__(self):
        super().__init__()
        self.messages = []

    def compose(self) -> ComposeResult:
        yield KanbanBoard()

    @on(KanbanBoard.StatusChanged)
    def on_status_changed(self, message: KanbanBoard.StatusChanged):
        self.messages.append(message)

class TestTuiKanban(unittest.IsolatedAsyncioTestCase):
    async def test_kanban_board_layout(self):
        app = KanbanTestApp()
        async with app.run_test() as pilot:
            board = pilot.app.query_one(KanbanBoard)
            self.assertIsNotNone(board)

            # Check columns
            cols = board.query(KanbanColumn)
            self.assertEqual(len(cols), 3)
            self.assertEqual(cols[0].title, "To Do")
            self.assertEqual(cols[1].title, "In Progress")
            self.assertEqual(cols[2].title, "Done")

    async def test_add_task(self):
        app = KanbanTestApp()
        async with app.run_test() as pilot:
            board = pilot.app.query_one(KanbanBoard)

            task = Task(id="1", source="sprint", title="Test Task", status="PENDING", priority="High")
            board.add_task(task)

            # Allow mount to propagate
            await pilot.pause()

            col_todo = board.query_one("#col-todo", KanbanColumn)
            cards = col_todo.query(KanbanCard)
            self.assertEqual(len(cards), 1)
            self.assertEqual(cards[0].kanban_task.title, "Test Task")

    async def test_move_task(self):
        app = KanbanTestApp()
        async with app.run_test() as pilot:
            board = pilot.app.query_one(KanbanBoard)
            task = Task(id="1", source="sprint", title="Test Task", status="PENDING", priority="High")
            board.add_task(task)

            await pilot.pause()

            # Find the card
            card = board.query(KanbanCard).first()

            # Click "Next" using class selector
            await pilot.click(".move-right")

            # Check message
            self.assertTrue(len(app.messages) > 0)
            msg = app.messages[0]
            self.assertEqual(msg.task_id, "1")
            self.assertEqual(msg.new_status, "In Progress")

if __name__ == "__main__":
    unittest.main()

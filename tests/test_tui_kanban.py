import unittest
from unittest.mock import patch
from textual.app import App, ComposeResult
from shared.tui_kanban import KanbanBoard, KanbanCard, KanbanColumn
from shared.task_manager import Task

class KanbanApp(App):
    def compose(self) -> ComposeResult:
        yield KanbanBoard()

class TestTUIKanban(unittest.IsolatedAsyncioTestCase):
    async def test_kanban_board_load_tasks(self):
        app = KanbanApp()
        async with app.run_test():
            board = app.query_one(KanbanBoard)

            tasks = [
                Task(id="1", source="test", title="Task 1", status="PENDING", priority="High"),
                Task(id="2", source="test", title="Task 2", status="IN_PROGRESS", priority="Medium"),
                Task(id="3", source="test", title="Task 3", status="COMPLETED", priority="Low"),
            ]

            board.load_tasks(tasks)

            # Check if tasks are distributed correctly
            col_todo = board.query_one("#col-todo", KanbanColumn)
            col_prog = board.query_one("#col-prog", KanbanColumn)
            col_done = board.query_one("#col-done", KanbanColumn)

            self.assertEqual(len(col_todo.query(KanbanCard)), 1)
            self.assertEqual(len(col_prog.query(KanbanCard)), 1)
            self.assertEqual(len(col_done.query(KanbanCard)), 1)

            card1 = col_todo.query(KanbanCard).first()
            self.assertEqual(card1.kanban_task.title, "Task 1")

    async def test_kanban_card_move_logic(self):
        app = KanbanApp()
        async with app.run_test():
            board = app.query_one(KanbanBoard)
            task = Task(id="1", source="test", title="Task 1", status="PENDING", priority="High")
            board.load_tasks([task])

            # Mock post_message to intercept StatusUpdate
            with patch.object(board, 'post_message') as mock_post:
                # Simulate move right from Todo -> In Progress
                move_event = KanbanCard.Move(card_id="1", direction="right")
                board.on_card_move(move_event)

                self.assertTrue(mock_post.called)
                args = mock_post.call_args[0]
                message = args[0]
                self.assertIsInstance(message, KanbanBoard.StatusUpdate)
                self.assertEqual(message.task_id, "1")
                self.assertEqual(message.new_status, "IN_PROGRESS")

if __name__ == "__main__":
    unittest.main()

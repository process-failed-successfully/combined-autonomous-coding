import unittest
from textual.widgets import Label
from shared.tui_kanban import KanbanBoard, KanbanCard, KanbanColumn
from shared.task_manager import Task

class TestTUIKanban(unittest.IsolatedAsyncioTestCase):
    async def test_kanban_card(self):
        task = Task(id="1", source="sprint", title="Test Task", status="PENDING", priority="High")
        card = KanbanCard(task)

        self.assertEqual(card.kanban_task.title, "Test Task")

        widgets = list(card.compose())

        found_title = False
        found_priority = False

        for w in widgets:
            if isinstance(w, Label):
                # Try to extract text content. Textual Label usually wraps a Rich Renderable.
                # In 0.70+, accessing it might be via .render()
                try:
                    # Check if render() returns a renderable that converts to str
                    content = str(w.render())
                except Exception:
                    content = ""

                if "Test Task" in content:
                    found_title = True
                if "High" in content:
                    found_priority = True

        self.assertTrue(found_title, "Title label not found in card composition")
        self.assertTrue(found_priority, "Priority label not found in card composition")

    async def test_kanban_board_structure(self):
        board = KanbanBoard()
        cols = list(board.compose())
        self.assertEqual(len(cols), 3)
        ids = [c.id for c in cols]
        self.assertIn("col-todo", ids)
        self.assertIn("col-inprogress", ids)
        self.assertIn("col-done", ids)

if __name__ == "__main__":
    unittest.main()

from pathlib import Path
from typing import List, Dict, Optional, Any
from shared.todos import scan_todos, get_todo_blame


class TodoLabManager:
    """
    Manages TODO operations: scanning, fetching blame info.
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def get_todos(self, tags: Optional[List[str]] = None, exclude_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Scans the project for TODOs."""
        return scan_todos(self.project_dir, tags=tags, exclude_paths=exclude_paths)

    def get_blame(self, file_path: str, line_num: int) -> Dict[str, str]:
        """Fetches git blame information for a specific TODO."""
        return get_todo_blame(self.project_dir, file_path, line_num)

    def get_todos_with_blame(self, tags: Optional[List[str]] = None, exclude_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Scans the project for TODOs and fetches blame information for each."""
        todos = self.get_todos(tags=tags, exclude_paths=exclude_paths)
        for todo in todos:
            blame = self.get_blame(todo['file'], todo['line'])
            todo['author'] = blame.get('author', 'Unknown')
            todo['date'] = blame.get('date', 'Unknown')
        return todos


def run_todo_lab_logic(args):
    """CLI Entry point for Todo Lab."""
    # This might not be fully needed if we stick with `run_todos` in main.py,
    # but provides a dedicated entry point for consistency if we want.
    pass

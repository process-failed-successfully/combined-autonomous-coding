from pathlib import Path
from typing import List, Optional


class TreeLabManager:
    def __init__(self, exclude: Optional[List[str]] = None):
        if exclude is None:
            self.exclude = [".git", "__pycache__", "node_modules", ".venv", "venv"]
        else:
            self.exclude = exclude

    def generate_tree(self, dir_path: Path, max_depth: int = -1, prefix: str = "", current_depth: int = 0) -> str:
        """
        Generates an ASCII tree representation of the given directory.
        """
        if not dir_path.is_dir():
            return f"Error: {dir_path} is not a directory."

        # Sort files and directories, directories first
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return prefix + "[Permission Denied]\n"

        entries = [e for e in entries if e.name not in self.exclude]

        tree_str = ""
        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            tree_str += f"{prefix}{connector}{entry.name}\n"

            if entry.is_dir():
                if max_depth == -1 or current_depth < max_depth:
                    extension = "    " if is_last else "│   "
                    tree_str += self.generate_tree(entry, max_depth, prefix + extension, current_depth + 1)

        return tree_str


def run_tree_lab_logic(args):
    """CLI logic for the tree-lab command."""
    manager = TreeLabManager(exclude=args.exclude)

    target_dir = Path(args.dir)
    if not target_dir.exists():
        print(f"Error: Directory '{target_dir}' does not exist.")
        return

    print(f"{target_dir.resolve().name}/")
    print(manager.generate_tree(target_dir, max_depth=args.max_depth), end="")

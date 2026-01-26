"""
Snippet Manager
===============

Manages reusable code snippets stored in the project's .agent_snippets directory.
"""

import os
from pathlib import Path
from typing import List, Optional

class SnippetManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.snippets_dir = self.project_dir / ".agent_snippets"
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.snippets_dir.exists():
            self.snippets_dir.mkdir(parents=True, exist_ok=True)

    def list_snippets(self) -> List[str]:
        """Returns a list of snippet names."""
        if not self.snippets_dir.exists():
            return []
        return sorted([f.name for f in self.snippets_dir.iterdir() if f.is_file()])

    def get_snippet(self, name: str) -> Optional[str]:
        """Returns the content of a snippet."""
        path = self.snippets_dir / name
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8", errors="replace")

    def create_snippet(self, name: str, content: str) -> Path:
        """Creates or overwrites a snippet."""
        self._ensure_dir()
        path = self.snippets_dir / name
        path.write_text(content, encoding="utf-8")
        return path

    def delete_snippet(self, name: str) -> bool:
        """Deletes a snippet."""
        path = self.snippets_dir / name
        if path.exists():
            path.unlink()
            return True
        return False

    def apply_snippet(self, name: str, target_file: Path, mode: str = "append") -> bool:
        """
        Applies a snippet to a target file.
        mode: "append" (default), "overwrite", "prepend"
        """
        content = self.get_snippet(name)
        if content is None:
            return False

        if not target_file.exists():
            # If file doesn't exist, create it regardless of mode
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(content, encoding="utf-8")
            return True

        original_content = target_file.read_text(encoding="utf-8", errors="replace")
        new_content = ""

        if mode == "overwrite":
            new_content = content
        elif mode == "prepend":
            new_content = content + "\n" + original_content
        else: # append
            if original_content and not original_content.endswith("\n"):
                original_content += "\n"
            new_content = original_content + content

        target_file.write_text(new_content, encoding="utf-8")
        return True

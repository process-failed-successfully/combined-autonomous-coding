import os
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional
import shutil

class PathLabManager:
    """Manages path operations: inspection, calculation, and globbing."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir or Path.cwd()

    def inspect_path(self, path_str: str) -> Dict[str, Any]:
        """Returns details about a path."""
        try:
            p = Path(path_str)
            resolved = p.resolve()
        except Exception as e:
            return {"error": str(e)}

        info = {
            "input": path_str,
            "parts": p.parts,
            "drive": p.drive,
            "root": p.root,
            "anchor": p.anchor,
            "name": p.name,
            "stem": p.stem,
            "suffix": p.suffix,
            "suffixes": p.suffixes,
            "parent": str(p.parent),
            "absolute": str(p.absolute()),
            "resolved": str(resolved),
            "exists": p.exists(),
            "is_symlink": p.is_symlink(),
            "is_file": p.is_file(),
            "is_dir": p.is_dir(),
            "is_absolute": p.is_absolute(),
            "is_reserved": p.is_reserved() if hasattr(p, 'is_reserved') else False,
        }

        if p.exists():
            try:
                stat = p.stat()
                info.update({
                    "size": stat.st_size,
                    "owner": stat.st_uid, # Getting name requires pwd module, potentially unavailable on Windows
                    "group": stat.st_gid,
                    "permissions_octal": oct(stat.st_mode)[-3:],
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                })
            except Exception as e:
                info["stat_error"] = str(e)

        return info

    def resolve_path(self, path_str: str, strict: bool = False) -> str:
        """Resolves a path to its absolute form."""
        try:
            return str(Path(path_str).resolve(strict=strict))
        except Exception as e:
            return f"Error: {e}"

    def calculate_relative(self, target: str, start: str) -> str:
        """Calculates relative path from start to target."""
        try:
            return os.path.relpath(target, start)
        except Exception as e:
            return f"Error: {e}"

    def join_paths(self, paths: List[str]) -> str:
        """Joins multiple path components."""
        try:
            return str(Path(*paths))
        except Exception as e:
            return f"Error: {e}"

    def expand_user(self, path_str: str) -> str:
        """Expands user home directory (~)."""
        try:
            return str(Path(path_str).expanduser())
        except Exception as e:
            return f"Error: {e}"

    def glob_search(self, base_dir: str, pattern: str, recursive: bool = False) -> List[str]:
        """Searches for files matching a glob pattern."""
        try:
            base = Path(base_dir).expanduser().resolve()
            if not base.is_dir():
                return [f"Error: Base directory '{base}' does not exist or is not a directory."]

            # Use glob module for more flexibility or pathlib.glob
            # pathlib.glob is safer regarding boundaries if we stick to the object

            results = []
            if recursive and "**" in pattern:
                 iterator = base.glob(pattern)
            else:
                 # If pattern is absolute, it ignores base in pathlib? No, pathlib.glob is relative to object.
                 # If user types "*.py", it works.
                 iterator = base.glob(pattern)

            # Limit results to 100 to prevent freezing TUI
            count = 0
            for item in iterator:
                results.append(str(item.relative_to(base)))
                count += 1
                if count >= 100:
                    results.append("... (limit reached)")
                    break

            return results if results else ["No matches found."]

        except Exception as e:
            return [f"Error: {e}"]

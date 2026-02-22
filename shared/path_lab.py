import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional

class PathLabManager:
    """
    Manages path manipulation and analysis operations.
    """

    def analyze_path(self, path_str: str) -> Dict[str, Any]:
        """
        Analyzes a path string and returns detailed properties.
        """
        p = Path(path_str)

        info = {
            "original": path_str,
            "parts": p.parts,
            "anchor": p.anchor,
            "name": p.name,
            "stem": p.stem,
            "suffix": p.suffix,
            "suffixes": p.suffixes,
            "parent": str(p.parent),
            "absolute": str(p.absolute()),
            "is_absolute": p.is_absolute(),
            "exists": False,
            "is_file": False,
            "is_dir": False,
            "is_symlink": False,
            "stat": None,
            "resolved": None
        }

        try:
            resolved = p.resolve()
            info["resolved"] = str(resolved)
        except Exception:
            info["resolved"] = "N/A (Could not resolve)"

        if p.exists():
            info["exists"] = True
            info["is_file"] = p.is_file()
            info["is_dir"] = p.is_dir()
            info["is_symlink"] = p.is_symlink()

            try:
                stat = p.stat()
                info["stat"] = {
                    "size": stat.st_size,
                    "mode": oct(stat.st_mode),
                    "uid": stat.st_uid,
                    "gid": stat.st_gid,
                    "mtime": stat.st_mtime
                }
            except Exception:
                info["stat"] = "Error reading stat"

        return info

    def calculate_relative(self, target: str, start: str) -> Dict[str, Any]:
        """
        Calculates relative path from start to target.
        """
        try:
            target_p = Path(target)
            start_p = Path(start)
            # relative_to requires paths to be on the same drive/root if absolute
            # It strictly checks if target is subpath of start
            # os.path.relpath is more flexible for ".."

            result = os.path.relpath(target, start)
            return {"success": True, "result": result}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}

    def join_paths(self, base: str, parts: List[str]) -> str:
        """
        Joins path components.
        """
        return str(Path(base).joinpath(*parts))

    def glob_path(self, root: str, pattern: str, recursive: bool = False) -> List[str]:
        """
        Runs a glob pattern from a root directory.
        """
        root_path = Path(root)
        if not root_path.exists() or not root_path.is_dir():
            return []

        # Use rglob if recursive, else glob
        # But wait, glob module allows recursive with **
        # pathlib glob is safer

        try:
            if recursive:
                matches = root_path.rglob(pattern)
            else:
                matches = root_path.glob(pattern)

            return [str(p.relative_to(root_path)) for p in matches]
        except Exception as e:
            return [f"Error: {e}"]

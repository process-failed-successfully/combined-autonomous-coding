import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

def format_size(size: int) -> str:
    """Converts bytes to human-readable strings (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def scan_disk_usage(root: Path) -> Dict[str, Any]:
    """
    Recursively scans directory to build a tree with sizes.
    Returns a dictionary structure:
    {
        "name": str,
        "path": Path,
        "size": int,
        "type": "dir" | "file",
        "children": [ ... ] (sorted by size desc)
    }
    """
    try:
        # Check if root exists and is accessible
        if not root.exists():
            return {"name": root.name, "path": root, "size": 0, "type": "unknown", "children": []}

        if root.is_file():
            size = root.stat().st_size
            return {
                "name": root.name,
                "path": root,
                "size": size,
                "type": "file",
                "children": []
            }

        total_size = 0
        children = []

        # Use os.scandir for better performance
        with os.scandir(root) as it:
            for entry in it:
                # Skip symlinks to avoid loops/double counting
                if entry.is_symlink():
                    continue

                entry_path = Path(entry.path)

                if entry.is_file():
                    try:
                        size = entry.stat().st_size
                        total_size += size
                        children.append({
                            "name": entry.name,
                            "path": entry_path,
                            "size": size,
                            "type": "file",
                            "children": []
                        })
                    except OSError:
                        # Permission denied or disappeared
                        pass

                elif entry.is_dir():
                    child_node = scan_disk_usage(entry_path)
                    total_size += child_node["size"]
                    children.append(child_node)

        # Sort children by size descending
        children.sort(key=lambda x: x["size"], reverse=True)

        return {
            "name": root.name,
            "path": root,
            "size": total_size,
            "type": "dir",
            "children": children
        }

    except PermissionError:
        return {"name": root.name, "path": root, "size": 0, "type": "dir", "children": []}
    except Exception as e:
        return {"name": root.name, "path": root, "size": 0, "type": "error", "error": str(e), "children": []}

def get_largest_files(root: Path, limit: int = 20) -> List[Dict[str, Any]]:
    """Returns a flat list of the largest files for quick identification."""
    files = []

    # Use os.walk for flat scanning
    try:
        for dirpath, _, filenames in os.walk(root):
            for f in filenames:
                fp = Path(dirpath) / f
                if fp.is_symlink():
                    continue
                try:
                    size = fp.stat().st_size
                    files.append({
                        "name": f,
                        "path": fp,
                        "size": size,
                        "formatted_size": format_size(size)
                    })
                except OSError:
                    pass
    except Exception:
        pass

    # Sort and slice
    files.sort(key=lambda x: x["size"], reverse=True)
    return files[:limit]

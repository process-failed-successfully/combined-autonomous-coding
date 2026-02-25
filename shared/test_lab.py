import subprocess  # nosec B404
import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

class TestLabManager:
    """
    Manages test discovery and execution.
    """
    __test__ = False

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def collect_tests(self) -> Dict[str, Any]:
        """
        Discovers tests using pytest --collect-only.
        Returns a hierarchical structure.
        """
        try:
            # We use --collect-only and -q to get a flat list of node ids
            # Alternatively, we could try to parse the output more robustly
            cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
            result = subprocess.run(  # nosec B603
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return {"error": result.stderr or result.stdout}

            node_ids = [line for line in result.stdout.splitlines() if line.strip() and not line.startswith("no tests ran")]
            return self._build_tree(node_ids)

        except Exception as e:
            return {"error": str(e)}

    def _build_tree(self, node_ids: List[str]) -> Dict[str, Any]:
        """
        Converts a list of node IDs into a tree structure.
        Node ID format: path/to/file.py::ClassName::test_method
        """
        tree = {"name": "root", "children": [], "type": "directory"}

        for node_id in node_ids:
            parts = node_id.split("::")
            file_path = parts[0]
            test_parts = parts[1:]

            # 1. Handle File Path
            path_segments = file_path.split(os.sep)
            current_level = tree

            for i, segment in enumerate(path_segments):
                # Find existing child
                found = next((c for c in current_level["children"] if c["name"] == segment), None)
                if not found:
                    is_file = (i == len(path_segments) - 1)
                    new_node = {
                        "name": segment,
                        "children": [],
                        "type": "file" if is_file else "directory",
                        "path": os.path.join(*path_segments[:i+1]) if i > 0 else segment
                    }
                    # If it's a file, the id is the file path (for running all tests in file)
                    if is_file:
                        new_node["id"] = file_path

                    current_level["children"].append(new_node)
                    current_level = new_node
                else:
                    current_level = found

            # 2. Handle Test Parts (Class / Method)
            # current_level is now the file node
            parent_node = current_level
            current_id = file_path

            for part in test_parts:
                current_id += f"::{part}"
                found = next((c for c in parent_node["children"] if c["name"] == part), None)
                if not found:
                    # Guess type: usually starts with Test -> Class, test_ -> Function
                    # But simpler: leaf is test, intermediate is suite/class
                    is_leaf = (part == test_parts[-1])
                    new_node = {
                        "name": part,
                        "children": [],
                        "type": "test" if is_leaf else "suite",
                        "id": current_id
                    }
                    parent_node["children"].append(new_node)
                    parent_node = new_node
                else:
                    parent_node = found

        return tree

    def run_tests(self, node_id: str = None) -> Dict[str, Any]:
        """
        Runs tests for a given node ID (or all if None).
        Returns execution result.
        """
        cmd = [sys.executable, "-m", "pytest"]
        if node_id:
            cmd.append(node_id)

        # Add verbose flag to get more info
        cmd.append("-v")
        # Add -rA to show extra summary info
        cmd.append("-rA")

        try:
            result = subprocess.run(  # nosec B603
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e), "output": ""}

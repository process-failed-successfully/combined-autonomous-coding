"""
Code Map Generator
==================

Generates a visualization of the project's internal structure (files, classes, functions).
"""

import ast
import json
import concurrent.futures
import multiprocessing
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple

# Re-use existing utility for finding Python files
from shared.complexity import get_python_files


class CodeNode:
    def __init__(self, name: str, type: str, file: str, lineno: int, end_lineno: Optional[int] = None):
        self.name = name
        self.type = type  # 'module', 'class', 'function'
        self.file = file
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.children: List['CodeNode'] = []
        self.dependencies: Set[str] = set()  # references to other nodes (e.g. imports)

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "file": self.file,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
            "children": [c.to_dict() for c in self.children],
            "dependencies": list(sorted(self.dependencies))
        }


class PythonMapBuilder(ast.NodeVisitor):
    def __init__(self, file_path: Path, project_root: Path):
        self.file_path = file_path
        self.project_root = project_root
        try:
            self.rel_path = str(file_path.relative_to(project_root))
        except ValueError:
            self.rel_path = str(file_path)

        # Root node for this file
        self.module_node = CodeNode(self.rel_path, 'module', self.rel_path, 0)
        self.current_scope = self.module_node
        self.stack = [self.module_node]

    def visit_ClassDef(self, node):
        end_lineno = getattr(node, 'end_lineno', None)
        class_node = CodeNode(node.name, 'class', self.rel_path, node.lineno, end_lineno)
        self.current_scope.children.append(class_node)

        self.stack.append(class_node)
        self.current_scope = class_node

        self.generic_visit(node)

        self.stack.pop()
        self.current_scope = self.stack[-1]

    def visit_FunctionDef(self, node):
        end_lineno = getattr(node, 'end_lineno', None)
        func_node = CodeNode(node.name, 'function', self.rel_path, node.lineno, end_lineno)
        self.current_scope.children.append(func_node)

        self.stack.append(func_node)
        self.current_scope = func_node

        self.generic_visit(node)

        self.stack.pop()
        self.current_scope = self.stack[-1]

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.module_node.dependencies.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.module_node.dependencies.add(node.module)
        self.generic_visit(node)


def _process_file_map(file_path: Path, project_dir: Path) -> Optional[Tuple[str, CodeNode]]:
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
        builder = PythonMapBuilder(file_path, project_dir)
        builder.visit(tree)
        return (builder.rel_path, builder.module_node)
    except Exception:
        return None


PARALLEL_THRESHOLD = 10


def _scan_sequential(py_files: List[Path], project_dir: Path) -> Dict[str, CodeNode]:
    """Helper for sequential scanning."""
    map_data = {}
    for f in py_files:
        result = _process_file_map(f, project_dir)
        if result:
            map_data[result[0]] = result[1]
    return map_data


def scan_project(project_dir: Path) -> Dict[str, CodeNode]:
    """Scans the project directory and builds a map of the code structure."""
    py_files = get_python_files(project_dir)

    if len(py_files) < PARALLEL_THRESHOLD:
        # Run sequentially for small projects to avoid multiprocessing overhead
        return _scan_sequential(py_files, project_dir)
    else:
        try:
            # Use 'spawn' to ensure a clean process environment, preventing issues with
            # pytest-cov or other tools that might interfere with 'fork' behavior.
            ctx = multiprocessing.get_context("spawn")
            map_data = {}
            with concurrent.futures.ProcessPoolExecutor(mp_context=ctx) as executor:
                futures = [executor.submit(_process_file_map, f, project_dir) for f in py_files]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            map_data[result[0]] = result[1]
                    except Exception:
                        # Ignore worker errors to prevent crash
                        pass
            return map_data
        except Exception as e:
            # Fallback to sequential execution if parallel execution fails (e.g., resource limits)
            print(f"Parallel scan failed: {e}. Falling back to sequential.")
            return _scan_sequential(py_files, project_dir)


def generate_mermaid(map_data: Dict[str, CodeNode], focus_file: Optional[str] = None) -> str:
    """Generates a Mermaid class diagram from the map data."""
    lines = ["classDiagram"]

    # Filter if focus_file is provided
    # If focus_file, only show that file and things connected to it (direct neighbors)
    relevant_files = set()
    if focus_file:
        for file, node in map_data.items():
            if focus_file in file:
                relevant_files.add(file)
                # Add imports as neighbors (rough approximation as imports are module names, not file paths directly)
                # But we can try to match known file paths that look like the import
                # For now, simplistic approach: just the file itself.
                # Improving neighbor detection would require mapping imports to file paths.
    else:
        relevant_files = set(map_data.keys())

    # Build Diagram
    for file_path, node in map_data.items():
        if focus_file and file_path not in relevant_files:
            continue

        # Sanitize name for Mermaid class ID
        safe_id = file_path.replace("/", "_").replace(".", "_").replace("-", "_")

        lines.append(f"    class {safe_id} {{")
        lines.append(f"        <<{file_path}>>")

        # List Top-Level Classes and Functions
        for child in node.children:
            if child.type == 'class':
                lines.append(f"        class {child.name}")
            elif child.type == 'function':
                lines.append(f"        {child.name}()")

        lines.append("    }")

        # Add Relationships (Imports)
        # We try to link to other known files in the map
        for dep in node.dependencies:
            # dep is a module path like 'shared.utils'
            # We check if 'shared/utils.py' exists in our map keys
            potential_match = dep.replace(".", "/") + ".py"

            # Try exact match
            matched_key = None
            if potential_match in map_data:
                matched_key = potential_match
            else:
                # Try finding it as a suffix? e.g. import utils -> shared/utils.py
                # This is risky, let's just stick to direct translation for now.
                pass

            if matched_key and (not focus_file or matched_key in relevant_files or file_path in relevant_files):
                safe_dep_id = matched_key.replace("/", "_").replace(".", "_").replace("-", "_")
                lines.append(f"    {safe_id} ..> {safe_dep_id} : imports")

    return "\n".join(lines)


def _run_map_logic(project_dir: Path, output_format: str, focus: Optional[str] = None):
    data = scan_project(project_dir)

    if output_format == "json":
        # Convert to dict
        json_data = {k: v.to_dict() for k, v in data.items()}
        print(json.dumps(json_data, indent=2))
    elif output_format == "mermaid":
        print(generate_mermaid(data, focus_file=focus))
    else:
        # Simple text representation
        for file_path, node in data.items():
            if focus and focus not in file_path:
                continue
            print(f"📦 {file_path}")
            for child in node.children:
                prefix = "C" if child.type == 'class' else "F"
                print(f"  ├─ [{prefix}] {child.name}")
                if child.children:
                    for grandchild in child.children:
                        prefix_gc = "C" if grandchild.type == 'class' else "F"
                        print(f"  │    ├─ [{prefix_gc}] {grandchild.name}")
            if node.dependencies:
                print(f"  └─ Imports: {', '.join(list(node.dependencies)[:5])}...")
            print("")

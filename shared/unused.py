import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
import fnmatch

class UnusedCodeDetector:
    def __init__(self, project_dir: Path, file_pattern: str = "*.py", ignore_patterns: Optional[List[str]] = None):
        self.project_dir = project_dir
        self.file_pattern = file_pattern
        self.ignore_patterns = ignore_patterns or []

        # storage
        self.definitions: List[Dict[str, Any]] = [] # {name, type, file, lineno}
        self.usages: Set[str] = set()

        # Stats
        self.scanned_files = 0

    def is_ignored(self, file_path: Path) -> bool:
        rel_path = str(file_path.relative_to(self.project_dir))
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # Also match directories
            if pattern.endswith("/") and rel_path.startswith(pattern):
                return True
        return False

    def scan(self):
        """Scans the project for definitions and usages."""
        for root, dirs, files in os.walk(self.project_dir):
            # Filtering dirs
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

            for file in files:
                if not fnmatch.fnmatch(file, self.file_pattern):
                    continue

                file_path = Path(root) / file
                if self.is_ignored(file_path):
                    continue

                self.scan_file(file_path)

    def scan_file(self, file_path: Path):
        self.scanned_files += 1
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)

            visitor = SymbolVisitor(file_path, self.project_dir)
            visitor.visit(tree)

            self.definitions.extend(visitor.definitions)
            self.usages.update(visitor.usages)

        except Exception:
            # Skip files that can't be parsed
            pass

    def get_unused_definitions(self) -> List[Dict[str, Any]]:
        """Returns a list of definitions that have no recorded usages."""
        unused = []
        for defn in self.definitions:
            name = defn['name']

            # Skip special methods
            if name.startswith("__") and name.endswith("__"):
                continue

            # Naive check: is the name in the usage set?
            # Note: This has false negatives (if the name is used in a string or comment, or by another unrelated object)
            # But it minimizes false positives (flagging something as unused when it IS used)
            if name not in self.usages:
                unused.append(defn)

        return sorted(unused, key=lambda x: (str(x['file']), int(x['lineno'])))

class SymbolVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path, project_root: Path):
        self.file_path = file_path
        try:
            self.rel_path = str(file_path.relative_to(project_root))
        except ValueError:
            self.rel_path = str(file_path)

        self.definitions: List[Dict[str, Any]] = []
        self.usages: Set[str] = set()

    def visit_FunctionDef(self, node):
        self.definitions.append({
            "name": node.name,
            "type": "function",
            "file": self.rel_path,
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.definitions.append({
            "name": node.name,
            "type": "async_function",
            "file": self.rel_path,
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.definitions.append({
            "name": node.name,
            "type": "class",
            "file": self.rel_path,
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.usages.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # In x.y, 'y' is the attribute. 'x' is the value (visited separately)
        self.usages.add(node.attr)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        # from x import y -> y is a definition in that file, but 'x' is a usage of module x
        # usage of 'y' inside this file is handled by Name nodes later if used.
        # But wait, 'from shared import unused' -> 'unused' is defined in current namespace.
        # It's not a definition WE created, so we don't add to self.definitions.
        # But we should mark 'shared' as used?
        if node.module:
            parts = node.module.split('.')
            self.usages.update(parts)
        self.generic_visit(node)

def _run_unused_logic(project_dir: Path, files: Optional[str] = None, ignore: Optional[str] = None):
    """
    Main entry point for CLI.
    """
    # Parse patterns
    file_pattern = files if files else "*.py"
    ignore_patterns = [p.strip() for p in ignore.split(",")] if ignore else []

    # Defaults ignores
    if not ignore:
        ignore_patterns = [".git*", "venv*", "tests*", "*test_*"]

    print(f"--- Unused Code Detection in: {project_dir} ---")
    print(f"Scanning pattern: {file_pattern}")
    print(f"Ignoring: {', '.join(ignore_patterns)}")

    detector = UnusedCodeDetector(project_dir, file_pattern, ignore_patterns)
    detector.scan()

    unused = detector.get_unused_definitions()

    if not unused:
        print("\n✅ No unused definitions found (based on name matching).")
        return

    print(f"\nFound {len(unused)} potentially unused definitions:")

    # Group by file
    by_file: Dict[str, List[Dict[str, Any]]] = {}
    for item in unused:
        f = str(item['file'])
        if f not in by_file:
            by_file[f] = []
        by_file[f].append(item)

    for f in sorted(by_file.keys()):
        print(f"\n📄 {f}")
        for item in by_file[f]:
            print(f"  Line {str(item['lineno']):<4} [{item['type']}] {item['name']}")

    print("\nNote: This is a heuristic scan based on name matching.")
    print("      It may have false negatives (missed unused items) if names collide.")
    print("      Dynamic usage (getattr) is not detected.")

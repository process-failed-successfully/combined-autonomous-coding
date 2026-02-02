import ast
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

class DependencyGraph:
    """Analyzes file-level dependencies (imports)."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def get_imports(self, file_path: Path) -> List[Path]:
        """Returns a list of files imported by the given file."""
        if file_path.suffix == '.py':
            return self._get_python_imports(file_path)
        # Add support for other languages here (JS/TS via regex)
        return []

    def _get_python_imports(self, file_path: Path) -> List[Path]:
        imports = set()
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
        except Exception:
            return []

        for node in ast.walk(tree):
            module_name = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    self._resolve_and_add(module_name, file_path, imports)
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module
                level = node.level
                if module_name:
                    self._resolve_and_add(module_name, file_path, imports, level)
                elif level > 0:
                    # Relative import without module name (e.g. from . import foo)
                    # We need to look at names
                    # This is tricky because 'foo' could be a file or a function.
                    # Simplified: assume we resolve the parent package
                    pass

        return sorted(list(imports))

    def _resolve_and_add(self, module_name: str, current_file: Path, imports: Set[Path], level: int = 0):
        """Resolves a module name to a file path."""
        if not module_name:
            return

        resolved = self._resolve_python_path(module_name, current_file, level)
        if resolved and resolved.exists():
            imports.add(resolved)

    def _resolve_python_path(self, module_name: str, current_file: Path, level: int) -> Optional[Path]:
        """
        Resolves a Python module path to a file path.
        Handles absolute (project-root relative) and relative imports.
        """
        parts = module_name.split('.')

        start_dir = current_file.parent
        if level > 0:
            for _ in range(level - 1):
                start_dir = start_dir.parent

        # 1. Check relative to current file/level
        if level > 0:
            candidate = start_dir.joinpath(*parts).with_suffix('.py')
            if candidate.exists():
                return candidate
            candidate = start_dir.joinpath(*parts) / "__init__.py"
            if candidate.exists():
                return candidate

        # 2. Check relative to project root (Absolute imports)
        candidate = self.project_dir.joinpath(*parts).with_suffix('.py')
        if candidate.exists():
            return candidate
        candidate = self.project_dir.joinpath(*parts) / "__init__.py"
        if candidate.exists():
            return candidate

        # 3. Handle shared.* or agents.* specific to this project structure
        # If the project dir *contains* shared, then 'import shared.utils' works.
        # But if we are running FROM the root, it matches logic #2.

        return None

class TestDiscoverer:
    """Finds tests related to a source file."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def find_tests(self, source_file: Path) -> List[Path]:
        """Heuristically finds test files."""
        tests = []
        name = source_file.stem

        # Common patterns
        patterns = [
            f"test_{name}.py",
            f"{name}_test.py",
            f"tests/test_{name}.py",
            f"tests/{name}_test.py",
            # Nested mirrors: src/utils.py -> tests/test_utils.py or tests/src/test_utils.py
        ]

        # Scan for matches
        # 1. Direct name match in tests/ folder
        tests_dir = self.project_dir / "tests"
        if tests_dir.exists():
            for p in patterns:
                candidate = self.project_dir / p
                if candidate.exists() and candidate != source_file:
                    tests.append(candidate)

            # Also search recursively in tests/ for test_{name}.py
            for t in tests_dir.rglob(f"test_{name}.py"):
                if t != source_file:
                    tests.append(t)

        return sorted(list(set(tests)))

class TemporalCoupling:
    """Analyzes git history for co-changed files."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.git_path = shutil.which("git")

    def analyze(self, target_file: Path, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.git_path or not (self.project_dir / ".git").is_dir():
            return []

        try:
            rel_path = target_file.relative_to(self.project_dir)
        except ValueError:
            return []

        # Get commits that touched this file
        cmd = [
            self.git_path, "-C", str(self.project_dir),
            "log", "--pretty=format:%H", "--follow", "--", str(rel_path)
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            hashes = result.stdout.strip().splitlines()
        except subprocess.CalledProcessError:
            return []

        if not hashes:
            return []

        # Limit analysis to recent N commits involving this file
        # (Though argument 'limit' usually refers to output limit, let's limit history depth for perf)
        recent_hashes = hashes[:50]

        file_counts = Counter()

        for h in recent_hashes:
            cmd_show = [
                self.git_path, "-C", str(self.project_dir),
                "show", "--name-only", "--pretty=format:", h
            ]
            try:
                res = subprocess.run(cmd_show, capture_output=True, text=True)
                files = res.stdout.strip().splitlines()
                for f in files:
                    if f and f != str(rel_path):
                        file_counts[f] += 1
            except Exception:
                continue

        # Format results
        coupling = []
        for f, count in file_counts.most_common(limit):
            coupling.append({
                "file": f,
                "count": count,
                "strength": count / len(recent_hashes) # rudimentary strength metric
            })

        return coupling

class SmartContextManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.dep_graph = DependencyGraph(project_dir)
        self.test_disc = TestDiscoverer(project_dir)
        self.coupling = TemporalCoupling(project_dir)

    def generate_context(self, target_file: Path, depth: int = 1, history_limit: int = 5) -> Dict[str, Any]:
        target_file = target_file.resolve()

        # 1. Imports
        imports = self.dep_graph.get_imports(target_file)

        # 2. Tests
        tests = self.test_disc.find_tests(target_file)

        # 3. Coupling
        coupled_files = self.coupling.analyze(target_file, limit=history_limit)

        context = {
            "target": str(target_file.relative_to(self.project_dir)),
            "imports": [str(p.relative_to(self.project_dir)) for p in imports],
            "tests": [str(p.relative_to(self.project_dir)) for p in tests],
            "temporal_coupling": coupled_files
        }

        return context


def run_smart_context(args):
    """Entry point for the smart-context command."""
    project_dir = args.project_dir.resolve()
    target_file = Path(args.file)

    if not target_file.is_absolute():
        target_file = project_dir / target_file

    if not target_file.exists():
        print(f"❌ Error: File '{target_file}' not found.")
        sys.exit(1)

    manager = SmartContextManager(project_dir)
    context = manager.generate_context(
        target_file,
        depth=args.depth,
        history_limit=args.limit
    )

    # Output formatting
    if args.output == "json":
        import json
        print(json.dumps(context, indent=2))
    else:
        print(f"--- Smart Context: {context['target']} ---")

        print(f"\n[ Imports ({len(context['imports'])}) ]")
        if context['imports']:
            for imp in context['imports']:
                print(f"  - {imp}")
        else:
            print("  (None found)")

        print(f"\n[ Related Tests ({len(context['tests'])}) ]")
        if context['tests']:
            for t in context['tests']:
                print(f"  - {t}")
        else:
            print("  (None found)")

        print(f"\n[ Temporal Coupling (Top {args.limit}) ]")
        if context['temporal_coupling']:
            print(f"  Files frequently changed with {context['target']}:")
            for c in context['temporal_coupling']:
                print(f"  - {c['file']} (Co-occurrences: {c['count']}, Strength: {c['strength']:.2f})")
        else:
            print("  (No history or no coupling found)")

    sys.exit(0)

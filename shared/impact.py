from collections import defaultdict
import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Set, Dict, Any, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import ast

def parse_imports(file_path: Path) -> List[Tuple[str, int]]:
    """Parses a Python file to extract imported module names and relative levels."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, 0))
        elif isinstance(node, ast.ImportFrom):
            level = node.level
            module = node.module
            if level == 0:
                # Absolute import: from os import path
                if module:
                    imports.append((module, 0))
            else:
                # Relative import
                if module:
                    # from .utils import x
                    imports.append((module, level))
                else:
                    # from . import utils
                    for alias in node.names:
                        imports.append((alias.name, level))
    return imports

class ImpactAnalyzer:
    """
    Analyzes the impact of changes in the codebase.
    Constructs a dependency graph and traverses it to find affected files and tests.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.dependencies: Dict[str, Set[str]] = defaultdict(set) # file -> set of imported files
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set) # file -> set of files that import it
        self.files_map: Dict[str, Path] = {}

    def build_graph(self):
        """Builds the dependency graph for Python files."""
        # 1. List all Python files
        for root, dirs, files in os.walk(self.project_dir):
            # Skip hidden dirs and venv
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'env', 'node_modules', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    full_path = Path(root) / file
                    rel_path = str(full_path.relative_to(self.project_dir))
                    self.files_map[rel_path] = full_path

        # 2. Parse imports
        # Optimization: Use parallel processing for larger codebases
        if len(self.files_map) >= 50:
            self._build_graph_parallel()
        else:
            self._build_graph_serial()

    def _build_graph_serial(self):
        for rel_path, full_path in self.files_map.items():
            imports = parse_imports(full_path)
            self._process_imports(rel_path, full_path, imports)

    def _build_graph_parallel(self):
        with ProcessPoolExecutor() as executor:
            future_to_path = {
                executor.submit(parse_imports, full_path): rel_path
                for rel_path, full_path in self.files_map.items()
            }

            for future in as_completed(future_to_path):
                rel_path = future_to_path[future]
                full_path = self.files_map[rel_path]
                try:
                    imports = future.result()
                    self._process_imports(rel_path, full_path, imports)
                except Exception:
                    pass

    def _process_imports(self, rel_path: str, full_path: Path, imports: List[Tuple[str, int]]):
        for name, level in imports:
            # Resolve import to file path
            resolved = self._resolve_import(name, level, full_path)
            if resolved:
                self.dependencies[rel_path].add(resolved)
                self.reverse_dependencies[resolved].add(rel_path)

    def _get_imports(self, file_path: Path) -> List[Tuple[str, int]]:
        """Parses a Python file to extract imported module names and relative levels."""
        return parse_imports(file_path)

    def _resolve_import(self, name: str, level: int, source_file: Path) -> str:
        """
        Resolves a module name to a relative file path.
        Handles both absolute (level=0) and relative (level>0) imports.
        """
        if level == 0:
            return self._resolve_absolute_import(name)
        else:
            return self._resolve_relative_import(name, level, source_file)

    def _resolve_absolute_import(self, module_name: str) -> str:
        parts = module_name.split('.')

        # Try as file
        possible_path = Path(*parts).with_suffix('.py')
        if str(possible_path) in self.files_map:
            return str(possible_path)

        # Try as directory (package) -> __init__.py
        possible_path_init = Path(*parts) / '__init__.py'
        if str(possible_path_init) in self.files_map:
            return str(possible_path_init)

        return None

    def _resolve_relative_import(self, name: str, level: int, source_file: Path) -> str:
        # source_file is absolute path
        current_dir = source_file.parent
        for _ in range(level - 1):
            current_dir = current_dir.parent
            # Safety check to avoid going above project root?
            # ImpactAnalyzer assumes self.project_dir is root.
            # But checking if we go outside might be safer.
            if not str(current_dir).startswith(str(self.project_dir)):
                 return None

        parts = name.split('.')

        # Candidate 1: current_dir/name.py
        candidate_file = current_dir.joinpath(*parts).with_suffix('.py')
        try:
            rel = candidate_file.relative_to(self.project_dir)
            if str(rel) in self.files_map:
                return str(rel)
        except ValueError:
            pass

        # Candidate 2: current_dir/name/__init__.py
        candidate_init = current_dir.joinpath(*parts) / '__init__.py'
        try:
            rel = candidate_init.relative_to(self.project_dir)
            if str(rel) in self.files_map:
                return str(rel)
        except ValueError:
            pass

        return None

    def get_changed_files(self) -> List[str]:
        """Gets a list of changed files (staged and unstaged) using git."""
        git_path = shutil.which("git")
        if not git_path:
            return []

        changed_files = []
        try:
            # Staged + Unstaged changes
            # git diff --name-only HEAD
            result = subprocess.run(
                [git_path, "-C", str(self.project_dir), "diff", "--name-only", "HEAD"],
                capture_output=True, text=True, check=True
            )
            files = result.stdout.strip().splitlines()

            # Untracked files?
            result_untracked = subprocess.run(
                [git_path, "-C", str(self.project_dir), "ls-files", "--others", "--exclude-standard"],
                capture_output=True, text=True, check=True
            )
            files.extend(result_untracked.stdout.strip().splitlines())

            # Filter for Python files and existence
            for f in files:
                if f.endswith('.py') and (self.project_dir / f).exists():
                    changed_files.append(f)

        except subprocess.CalledProcessError:
            pass

        return list(set(changed_files))

    def find_impacted_files(self, changed_files: List[str]) -> Tuple[Set[str], Set[str]]:
        """
        Traverses the reverse dependency graph to find all impacted files.
        Returns (impacted_source_files, impacted_test_files).
        """
        visited = set()
        queue = list(changed_files)

        impacted_source = set()
        impacted_tests = set()

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            # Categorize
            if current.startswith("tests/") or "test_" in current:
                impacted_tests.add(current)
            else:
                impacted_source.add(current)

            # Add reverse dependencies to queue
            for dependent in self.reverse_dependencies.get(current, []):
                if dependent not in visited:
                    queue.append(dependent)

        return impacted_source, impacted_tests

def run_impact_logic(project_dir: Path, json_output: bool = False) -> bool:
    analyzer = ImpactAnalyzer(project_dir)
    print("Building dependency graph...")
    analyzer.build_graph()

    print("Detecting changes...")
    changed_files = analyzer.get_changed_files()

    if not changed_files:
        print("✅ No changed Python files detected.")
        return True

    print(f"Detected {len(changed_files)} changed file(s):")
    for f in changed_files:
        print(f"  - {f}")

    impacted_source, impacted_tests = analyzer.find_impacted_files(changed_files)

    # Filter out the changed files themselves from the impacted source list for clarity
    # (Though technically they are impacted by themselves)
    indirectly_impacted_source = impacted_source - set(changed_files)

    results = {
        "changed_files": changed_files,
        "impacted_source_files": list(indirectly_impacted_source),
        "suggested_tests": list(impacted_tests)
    }

    if json_output:
        import json
        print(json.dumps(results, indent=2))
        return True

    print("\n--- Impact Analysis Results ---")

    if indirectly_impacted_source:
        print(f"\n⚠️  {len(indirectly_impacted_source)} source file(s) may be affected:")
        for f in sorted(indirectly_impacted_source):
            print(f"  - {f}")
    else:
        print("\n✅ No other source files appear to depend on these changes.")

    if impacted_tests:
        print(f"\n🧪 Suggested Tests ({len(impacted_tests)}):")
        for f in sorted(impacted_tests):
            print(f"  - {f}")

        print("\nTo run these tests:")
        print(f"  pytest {' '.join(sorted(impacted_tests))}")
    else:
        print("\n⚠️  No existing tests found that cover these files.")
        print("   Consider adding tests for your changes.")

    return True

from collections import defaultdict
import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Set, Dict, Any, Tuple

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
        for rel_path, full_path in self.files_map.items():
            try:
                imports = self._get_imports(full_path)
                for imp in imports:
                    # Resolve import to file path
                    resolved = self._resolve_import(imp, full_path)
                    if resolved:
                        self.dependencies[rel_path].add(resolved)
                        self.reverse_dependencies[resolved].add(rel_path)
            except Exception as e:
                # Ignore parsing errors
                pass

    def _get_imports(self, file_path: Path) -> List[str]:
        """Parses a Python file to extract imported module names."""
        import ast
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=str(file_path))
            except SyntaxError:
                return []

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                else:
                    # Relative import (from . import x) - handled later but requires context
                    pass
        return imports

    def _resolve_import(self, module_name: str, source_file: Path) -> str:
        """
        Resolves a module name (e.g. 'shared.utils') to a relative file path (e.g. 'shared/utils.py').
        Very basic resolution strategy.
        """
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

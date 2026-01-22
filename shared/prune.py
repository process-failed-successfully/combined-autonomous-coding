import os
import shutil
import ast
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Any, Optional
from shared.dependencies import DependencyAnalyzer, DependencyUpdater
from shared.impact import ImpactAnalyzer, parse_imports

class PruneManager:
    """
    Manages the identification and removal of unused code and dependencies.
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.dep_analyzer = DependencyAnalyzer(self.project_dir)
        self.impact_analyzer = ImpactAnalyzer(self.project_dir)

        # Common entry points and configuration files to ignore when pruning files
        self.IGNORE_FILES = {
            "main.py", "setup.py", "manage.py", "app.py", "wsgi.py", "asgi.py",
            "conftest.py", "__init__.py"
        }
        self.IGNORE_DIRS = {
            "tests", "scripts", "bin", "migrations", "docs", ".github"
        }

    def scan_unused_dependencies(self) -> List[Dict[str, Any]]:
        """
        Identifies declared dependencies that do not appear to be imported.
        Currently supports Python (requirements.txt).
        """
        # 1. Get declared dependencies
        manifests = self.dep_analyzer.scan()
        python_deps = []
        for item in manifests.get("python", []):
            if item["source"] == "requirements.txt":
                python_deps.extend(item["dependencies"])

        if not python_deps:
            return []

        declared_names = {d["name"].lower() for d in python_deps}

        # 2. Scan all imports in the project
        all_imports = set()
        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["venv", "env", "__pycache__"]]
            for file in files:
                if file.endswith(".py"):
                    path = Path(root) / file
                    try:
                        imports = parse_imports(path)
                        for name, _ in imports:
                            # Extract top-level module (e.g. 'yaml.scanner' -> 'yaml')
                            top_level = name.split('.')[0].lower()
                            all_imports.add(top_level)
                    except Exception:
                        pass

        # 3. Compare (Heuristic)
        # Note: Package names (PyYAML) don't always match import names (yaml).
        # We use a simple normalization (lowercase) and specific overrides if needed.
        # This list can be expanded.
        PACKAGE_TO_IMPORT = {
            "pyyaml": "yaml",
            "beautifulsoup4": "bs4",
            "python-dotenv": "dotenv",
            "pillow": "PIL",
            "scikit-learn": "sklearn",
            "protobuf": "google.protobuf",
        }

        unused = []
        for dep in python_deps:
            pkg_name = dep["name"]
            norm_name = pkg_name.lower()

            # Map package name to import name
            import_name = PACKAGE_TO_IMPORT.get(norm_name, norm_name)

            # Special case: some packages are just plugins or tools (e.g. pytest, black, flake8)
            # We shouldn't flag them as unused just because they aren't imported.
            # We assume dev-dependencies might be in requirements.txt
            KNOWN_TOOLS = {"pytest", "black", "flake8", "mypy", "isort", "bandit", "tox", "twine", "wheel", "pip", "setuptools"}
            if norm_name in KNOWN_TOOLS or norm_name.startswith("pytest-"):
                continue

            if import_name not in all_imports:
                # One last check: try to find the exact string in the codebase?
                # (Maybe used dynamically or in a weird way).
                # skipping for now to keep it simple.
                unused.append(dep)

        return unused

    def scan_unused_files(self) -> List[Path]:
        """
        Identifies Python files that are not imported by any other file
        and do not appear to be entry points.
        """
        self.impact_analyzer.build_graph()

        # files_map keys are relative paths strings
        all_files = set(self.impact_analyzer.files_map.keys())

        # Files that ARE imported by someone
        # reverse_dependencies: file -> set of files that import it.
        # If a file IS imported, it will appear as a KEY in reverse_dependencies?
        # Wait, let's check impact.py:
        # self.dependencies[rel_path].add(resolved)  -> rel_path imports resolved
        # self.reverse_dependencies[resolved].add(rel_path) -> resolved is imported by rel_path

        # So files that are imported are the KEYS of reverse_dependencies.
        imported_files = set(self.impact_analyzer.reverse_dependencies.keys())

        candidates = []
        for rel_path in all_files:
            if rel_path in imported_files:
                continue

            # It's a leaf (or root). Check if it's an entry point.
            path_obj = Path(rel_path)

            # 1. Ignore list
            if path_obj.name in self.IGNORE_FILES:
                continue

            # 2. Ignore dirs
            if any(part in self.IGNORE_DIRS for part in path_obj.parts):
                continue

            # 3. Check for "if __name__ == '__main__':"
            full_path = self.project_dir / rel_path
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                if "if __name__" in content and "__main__" in content:
                    continue
            except Exception:
                pass

            candidates.append(full_path)

        return sorted(candidates)

    def prune_interactive(self, dry_run: bool = False, yes: bool = False, types: Optional[List[str]] = None):
        """
        Interactive pruning process.
        """
        if types is None:
            types = ["deps", "files"]

        # --- Dependencies ---
        if "deps" in types:
            print("\n🔍 Scanning for unused dependencies...")
            unused_deps = self.scan_unused_dependencies()

            if unused_deps:
                print(f"Found {len(unused_deps)} potentially unused dependencies in requirements.txt:")
                for i, dep in enumerate(unused_deps):
                    print(f"  [{i+1}] {dep['name']} ({dep['version']})")

                if not dry_run:
                    self._handle_deletion(
                        items=unused_deps,
                        item_type="dependency",
                        yes=yes,
                        delete_func=self._delete_dependencies
                    )
            else:
                print("✅ No unused dependencies found.")

        # --- Files ---
        if "files" in types:
            print("\n🔍 Scanning for unused files...")
            unused_files = self.scan_unused_files()

            if unused_files:
                print(f"Found {len(unused_files)} potentially unused files:")
                for i, f in enumerate(unused_files):
                    print(f"  [{i+1}] {f.relative_to(self.project_dir)}")

                if not dry_run:
                    self._handle_deletion(
                        items=unused_files,
                        item_type="file",
                        yes=yes,
                        delete_func=self._delete_files
                    )
            else:
                print("✅ No unused files found.")

    def _handle_deletion(self, items: List[Any], item_type: str, yes: bool, delete_func):
        if not items:
            return

        selected = []
        if yes:
            selected = items
        else:
            print(f"\nEnter numbers to remove (e.g. '1 3 5'), 'a' for all, or Enter to skip.")
            choice = input("> ").strip().lower()
            if choice == 'a':
                selected = items
            elif choice:
                try:
                    indices = [int(x) - 1 for x in choice.split()]
                    for idx in indices:
                        if 0 <= idx < len(items):
                            selected.append(items[idx])
                except ValueError:
                    print("Invalid input. Skipping.")
                    return
            else:
                print("Skipping.")
                return

        if not selected:
            return

        # Stash if not empty
        self._stash_changes()

        print(f"Removing {len(selected)} {item_type}(s)...")
        delete_func(selected)
        print("✅ Done.")

    def _stash_changes(self):
        """Creates a git stash before making changes."""
        git_path = shutil.which("git")
        if git_path and (self.project_dir / ".git").is_dir():
            print("💾 Stashing current state for safety...")
            try:
                subprocess.run(
                    [git_path, "-C", str(self.project_dir), "stash", "push", "-u", "-m", "Auto-stash before prune"],
                    check=True, capture_output=True
                )
            except subprocess.CalledProcessError:
                print("Warning: Could not stash changes. Proceeding anyway.")

    def _delete_files(self, files: List[Path]):
        for f in files:
            try:
                f.unlink()
                print(f"  Deleted: {f.relative_to(self.project_dir)}")
            except OSError as e:
                print(f"  Error deleting {f.name}: {e}")

    def _delete_dependencies(self, deps: List[Dict]):
        # This is tricky because we need to parse requirements.txt and remove lines.
        # DependencyUpdater updates versions, but doesn't delete.
        # We'll implement a simple remover here.

        req_file = self.project_dir / "requirements.txt"
        if not req_file.exists():
            return

        try:
            lines = req_file.read_text(encoding="utf-8").splitlines()
            names_to_remove = {d["name"].lower() for d in deps}

            new_lines = []
            removed_count = 0

            for line in lines:
                clean_line = line.strip()
                if not clean_line or clean_line.startswith("#"):
                    new_lines.append(line)
                    continue

                # Extract name
                match = re.match(r"^([a-zA-Z0-9\-_]+)", clean_line)
                if match:
                    name = match.group(1).lower()
                    if name in names_to_remove:
                        removed_count += 1
                        print(f"  Removed from requirements.txt: {name}")
                        continue

                new_lines.append(line)

            req_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        except Exception as e:
            print(f"Error updating requirements.txt: {e}")

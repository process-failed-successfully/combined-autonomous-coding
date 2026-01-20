"""
Playground Manager
==================

Manages a safe, isolated environment for experimenting with code.
"""

import os
import sys
import shutil
import subprocess
import collections
import ast
from pathlib import Path
from typing import List, Dict, Counter

class PlaygroundManager:
    PLAYGROUND_DIR_NAME = ".playground"

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.playground_dir = self.project_dir / self.PLAYGROUND_DIR_NAME

    def ensure_setup(self):
        """Ensures the playground directory and .gitignore entry exist."""
        if not self.playground_dir.exists():
            self.playground_dir.mkdir(parents=True, exist_ok=True)

        # Add to .gitignore if not present
        gitignore_path = self.project_dir / ".gitignore"
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if self.PLAYGROUND_DIR_NAME not in content:
                with open(gitignore_path, "a") as f:
                    f.write(f"\n{self.PLAYGROUND_DIR_NAME}/\n")
        else:
            with open(gitignore_path, "w") as f:
                f.write(f"{self.PLAYGROUND_DIR_NAME}/\n")

    def _analyze_common_imports(self) -> str:
        """Scans the project for common imports to pre-fill the playground."""
        import_counter: Counter[str] = collections.Counter()

        for root, _, files in os.walk(self.project_dir):
            if any(p.startswith('.') for p in Path(root).parts):
                continue # Skip hidden dirs

            for file in files:
                if file.endswith(".py"):
                    try:
                        with open(Path(root) / file, "r", encoding="utf-8", errors="ignore") as f:
                            tree = ast.parse(f.read())
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        import_counter[f"import {alias.name}"] += 1
                                elif isinstance(node, ast.ImportFrom):
                                    if node.module:
                                        import_counter[f"from {node.module} import ..."] += 1
                    except Exception:
                        pass

        # Get top 5 most common imports
        common = import_counter.most_common(5)
        imports_code = []
        for imp_str, _ in common:
            if "..." in imp_str:
                # Expand 'from X import ...' to a comment or generic import?
                # Actually, capturing specific names is hard without clutter.
                # Let's just suggest the module.
                module = imp_str.split(" ")[1]
                imports_code.append(f"# from {module} import ...")
            else:
                imports_code.append(imp_str)

        # Always add some basics
        base_imports = ["import os", "import sys", "from pathlib import Path"]
        return "\n".join(sorted(list(set(base_imports + imports_code))))

    def create(self, name: str = "scratch.py") -> Path:
        """Creates a new playground file with boilerplate."""
        self.ensure_setup()

        if not name.endswith(".py"):
            name += ".py"

        file_path = self.playground_dir / name

        if file_path.exists():
            return file_path

        common_imports = self._analyze_common_imports()

        content = f"""\"\"\"
Playground: {name}
Run this file with: python3 {self.PLAYGROUND_DIR_NAME}/{name}
\"\"\"

{common_imports}

def main():
    print("Hello from the playground!")
    # Your experiment here...

if __name__ == "__main__":
    main()
"""
        file_path.write_text(content)
        return file_path

    def list_files(self) -> List[Path]:
        """Lists all files in the playground."""
        if not self.playground_dir.exists():
            return []
        return sorted([f for f in self.playground_dir.iterdir() if f.is_file()])

    def run(self, name: str) -> bool:
        """Runs a playground file."""
        if not name.endswith(".py"):
            name += ".py"

        file_path = self.playground_dir / name
        if not file_path.exists():
            print(f"❌ File '{name}' not found in playground.")
            return False

        print(f"--- Running {name} ---")
        try:
            # Run with project root as PYTHONPATH so imports work
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.project_dir) + os.pathsep + env.get("PYTHONPATH", "")

            subprocess.run([sys.executable, str(file_path)], env=env, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Script failed with exit code {e.returncode}")
            return False
        except Exception as e:
            print(f"❌ Error running script: {e}")
            return False

    def delete(self, name: str) -> bool:
        """Deletes a playground file."""
        if not name.endswith(".py"):
            name += ".py"

        file_path = self.playground_dir / name
        if not file_path.exists():
            return False

        file_path.unlink()
        return True

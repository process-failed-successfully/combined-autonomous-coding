import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Basic built-in templates
TEMPLATES: Dict[str, str] = {
    "python": """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.coverage
htmlcov/
.tox/
.nox/
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
""",
    "node": """
# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
.npm/
.yarn/
dist/
build/
coverage/
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
""",
    "go": """
# Go
bin/
pkg/
src/
*.exe
*.test
*.prof
vendor/
go.work
""",
    "java": """
# Java
*.class
*.log
*.ctxt
.mtj.tmp/
*.jar
*.war
*.nar
*.ear
*.zip
*.tar.gz
*.rar
hs_err_pid*
""",
    "cpp": """
# C++
*.o
*.obj
*.so
*.dll
*.dylib
*.exe
*.lib
*.a
*.pdb
build/
bin/
""",
    "rust": """
# Rust
/target
**/*.rs.bk
Cargo.lock
""",
    "macos": """
# macOS
.DS_Store
.AppleDouble
.LSOverride
Icon
._*
.Spotlight-V100
.Trashes
.VolumeIcon.icns
.com.apple.timemachine.donotpresent
""",
    "windows": """
# Windows
Thumbs.db
ehthumbs.db
Desktop.ini
$RECYCLE.BIN/
*.cab
*.msi
*.msm
*.msp
*.lnk
""",
    "linux": """
# Linux
*~
.fuse_hidden*
.directory
.Trash-*
.nfs*
""",
    "vscode": """
# VSCode
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
*.code-workspace
""",
    "intellij": """
# IntelliJ
.idea/
*.iml
*.iws
*.ipr
out/
"""
}

class GitignoreManager:
    """Manages .gitignore operations."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def list_templates(self) -> List[str]:
        """Returns a list of available templates."""
        return sorted(TEMPLATES.keys())

    def get_template(self, name: str) -> Optional[str]:
        """Returns the content of a specific template."""
        return TEMPLATES.get(name.lower())

    def generate(self, names: List[str]) -> str:
        """Generates gitignore content from multiple templates."""
        content = []
        for name in names:
            tpl = self.get_template(name)
            if tpl:
                content.append(tpl.strip())
            else:
                # If checking logic is strict, we could raise an error here.
                # For now, we'll just skip unknown templates or add a warning comment.
                content.append(f"# Warning: Template '{name}' not found.")

        return "\n\n".join(content)

    def check_ignore(self, path: str) -> Dict[str, str]:
        """
        Checks if a file is ignored using 'git check-ignore'.
        Returns a dict with status and details.
        """
        try:
            # git check-ignore -v path
            result = subprocess.run(
                ["git", "check-ignore", "-v", path],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Output format: source:line:pattern pathname
                # e.g., .gitignore:3:*.py[cod] test.pyc
                output = result.stdout.strip()
                return {
                    "ignored": "yes",
                    "details": output,
                    "message": f"'{path}' is ignored."
                }
            elif result.returncode == 1:
                return {
                    "ignored": "no",
                    "details": "",
                    "message": f"'{path}' is NOT ignored."
                }
            else:
                return {
                    "ignored": "error",
                    "details": result.stderr.strip(),
                    "message": f"Error checking ignore status: {result.stderr.strip()}"
                }
        except FileNotFoundError:
            return {
                "ignored": "error",
                "details": "git command not found",
                "message": "Error: 'git' command not found."
            }
        except Exception as e:
            return {
                "ignored": "error",
                "details": str(e),
                "message": f"Error: {e}"
            }

    def append(self, names: List[str]) -> bool:
        """Appends templates to .gitignore."""
        gitignore_path = self.project_dir / ".gitignore"
        content_to_append = self.generate(names)

        if not content_to_append:
            return False

        mode = "a" if gitignore_path.exists() else "w"
        try:
            with open(gitignore_path, mode) as f:
                if mode == "a":
                    f.write("\n")
                f.write(content_to_append + "\n")
            return True
        except IOError:
            return False

def run_gitignore_lab_logic(args):
    """CLI logic for Gitignore Lab."""
    project_dir = args.project_dir.resolve()
    manager = GitignoreManager(project_dir)

    if args.action == "list":
        print("--- Available Gitignore Templates ---")
        for tpl in manager.list_templates():
            print(f"  - {tpl}")
        sys.exit(0)

    elif args.action == "generate":
        if not args.templates:
            print("Error: --templates list is required (e.g., 'python,macos').", file=sys.stderr)
            sys.exit(1)

        names = [n.strip() for n in args.templates.split(",")]
        content = manager.generate(names)
        print(content)
        sys.exit(0)

    elif args.action == "check":
        if not args.path:
             print("Error: --path is required.", file=sys.stderr)
             sys.exit(1)

        result = manager.check_ignore(args.path)
        if result["ignored"] == "yes":
            print(f"🚫 {result['message']}")
            print(f"   Details: {result['details']}")
            sys.exit(0)
        elif result["ignored"] == "no":
            print(f"✅ {result['message']}")
            sys.exit(1) # Return 1 if NOT ignored (standard check behavior? Or 0?)
            # Actually, usually 'check' returns 0 if found (ignored) and 1 if not.
            # git check-ignore returns 0 if ignored, 1 if not.
        else:
            print(f"❌ {result['message']}", file=sys.stderr)
            sys.exit(2)

    elif args.action == "append":
        if not args.templates:
            print("Error: --templates list is required.", file=sys.stderr)
            sys.exit(1)

        names = [n.strip() for n in args.templates.split(",")]
        if manager.append(names):
            print(f"✅ Appended {len(names)} templates to .gitignore.")
            sys.exit(0)
        else:
            print("❌ Error appending to .gitignore.", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)

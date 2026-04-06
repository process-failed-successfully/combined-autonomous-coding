import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil

class PreCommitLabManager:
    """Manages pre-commit hook operations."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config_path = self.project_dir / ".pre-commit-config.yaml"

    def is_installed(self) -> bool:
        """Checks if pre-commit is installed in the environment."""
        return shutil.which("pre-commit") is not None

    def config_exists(self) -> bool:
        """Checks if the config file exists."""
        return self.config_path.exists()

    def install(self) -> bool:
        """Installs pre-commit using pip."""
        try:
            subprocess.run(["pip", "install", "pre-commit"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, OSError, FileNotFoundError):
            return False

    def create_default_config(self) -> bool:
        """Creates a default .pre-commit-config.yaml."""
        default_config = {
            "repos": [
                {
                    "repo": "https://github.com/pre-commit/pre-commit-hooks",
                    "rev": "v4.5.0",
                    "hooks": [
                        {"id": "trailing-whitespace"},
                        {"id": "end-of-file-fixer"},
                        {"id": "check-yaml"},
                        {"id": "check-added-large-files"},
                    ]
                },
                {
                    "repo": "https://github.com/psf/black",
                    "rev": "24.2.0",
                    "hooks": [
                        {"id": "black"}
                    ]
                },
                {
                    "repo": "https://github.com/PyCQA/flake8",
                    "rev": "7.0.0",
                    "hooks": [
                        {"id": "flake8"}
                    ]
                }
            ]
        }
        try:
            with open(self.config_path, "w") as f:
                yaml.dump(default_config, f, sort_keys=False)
            return True
        except Exception:
            return False

    def get_config_content(self) -> str:
        """Returns the content of the config file."""
        if not self.config_exists():
            return ""
        return self.config_path.read_text(encoding="utf-8", errors="replace")

    def save_config_content(self, content: str) -> bool:
        """Saves content to the config file."""
        try:
            self.config_path.write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False

    def install_hooks(self) -> tuple[bool, str]:
        """Runs 'pre-commit install'."""
        return self._run_command(["pre-commit", "install"])

    def run_all_hooks(self) -> tuple[bool, str]:
        """Runs 'pre-commit run --all-files'."""
        return self._run_command(["pre-commit", "run", "--all-files"])

    def autoupdate_hooks(self) -> tuple[bool, str]:
        """Runs 'pre-commit autoupdate'."""
        return self._run_command(["pre-commit", "autoupdate"])

    def _run_command(self, cmd: List[str]) -> tuple[bool, str]:
        """Helper to run commands safely."""
        try:
            # Check if pre-commit is in path first, to avoid cryptic FileNotFoundError if not
            if not shutil.which("pre-commit"):
                 return (False, "Error: pre-commit not found. Please install it first.")

            res = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=False # We want to capture failure output too
            )
            output = res.stdout
            if res.stderr:
                output += "\n" + res.stderr
            return (res.returncode == 0, output)
        except Exception as e:
            return (False, str(e))

    def get_hooks(self) -> List[Dict[str, Any]]:
        """Parses the config file to list hooks."""
        if not self.config_exists():
            return []

        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f) or {}

            hooks = []
            for repo in data.get("repos", []):
                repo_url = repo.get("repo", "local")
                for hook in repo.get("hooks", []):
                    hooks.append({
                        "id": hook.get("id"),
                        "repo": repo_url,
                        "rev": repo.get("rev", "unknown")
                    })
            return hooks
        except Exception:
            return []

def run_pre_commit_lab_logic(args):
    """CLI logic for the Pre-commit Lab."""
    import sys
    manager = PreCommitLabManager(args.project_dir)

    if args.action == "install-tool":
        print("Installing pre-commit tool...")
        success = manager.install()
        if success:
            print("✅ Successfully installed pre-commit.")
            sys.exit(0)
        else:
            print("❌ Failed to install pre-commit.")
            sys.exit(1)

    elif args.action == "create-config":
        print("Creating default .pre-commit-config.yaml...")
        success = manager.create_default_config()
        if success:
            print("✅ Successfully created config.")
            sys.exit(0)
        else:
            print("❌ Failed to create config.")
            sys.exit(1)

    elif args.action == "install":
        print("Installing pre-commit hooks...")
        success, output = manager.install_hooks()
        print(output)
        if success:
            print("✅ Successfully installed hooks.")
            sys.exit(0)
        else:
            print("❌ Failed to install hooks.")
            sys.exit(1)

    elif args.action == "run-all":
        print("Running all hooks...")
        success, output = manager.run_all_hooks()
        print(output)
        if success:
            print("✅ Hooks ran successfully.")
            sys.exit(0)
        else:
            print("❌ Hooks failed.")
            sys.exit(1)

    elif args.action == "autoupdate":
        print("Autoupdating hooks...")
        success, output = manager.autoupdate_hooks()
        print(output)
        if success:
            print("✅ Successfully autoupdated hooks.")
            sys.exit(0)
        else:
            print("❌ Failed to autoupdate hooks.")
            sys.exit(1)

    elif args.action == "status":
        print("--- Pre-commit Lab Status ---")
        if manager.is_installed():
            print("Tool: ✅ Installed")
        else:
            print("Tool: ❌ Not Installed")

        if manager.config_exists():
            print("Config: ✅ Found (.pre-commit-config.yaml)")
            hooks = manager.get_hooks()
            print(f"Hooks configured: {len(hooks)}")
            for h in hooks:
                print(f"  - {h['id']} ({h['repo']} @ {h['rev']})")
        else:
            print("Config: ❌ Missing")

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)

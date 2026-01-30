"""
Recipe Manager
==============

Allows users to define and run sequences of agent commands ("recipes" or "macros").
Recipes are stored in the `agent_config.yaml` file.
"""

import sys
import yaml
import subprocess
import shlex
from pathlib import Path
from typing import List, Dict, Optional, Any
from shared.config_loader import get_config_path

class RecipeManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config_path = get_config_path()
        # Cache for loaded config
        self._config_data: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Loads the raw configuration file."""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self._config_data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Could not load config for recipes: {e}", file=sys.stderr)
                self._config_data = {}
        else:
            self._config_data = {}

    def _save_config(self) -> bool:
        """Saves the configuration back to the file."""
        if not self.config_path:
            # If no config path exists, create one in XDG or current dir
            # For simplicity, let's use the one resolved by config_loader or default to XDG
            from platformdirs import user_config_dir
            xdg_config_dir = Path(user_config_dir("combined-autonomous-coding"))
            xdg_config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = xdg_config_dir / "agent_config.yaml"

        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self._config_data, f, sort_keys=False, indent=2)
            # Secure the file
            try:
                import os
                os.chmod(self.config_path, 0o600)
            except Exception:
                pass
            return True
        except Exception as e:
            print(f"Error saving config: {e}", file=sys.stderr)
            return False

    def list_recipes(self) -> Dict[str, List[str]]:
        """Returns a dictionary of available recipes."""
        return self._config_data.get("recipes", {})

    def get_recipe(self, name: str) -> Optional[List[str]]:
        """Returns the steps for a specific recipe."""
        recipes = self.list_recipes()
        return recipes.get(name)

    def add_recipe(self, name: str, steps: List[str]) -> bool:
        """Adds or updates a recipe."""
        if "recipes" not in self._config_data:
            self._config_data["recipes"] = {}

        self._config_data["recipes"][name] = steps
        return self._save_config()

    def delete_recipe(self, name: str) -> bool:
        """Deletes a recipe."""
        if "recipes" in self._config_data and name in self._config_data["recipes"]:
            del self._config_data["recipes"][name]
            return self._save_config()
        return False

    def run_recipe(self, name: str, dry_run: bool = False, capture_output: bool = False, known_commands: List[str] = None) -> bool | tuple[bool, str]:
        """
        Executes a recipe.

        Args:
            name: The name of the recipe to run.
            dry_run: If True, only prints the steps without executing.
            capture_output: If True, returns a tuple (success, output_log).
                            If False, prints to stdout and returns success (bool).
            known_commands: Optional list of known agent commands. If a step starts with one of these,
                            it will be executed as an agent command. Otherwise, it runs as shell.
        """
        steps = self.get_recipe(name)
        output_log = []

        def log(msg: str, is_error: bool = False):
            if capture_output:
                output_log.append(msg)
            else:
                file = sys.stderr if is_error else sys.stdout
                print(msg, file=file)

        if not steps:
            log(f"❌ Error: Recipe '{name}' not found.", is_error=True)
            return (False, "\n".join(output_log)) if capture_output else False

        log(f"--- Running Recipe: {name} ---")

        # Prevent infinite recursion (basic check)
        import os
        depth = int(os.environ.get("AGENT_RECIPE_DEPTH", "0"))
        if depth > 5:
            log("❌ Error: Maximum recipe recursion depth exceeded.", is_error=True)
            return (False, "\n".join(output_log)) if capture_output else False

        env = os.environ.copy()
        env["AGENT_RECIPE_DEPTH"] = str(depth + 1)

        executable = sys.executable
        script = str(Path(sys.argv[0]).resolve())
        current_cwd = self.project_dir

        success = True
        for i, step in enumerate(steps):
            log(f"\n[Step {i+1}/{len(steps)}] {step}")

            if dry_run:
                continue

            try:
                parts = shlex.split(step)
                if not parts:
                    continue

                cmd_name = parts[0]
                run_as_shell = False
                cmd = []

                # Handle internal commands like 'cd'
                if cmd_name == "cd":
                    if len(parts) > 1:
                        target = parts[1]
                        new_path = (current_cwd / target).resolve()
                        if new_path.is_dir():
                            current_cwd = new_path
                            log(f"Changed directory to: {current_cwd}")
                        else:
                            log(f"❌ Error: Directory not found: {target}", is_error=True)
                            success = False
                            break
                    else:
                        current_cwd = self.project_dir
                        log(f"Changed directory to project root: {current_cwd}")
                    continue

                # Determine execution mode
                is_explicit_python = cmd_name == "python" or cmd_name.endswith("python") or cmd_name.endswith("python3")
                is_explicit_main = cmd_name.endswith("main.py")

                if is_explicit_python:
                    cmd = [executable] + parts[1:]
                elif is_explicit_main:
                    cmd = [executable, script] + parts[1:]
                elif known_commands and cmd_name in known_commands:
                    # It's an agent command
                    cmd = [executable, script] + parts
                else:
                    # Default to shell for unknown commands (likely git, ls, etc.)
                    run_as_shell = True

                kwargs = {
                    "cwd": current_cwd,
                    "env": env,
                    "text": True
                }
                if capture_output:
                    kwargs["capture_output"] = True

                if run_as_shell:
                    # Run raw step string in shell
                    result = subprocess.run(step, shell=True, **kwargs)  # nosec B602
                else:
                    result = subprocess.run(cmd, **kwargs)

                if capture_output:
                    if result.stdout:
                        output_log.append(result.stdout)
                    if result.stderr:
                        output_log.append(result.stderr)

                if result.returncode != 0:
                    log(f"❌ Step failed with exit code {result.returncode}. Aborting recipe.", is_error=True)
                    success = False
                    break

            except Exception as e:
                log(f"❌ Error executing step '{step}': {e}", is_error=True)
                success = False
                break

        if success:
            log(f"\n✅ Recipe '{name}' completed successfully.")

        if capture_output:
            return success, "\n".join(output_log)
        return success

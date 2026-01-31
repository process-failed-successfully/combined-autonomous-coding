from pathlib import Path
import json
from typing import Dict, Any


class IdeConfigManager:
    """
    Manages IDE configuration generation (VS Code, Cursor, etc).
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def detect_project_type(self) -> str:
        """Detects the project type based on file structure."""
        if (self.project_dir / "package.json").exists():
            return "node"
        if (self.project_dir / "requirements.txt").exists() or (self.project_dir / "pyproject.toml").exists():
            return "python"
        if (self.project_dir / "go.mod").exists():
            return "go"
        return "unknown"

    def get_config_previews(self) -> Dict[str, Any]:
        """Returns the generated configuration for preview."""
        project_type = self.detect_project_type()
        return {
            "settings.json": self._get_settings(project_type),
            "launch.json": self._get_launch(project_type),
            "extensions.json": self._get_extensions(project_type)
        }

    def generate_vscode_config(self, dry_run: bool = False, force: bool = False) -> bool:
        """Generates .vscode configuration files."""
        project_type = self.detect_project_type()
        vscode_dir = self.project_dir / ".vscode"

        print(f"Detected project type: {project_type}")

        settings = self._get_settings(project_type)
        launch = self._get_launch(project_type)
        extensions = self._get_extensions(project_type)

        files = {
            "settings.json": settings,
            "launch.json": launch,
            "extensions.json": extensions
        }

        if dry_run:
            print(f"[Dry Run] Would create directory: {vscode_dir}")
            for filename, content in files.items():
                print(f"\n--- .vscode/{filename} ---")
                print(json.dumps(content, indent=4))
            return True

        if not vscode_dir.exists():
            vscode_dir.mkdir(parents=True)
            print(f"Created directory: {vscode_dir}")

        for filename, content in files.items():
            file_path = vscode_dir / filename
            if file_path.exists() and not force:
                print(f"⚠️  Skipping {filename} (already exists). Use --force to overwrite.")
                continue

            try:
                with open(file_path, "w") as f:
                    json.dump(content, f, indent=4)
                print(f"✅ Generated {filename}")
            except IOError as e:
                print(f"❌ Error writing {filename}: {e}")
                return False

        return True

    def _get_settings(self, project_type: str) -> Dict[str, Any]:
        settings: Dict[str, Any] = {
            "search.exclude": {
                "**/.git": True,
                "**/.ds_store": True,
                "**/.venv": True,
                "**/__pycache__": True,
                "**/.agent_trash": True,
                "**/.agent_archives": True
            },
            "files.watcherExclude": {
                "**/.git/objects/**": True,
                "**/.git/subtree-cache/**": True,
                "**/node_modules/*/**": True,
                "**/.agent_trash/**": True
            }
        }

        if project_type == "python":
            settings.update({
                "python.analysis.typeCheckingMode": "basic",
                "python.formatting.provider": "black",
                "python.linting.enabled": True,
                "python.linting.flake8Enabled": True,
                "editor.formatOnSave": True,
                "[python]": {
                    "editor.defaultFormatter": "ms-python.black-formatter"
                }
            })
            if (self.project_dir / ".venv").exists():
                settings["python.defaultInterpreterPath"] = "${workspaceFolder}/.venv/bin/python"
            elif (self.project_dir / "venv").exists():
                settings["python.defaultInterpreterPath"] = "${workspaceFolder}/venv/bin/python"

        elif project_type == "node":
            settings.update({
                "editor.formatOnSave": True,
                "editor.defaultFormatter": "esbenp.prettier-vscode",
                "editor.codeActionsOnSave": {
                    "source.fixAll.eslint": "explicit"
                }
            })

        return settings

    def _get_launch(self, project_type: str) -> Dict[str, Any]:
        configurations = []
        if project_type == "python":
            configurations.append({
                "name": "Python: Current File",
                "type": "python",
                "request": "launch",
                "program": "${file}",
                "console": "integratedTerminal"
            })
            # Heuristic for Flask/Django/FastAPI
            if (self.project_dir / "app.py").exists():
                configurations.append({
                    "name": "Python: Run app.py",
                    "type": "python",
                    "request": "launch",
                    "program": "${workspaceFolder}/app.py",
                    "console": "integratedTerminal"
                })
            elif (self.project_dir / "main.py").exists():
                configurations.append({
                    "name": "Python: Run main.py",
                    "type": "python",
                    "request": "launch",
                    "program": "${workspaceFolder}/main.py",
                    "console": "integratedTerminal"
                })

        elif project_type == "node":
            configurations.append({
                "type": "node",
                "request": "launch",
                "name": "Launch Program",
                "skipFiles": ["<node_internals>/**"],
                "program": "${workspaceFolder}/index.js"
            })
            if (self.project_dir / "package.json").exists():
                configurations.append({
                    "name": "Run 'npm start'",
                    "command": "npm start",
                    "request": "launch",
                    "type": "node-terminal"
                })

        return {
            "version": "0.2.0",
            "configurations": configurations
        }

    def _get_extensions(self, project_type: str) -> Dict[str, Any]:
        recommendations = []
        if project_type == "python":
            recommendations = [
                "ms-python.python",
                "ms-python.vscode-pylance",
                "ms-python.black-formatter",
                "ms-python.flake8",
            ]
        elif project_type == "node":
            recommendations = [
                "dbaeumer.vscode-eslint",
                "esbenp.prettier-vscode"
            ]
        elif project_type == "go":
            recommendations = [
                "golang.go"
            ]

        return {
            "recommendations": recommendations
        }

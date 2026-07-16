import sys
import argparse
from pathlib import Path
from typing import Dict, Optional

from shared.dockerizer import Dockerizer

class DockerfileLabManager:
    """Manages Dockerfile generation and previews."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.dockerizer = Dockerizer(self.project_dir)
        self.project_type = self.dockerizer.detect_project_type()

    def generate(self) -> Dict[str, str]:
        """Generates configuration files as a dictionary."""
        if self.project_type == "unknown":
            raise ValueError("Could not detect project type (Python, Node, Go).")

        return {
            "Dockerfile": self.dockerizer.generate_dockerfile(self.project_type),
            "docker-compose.yml": self.dockerizer.generate_docker_compose(self.project_type),
            ".dockerignore": self.dockerizer.generate_dockerignore(self.project_type)
        }

    def save_files(self, files: Dict[str, str], force: bool = False) -> list:
        """Saves generated files to the project directory."""
        saved = []
        for filename, content in files.items():
            file_path = self.project_dir / filename
            if file_path.exists() and not force:
                continue

            try:
                file_path.write_text(content)
                saved.append(filename)
            except IOError as e:
                print(f"Error writing {filename}: {e}", file=sys.stderr)

        return saved


def run_dockerfile_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Dockerfile Lab."""

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        try:
            from main import run_tui
            print("Launching Dockerfile Lab TUI...")
            run_tui(args, start_tab="tab-dockerfile")
            return True
        except ImportError as e:
            print(f"Error launching TUI: {e}", file=sys.stderr)
            return False

    project_dir = getattr(args, "project_dir", Path(".")).resolve()

    try:
        manager = DockerfileLabManager(project_dir)
    except Exception as e:
        print(f"Error initializing DockerfileLabManager: {e}", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "action", None) == "generate":
        try:
            files_to_generate = manager.generate()

            if getattr(args, "dry_run", False):
                print(f"--- [Dry Run] Generated configs for '{manager.project_type}' project ---")
                for filename, content in files_to_generate.items():
                    print(f"\n--- {filename} ---")
                    print(content)
                return True

            saved_files = manager.save_files(files_to_generate, force=getattr(args, "force", False))

            if saved_files:
                for f in saved_files:
                    print(f"✅ Generated {f}")
                print("\n🎉 Successfully generated Docker configuration!")
            else:
                print("No files were generated (they might already exist). Use --force to overwrite.")
            return True

        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error generating files: {e}", file=sys.stderr)
            sys.exit(1)

    return False

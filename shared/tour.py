import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict, field

@dataclass
class TourStep:
    file: str
    line: int
    description: str

@dataclass
class Tour:
    title: str
    description: str
    steps: List[TourStep] = field(default_factory=list)

class TourManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.tours_dir = project_dir / ".tours"
        self.tours_dir.mkdir(parents=True, exist_ok=True)

    def _get_tour_path(self, name: str) -> Path:
        return self.tours_dir / f"{name}.json"

    def list_tours(self) -> List[str]:
        return sorted([f.stem for f in self.tours_dir.glob("*.json")])

    def get_tour(self, name: str) -> Optional[Tour]:
        path = self._get_tour_path(name)
        if not path.exists():
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            steps = [TourStep(**s) for s in data.get("steps", [])]
            return Tour(
                title=data.get("title", ""),
                description=data.get("description", ""),
                steps=steps
            )
        except Exception as e:
            print(f"Error loading tour '{name}': {e}", file=sys.stderr)
            return None

    def create_tour(self, name: str, title: str, description: str) -> bool:
        path = self._get_tour_path(name)
        if path.exists():
            return False

        tour = Tour(title=title, description=description, steps=[])
        self._save_tour(name, tour)
        return True

    def add_step(self, name: str, file: str, line: int, description: str) -> bool:
        tour = self.get_tour(name)
        if not tour:
            return False

        # Normalize file path relative to project dir if possible
        try:
            full_path = Path(file).resolve()
            proj_path = self.project_dir.resolve()
            if str(full_path).startswith(str(proj_path)):
                file = str(full_path.relative_to(proj_path))
        except Exception:
            pass # Keep as is if relative fails

        tour.steps.append(TourStep(file=file, line=line, description=description))
        self._save_tour(name, tour)
        return True

    def delete_tour(self, name: str) -> bool:
        path = self._get_tour_path(name)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _save_tour(self, name: str, tour: Tour):
        path = self._get_tour_path(name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(asdict(tour), f, indent=2)

def run_tour_logic(args):
    """Handles the tour CLI commands."""
    project_dir = args.project_dir.resolve()
    manager = TourManager(project_dir)
    action = args.action

    if action == "list":
        tours = manager.list_tours()
        if not tours:
            print("No tours found.")
        else:
            print("--- Available Tours ---")
            for t in tours:
                tour = manager.get_tour(t)
                title = tour.title if tour else "Error loading"
                print(f"  - {t:<20} : {title}")

    elif action == "create":
        if not args.name:
            print("Error: Name is required.", file=sys.stderr)
            sys.exit(1)

        if manager.create_tour(args.name, args.title or args.name, args.description or ""):
            print(f"✅ Tour '{args.name}' created.")
        else:
            print(f"❌ Tour '{args.name}' already exists.", file=sys.stderr)
            sys.exit(1)

    elif action == "add":
        if not args.name or not args.file or not args.line:
            print("Error: Name, File, and Line are required.", file=sys.stderr)
            sys.exit(1)

        if manager.add_step(args.name, args.file, args.line, args.description or ""):
            print(f"✅ Step added to tour '{args.name}'.")
        else:
            print(f"❌ Tour '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    elif action == "delete":
        if not args.name:
            print("Error: Name is required.", file=sys.stderr)
            sys.exit(1)

        if manager.delete_tour(args.name):
            print(f"✅ Tour '{args.name}' deleted.")
        else:
            print(f"❌ Tour '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    elif action == "show":
        if not args.name:
            print("Error: Name is required.", file=sys.stderr)
            sys.exit(1)

        tour = manager.get_tour(args.name)
        if not tour:
            print(f"❌ Tour '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Tour: {tour.title} ---")
        print(f"Description: {tour.description}")
        print(f"Steps: {len(tour.steps)}")
        for i, step in enumerate(tour.steps):
            print(f"  [{i+1}] {step.file}:{step.line} - {step.description}")

    elif action == "play":
        if not args.name:
            print("Error: Name is required.", file=sys.stderr)
            sys.exit(1)

        tour = manager.get_tour(args.name)
        if not tour:
            print(f"❌ Tour '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

        _play_tour(manager, tour)

def _play_tour(manager: TourManager, tour: Tour):
    """Interactive player for the tour."""
    try:
        from rich.console import Console
        from rich.syntax import Syntax
        from rich.panel import Panel
        from rich.markdown import Markdown
        console = Console()
    except ImportError:
        console = None
        print("Rich library not found. Falling back to simple output.")

    total_steps = len(tour.steps)
    if total_steps == 0:
        print("Tour has no steps.")
        return

    current_index = 0
    while True:
        step = tour.steps[current_index]

        # Clear screen (optional, maybe distracting if logs are needed, let's just print separator)
        print("\n" + "="*60)
        if console:
            console.print(f"[bold blue]Tour: {tour.title}[/bold blue] ({current_index + 1}/{total_steps})")
            console.print(Markdown(step.description))
        else:
            print(f"Tour: {tour.title} ({current_index + 1}/{total_steps})")
            print(f"Description: {step.description}")

        print(f"Location: {step.file}:{step.line}")
        print("-" * 60)

        # Read context
        try:
            file_path = manager.project_dir / step.file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                start_line = max(0, step.line - 5)
                end_line = min(len(lines), step.line + 5)

                code_snippet = "".join(lines[start_line:end_line])

                if console:
                    syntax = Syntax(code_snippet, "python", theme="monokai", line_numbers=True, start_line=start_line+1, highlight_lines={step.line})
                    console.print(Panel(syntax, title=step.file))
                else:
                    print(code_snippet)
            else:
                print(f"⚠️  File not found: {step.file}")
        except Exception as e:
            print(f"Error reading file: {e}")

        # Navigation
        print("\n[n]ext, [p]revious, [q]uit")
        try:
            choice = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("Exiting tour.")
            break

        if choice == 'q':
            break
        elif choice == 'p':
            if current_index > 0:
                current_index -= 1
            else:
                print("Already at start.")
        else: # default next
            if current_index < total_steps - 1:
                current_index += 1
            else:
                print("End of tour.")
                # Loop or quit? Let's stay at end
                retry = input("Restart? [y/N]: ").strip().lower()
                if retry == 'y':
                    current_index = 0
                else:
                    break

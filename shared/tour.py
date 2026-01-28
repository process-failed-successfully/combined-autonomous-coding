import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional

@dataclass
class TourStep:
    file: str
    line: int
    description: str

@dataclass
class Tour:
    title: str
    steps: List[TourStep] = field(default_factory=list)

class TourManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.tours_dir = self.project_dir / ".tours"
        self.tours_dir.mkdir(exist_ok=True)

    def _get_tour_path(self, name: str) -> Path:
        # Sanitize name to prevent path traversal
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
        return self.tours_dir / f"{safe_name}.json"

    def create_tour(self, name: str) -> Path:
        """Creates a new empty tour."""
        path = self._get_tour_path(name)
        if path.exists():
            raise FileExistsError(f"Tour '{name}' already exists.")

        tour = Tour(title=name)
        self._save_tour(path, tour)
        return path

    def list_tours(self) -> List[str]:
        """Lists available tours."""
        return sorted([f.stem for f in self.tours_dir.glob("*.json")])

    def get_tour(self, name: str) -> Optional[Tour]:
        """Loads a tour by name."""
        path = self._get_tour_path(name)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            steps = [TourStep(**s) for s in data.get("steps", [])]
            return Tour(title=data.get("title", name), steps=steps)
        except Exception:
            return None

    def add_step(self, tour_name: str, file_path: str, line: int, description: str) -> None:
        """Adds a step to a tour."""
        tour = self.get_tour(tour_name)
        if not tour:
            raise FileNotFoundError(f"Tour '{tour_name}' not found.")

        # Normalize file path relative to project root
        try:
            full_path = Path(file_path).resolve()
            rel_path = str(full_path.relative_to(self.project_dir))
        except ValueError:
            # If not relative to project dir, keep as is (or handle error)
            rel_path = file_path

        tour.steps.append(TourStep(file=rel_path, line=line, description=description))
        self._save_tour(self._get_tour_path(tour_name), tour)

    def delete_tour(self, name: str) -> bool:
        """Deletes a tour."""
        path = self._get_tour_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    def _save_tour(self, path: Path, tour: Tour) -> None:
        data = asdict(tour)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

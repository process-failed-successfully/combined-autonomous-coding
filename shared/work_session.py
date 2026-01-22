import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

@dataclass
class Session:
    name: str
    created_at: str
    updated_at: str
    files: List[str]
    notes: List[str]
    description: str = ""
    env_vars: Dict[str, str] = field(default_factory=dict)

class WorkSessionManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.sessions_dir = self.project_dir / ".agent_sessions"
        self.active_session_file = self.sessions_dir / "active_session.txt"
        self._ensure_sessions_dir()

    def _ensure_sessions_dir(self):
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, name: str) -> Path:
        return self.sessions_dir / f"{name}.json"

    def create(self, name: str, description: str = "") -> Session:
        if self._get_session_path(name).exists():
            raise FileExistsError(f"Session '{name}' already exists.")

        now = datetime.now().isoformat()
        session = Session(
            name=name,
            created_at=now,
            updated_at=now,
            files=[],
            notes=[],
            description=description,
            env_vars={}
        )
        self.save_session(session)
        self.set_active_session(name)
        return session

    def save_session(self, session: Session):
        session.updated_at = datetime.now().isoformat()
        path = self._get_session_path(session.name)
        with open(path, 'w') as f:
            json.dump(asdict(session), f, indent=2)

    def load_session(self, name: str) -> Optional[Session]:
        path = self._get_session_path(name)
        if not path.exists():
            return None

        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return Session(**data)
        except Exception as e:
            print(f"Error loading session {name}: {e}", file=sys.stderr)
            return None

    def list_sessions(self) -> List[Dict[str, str]]:
        sessions: List[Dict[str, str]] = []
        if not self.sessions_dir.exists():
            return sessions

        for p in self.sessions_dir.glob("*.json"):
            try:
                with open(p, 'r') as f:
                    data = json.load(f)
                    sessions.append({
                        "name": data["name"],
                        "updated_at": data["updated_at"],
                        "description": data.get("description", "")
                    })
            except Exception:
                continue
        return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)

    def set_active_session(self, name: str):
        if not self.load_session(name):
            raise FileNotFoundError(f"Session '{name}' does not exist.")
        self.active_session_file.write_text(name)

    def get_active_session(self) -> Optional[Session]:
        if not self.active_session_file.exists():
            return None
        name = self.active_session_file.read_text().strip()
        if not name:
            return None
        return self.load_session(name)

    def stop_session(self):
        if self.active_session_file.exists():
            self.active_session_file.unlink()

    def delete_session(self, name: str) -> bool:
        path = self._get_session_path(name)
        if path.exists():
            path.unlink()
            # If deleted session was active, stop it
            active = self.get_active_session()
            if active and active.name == name:
                self.stop_session()
            return True
        return False

    def add_file(self, name: str, file_path: str):
        session = self.load_session(name)
        if not session:
            raise FileNotFoundError(f"Session '{name}' not found.")

        # Resolve relative to project dir to ensure consistency
        try:
            abs_path = (self.project_dir / file_path).resolve()
            rel_path = str(abs_path.relative_to(self.project_dir))
        except ValueError:
            # If file is outside project dir, keep absolute path or warn?
            # For now, store as provided if outside, but prefer relative.
            rel_path = file_path

        if rel_path not in session.files:
            session.files.append(rel_path)
            self.save_session(session)

    def remove_file(self, name: str, file_path: str):
        session = self.load_session(name)
        if not session:
            raise FileNotFoundError(f"Session '{name}' not found.")

        if file_path in session.files:
            session.files.remove(file_path)
            self.save_session(session)

    def add_note(self, name: str, note: str):
        session = self.load_session(name)
        if not session:
            raise FileNotFoundError(f"Session '{name}' not found.")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        session.notes.append(f"[{timestamp}] {note}")
        self.save_session(session)

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Any

@dataclass
class ProductivitySession:
    id: str
    type: str  # "work", "break"
    start_time: float
    end_time: Optional[float] = None
    duration: float = 0.0
    task_id: Optional[str] = None
    notes: str = ""

@dataclass
class Distraction:
    timestamp: float
    description: str

class ProductivityManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.stats_file = self.project_dir / ".productivity_stats.json"
        self.current_session: Optional[ProductivitySession] = None
        self.sessions: List[ProductivitySession] = []
        self.distractions: List[Distraction] = []
        self.load_data()

    def load_data(self) -> None:
        if not self.stats_file.exists():
            return

        try:
            data = json.loads(self.stats_file.read_text())
            for s in data.get("sessions", []):
                self.sessions.append(ProductivitySession(**s))
            for d in data.get("distractions", []):
                self.distractions.append(Distraction(**d))
        except Exception:
            pass

    def save_data(self) -> None:
        data = {
            "sessions": [asdict(s) for s in self.sessions],
            "distractions": [asdict(d) for d in self.distractions]
        }
        self.stats_file.write_text(json.dumps(data, indent=2))

    def start_session(self, session_type: str, task_id: Optional[str] = None) -> None:
        if self.current_session:
            self.stop_session()

        self.current_session = ProductivitySession(
            id=str(int(time.time())),
            type=session_type,
            start_time=time.time(),
            task_id=task_id
        )

    def stop_session(self) -> None:
        if not self.current_session:
            return

        self.current_session.end_time = time.time()
        self.current_session.duration = self.current_session.end_time - self.current_session.start_time
        self.sessions.append(self.current_session)
        self.current_session = None
        self.save_data()

    def log_distraction(self, description: str) -> None:
        self.distractions.append(Distraction(timestamp=time.time(), description=description))
        self.save_data()

    def get_today_stats(self) -> Dict[str, Any]:
        today = date.today()
        today_sessions = [
            s for s in self.sessions
            if datetime.fromtimestamp(s.start_time).date() == today
        ]

        work_time = sum(s.duration for s in today_sessions if s.type == "work")
        break_time = sum(s.duration for s in today_sessions if s.type == "break")

        # Add current session duration if active
        if self.current_session:
            current_duration = time.time() - self.current_session.start_time
            if self.current_session.type == "work":
                work_time += current_duration
            elif self.current_session.type == "break":
                break_time += current_duration

        return {
            "work_time": work_time,
            "break_time": break_time,
            "sessions_count": len(today_sessions) + (1 if self.current_session else 0),
            "distractions": len([d for d in self.distractions if datetime.fromtimestamp(d.timestamp).date() == today])
        }

    def get_active_duration(self) -> float:
        if self.current_session:
            return time.time() - self.current_session.start_time
        return 0.0

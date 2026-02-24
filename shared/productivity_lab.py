import json
import time
import sys
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

            # Restore active session if present
            active = data.get("active_session")
            if active:
                self.current_session = ProductivitySession(**active)
        except Exception:
            pass

    def save_data(self) -> None:
        data = {
            "sessions": [asdict(s) for s in self.sessions],
            "distractions": [asdict(d) for d in self.distractions],
            "active_session": asdict(self.current_session) if self.current_session else None
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
        self.save_data()

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

def run_productivity_lab_logic(args):
    """CLI logic for Productivity Lab."""
    manager = ProductivityManager(args.project_dir.resolve())

    if args.action == "start":
        print(f"Starting {args.type} session...")
        if args.task:
            print(f"Task: {args.task}")
        manager.start_session(args.type, args.task)
        print("✅ Session started.")

    elif args.action == "stop":
        if not manager.current_session:
            print("No active session to stop.")
        else:
            duration = manager.get_active_duration()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            manager.stop_session()
            print(f"✅ Session stopped. Duration: {minutes}m {seconds}s")

    elif args.action == "status":
        if manager.current_session:
            s = manager.current_session
            duration = manager.get_active_duration()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            print(f"🔵 Active Session: {s.type.upper()}")
            print(f"   Started: {datetime.fromtimestamp(s.start_time).strftime('%H:%M:%S')}")
            print(f"   Duration: {minutes}m {seconds}s")
            if s.task_id:
                print(f"   Task: {s.task_id}")
        else:
            print("⚪ No active session.")

    elif args.action == "stats":
        stats = manager.get_today_stats()
        print("--- Today's Stats ---")
        print(f"Focus Time:   {int(stats['work_time'] // 60)}m")
        print(f"Break Time:   {int(stats['break_time'] // 60)}m")
        print(f"Sessions:     {stats['sessions_count']}")
        print(f"Distractions: {stats['distractions']}")

    elif args.action == "log":
        if not args.message:
            print("Error: --message required for logging distraction.", file=sys.stderr)
            sys.exit(1)
        manager.log_distraction(args.message)
        print("✅ Distraction logged.")

    elif args.action == "history":
        print("--- Session History (Last 10) ---")
        if not manager.sessions:
            print("No history found.")
        else:
            for s in reversed(manager.sessions[-10:]):
                start_str = datetime.fromtimestamp(s.start_time).strftime("%Y-%m-%d %H:%M")
                dur_str = f"{int(s.duration // 60)}m {int(s.duration % 60)}s"
                print(f"[{start_str}] {s.type.upper():<5} | {dur_str:<8} | {s.task_id or '-'}")

    sys.exit(0)

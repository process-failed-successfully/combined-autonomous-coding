import threading
import time
from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class AgentState:
    is_running: bool = False
    is_paused: bool = False
    iteration: int = 0
    current_task: str = "Idle"
    last_log: List[str] = field(default_factory=list)
    last_update_ts: float = 0.0


@dataclass
class AgentControl:
    stop_requested: bool = False
    pause_requested: bool = False
    resume_requested: bool = False
    skip_requested: bool = False


class StateManager:
    def __init__(self):
        self._state = AgentState()
        self._control = AgentControl()
        self._lock = threading.Lock()

    def update_state(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                if hasattr(self._state, k):
                    setattr(self._state, k, v)
            self._state.last_update_ts = time.time()

    def get_state(self) -> dict:
        with self._lock:
            return asdict(self._state)

    def request_stop(self):
        with self._lock:
            self._control.stop_requested = True

    def request_pause(self):
        with self._lock:
            self._control.pause_requested = True
            self._control.resume_requested = False

    def request_resume(self):
        with self._lock:
            self._control.resume_requested = True
            self._control.pause_requested = False

    def request_skip(self):
        with self._lock:
            self._control.skip_requested = True

    def check_control(self) -> AgentControl:
        with self._lock:
            # Return a copy to safely check
            return AgentControl(**asdict(self._control))

    def clear_skip(self):
        with self._lock:
            self._control.skip_requested = False

    def is_paused(self) -> bool:
        with self._lock:
            return self._control.pause_requested


import requests
import time
import socket
import concurrent.futures
from dataclasses import asdict
from typing import List, Optional
from shared.state import AgentState, AgentControl # We'll reuse these dataclasses effectively

class AgentClient:
    """
    Client for Agents to communicate with the Dashboard.
    """
    def __init__(self, agent_id: str, dashboard_url: str = "http://localhost:8000"):
        self.agent_id = agent_id
        self.dashboard_url = dashboard_url.rstrip("/")
        # We maintain a local control state
        self.local_control = AgentControl()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def report_state(self, **kwargs):
        """
        Send state update to dashboard (non-blocking).
        """
        self._executor.submit(self._do_report_state, kwargs)

    def _do_report_state(self, kwargs):
        try:
            url = f"{self.dashboard_url}/api/agents/{self.agent_id}/heartbeat"
            requests.post(url, json=kwargs, timeout=2) # Short timeout
        except Exception as e:
            # Silent fail is better than crashing agent
            pass

    def poll_commands(self) -> AgentControl:
        """
        Get pending commands and update local control state.
        """
        try:
            url = f"{self.dashboard_url}/api/agents/{self.agent_id}/commands"
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                commands = data.get("commands", [])
                for cmd in commands:
                    self._apply_command(cmd)
        except Exception:
            pass
        
        return self.local_control

    def _apply_command(self, cmd: str):
        if cmd == "stop":
            self.local_control.stop_requested = True
        elif cmd == "pause":
            self.local_control.pause_requested = True
        elif cmd == "resume":
            self.local_control.pause_requested = False # Resume clears pause
        elif cmd == "skip":
            self.local_control.skip_requested = True

    def clear_skip(self):
        self.local_control.skip_requested = False

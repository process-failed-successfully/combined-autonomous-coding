
import requests
import time
import concurrent.futures
import threading
# We'll reuse these dataclasses effectively
from shared.state import AgentControl


class AgentClient:
    """
    Client for Agents to communicate with the Dashboard.
    """

    def __init__(
            self,
            agent_id: str,
            dashboard_url: str = "http://localhost:8000"):
        self.agent_id = agent_id
        self.dashboard_url = dashboard_url.rstrip("/")
        # We maintain a local control state
        self.local_control = AgentControl()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        # Background Heartbeat
        self._stop_event = threading.Event()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def _heartbeat_loop(self):
        """
        Sends a heartbeat every 5 seconds to keep the agent 'online'.
        """
        while not self._stop_event.is_set():
            try:
                # We send a minimal heartbeat, just to update the timestamp
                # The server merges this with existing state
                self._do_report_state({})
            except Exception:
                pass
            time.sleep(5)

    def stop(self):
        self._stop_event.set()

    def report_state(self, **kwargs):
        """
        Send state update to dashboard (non-blocking).
        """
        self._executor.submit(self._do_report_state, kwargs)

    def _do_report_state(self, kwargs):
        try:
            url = f"{self.dashboard_url}/api/agents/{self.agent_id}/heartbeat"
            requests.post(url, json=kwargs, timeout=2)  # Short timeout
        except Exception:
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
            self.local_control.pause_requested = False  # Resume clears pause
        elif cmd == "skip":
            self.local_control.skip_requested = True

    def clear_skip(self):
        self.local_control.skip_requested = False

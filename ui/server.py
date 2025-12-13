
import http.server
import socketserver
import json
import threading
import time
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List

# --- Data Structures ---


@dataclass
class AgentState:
    id: str
    is_running: bool = False
    is_paused: bool = False
    iteration: int = 0
    current_task: str = "Idle"
    last_log: List[str] = field(default_factory=list)
    last_heartbeat: float = 0.0
    
    # New Metrics
    loc_count: int = 0
    manager_approvals: int = 0
    manager_rejections: int = 0
    
    # Persistence helpers
    total_iterations: int = 0
    last_session_iteration: int = 0  # To track delta within a session

    # Advanced Dev Metrics (15+)
    start_time: float = field(default_factory=time.time)
    error_count: int = 0  # Current session errors
    total_errors: int = 0 # Cumulative
    
    # Tool Usage (Cumulative)
    tool_usage: Dict[str, int] = field(default_factory=lambda: {
        "bash": 0, "write": 0, "read": 0, "search": 0
    })
    
    # Timing (Current Session Averages)
    avg_iteration_time: float = 0.0
    avg_llm_latency: float = 0.0
    avg_tool_execution_time: float = 0.0
    
    # Feature Tracking
    feature_completion_count: int = 0
    feature_completion_pct: float = 0.0


@dataclass
class AgentQueue:
    commands: List[str] = field(default_factory=list)


class DashboardState:
    def __init__(self, persistence_file: str = "dashboard_state.json"):
        self.agents: Dict[str, AgentState] = {}
        self.queues: Dict[str, AgentQueue] = {}
        self.persistence_file = Path(persistence_file)
        self.lock = threading.Lock()
        self.dirty = False
        self._load()

        # Start background saver
        self.running = True
        self.saver_thread = threading.Thread(
            target=self._background_saver, daemon=True)
        self.saver_thread.start()

    def _background_saver(self):
        while self.running:
            time.sleep(1)

            # Run cleanup every iteration
            self._cleanup_stale_agents()

            with self.lock:
                if not self.dirty:
                    continue
                # Snapshot data while locked
                data = {k: asdict(v) for k, v in self.agents.items()}
                self.dirty = False

            # Save to disk outside lock
            try:
                self.persistence_file.write_text(json.dumps(data, indent=2))
            except Exception as e:
                print(f"Error saving state: {e}")

    def _cleanup_stale_agents(self):
        # Mark agents as offline if they haven't heartbeat in 30 seconds
        # Do NOT delete them, to preserve stats.
        threshold = 30
        now = time.time()
        
        with self.lock:
            for agent_id, agent in self.agents.items():
                if agent.is_running and agent.last_heartbeat > 0 and (now - agent.last_heartbeat) > threshold:
                    print(f"Marking agent offline: {agent_id}")
                    agent.is_running = False
                    self.dirty = True

    def update_agent(self, agent_id: str, data: dict):
        with self.lock:
            if agent_id not in self.agents:
                self.agents[agent_id] = AgentState(id=agent_id)
                self.queues[agent_id] = AgentQueue()  # Init queue

            agent = self.agents[agent_id]
            
            # Special handling for metrics
            if 'iteration' in data:
                new_iter = data['iteration']
                
                # Logic to accumulate total iterations
                delta = 0
                if new_iter < agent.last_session_iteration:
                    # Agent restarted
                    delta = new_iter
                else:
                    delta = new_iter - agent.last_session_iteration
                
                if delta > 0:
                    agent.total_iterations += delta
                
                agent.last_session_iteration = new_iter

            # Handle Tool Usage Merging (Cumulative)
            if 'tool_usage' in data:
                new_usage = data['tool_usage']
                # Data comes in as cumulative for the session usually, or delta?
                # Let's assume the agent reports its CURRENT SESSION total.
                # But if we want proper cumulative across restarts, we need to handle it like iterations.
                # Actually, complexity: The agent might just report {bash: 1} for a single turn?
                # No, typically state is a snapshot.
                # Let's assume the agent reports a DELTA dictionary for this heartbeat? 
                # OR the agent reports its full session counters.
                # Let's assume the agent reports DELTA (increment) to simplify backend aggregation?
                # No, heartbeats usually replace state.
                # Strategy: Backend maintains `total_tool_usage`. 
                # Agent reports component `tool_usage_delta`?
                # EASIER: Agent reports `tool_usage_session`. Backend keeps `tool_usage_historical` + `tool_usage_session`.
                # FOR NOW: Let's assume simple replacement for stats that are averages.
                # For counts, we'll assume the agent sends a DELTA if key is `tool_usage_delta`.
                # If key is `tool_usage`, we replace it? No that resets history.
                
                # Re-decision: Client will send `tool_usage_delta` for increments.
                pass # Handled in loop below if we rename keys or specific logic

            # Handle Error Count (Cumulative)
            if 'error_match' in data: # signal to increment
                agent.total_errors += 1
                agent.error_count += 1
            
            # Generic Update
            for k, v in data.items():
                if k == 'tool_usage_delta':
                    # Merge delta
                    for tool, count in v.items():
                        agent.tool_usage[tool] = agent.tool_usage.get(tool, 0) + count
                elif k == 'tool_usage':
                     # If we receive full usage, maybe just set it? NO, cumulative is key.
                     # Ignore full usage replacement if we rely on deltas.
                     pass
                elif hasattr(agent, k) and k not in ['total_iterations', 'last_session_iteration', 'total_errors', 'tool_usage']:
                    setattr(agent, k, v)
            
            agent.last_heartbeat = time.time()
            # If we receive a heartbeat, it is running
            agent.is_running = True
            
            self.dirty = True

    def get_agent_commands(self, agent_id: str) -> List[str]:
        with self.lock:
            if agent_id in self.queues:
                cmds = self.queues[agent_id].commands
                self.queues[agent_id].commands = []  # Clear after reading
                return cmds
            return []

    def queue_command(self, agent_id: str, command: str):
        with self.lock:
            if agent_id not in self.queues:
                self.queues[agent_id] = AgentQueue()
            self.queues[agent_id].commands.append(command)

    def get_all_agents(self) -> List[dict]:
        with self.lock:
            return [asdict(a) for a in self.agents.values()]

    def _save(self):
        # Immediate save (used for shutdown or forced save)
        try:
            with self.lock:
                data = {k: asdict(v) for k, v in self.agents.items()}
                self.dirty = False
            self.persistence_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving state: {e}")

    def _load(self):
        if self.persistence_file.exists():
            try:
                data = json.loads(self.persistence_file.read_text())
                for k, v in data.items():
                    self.agents[k] = AgentState(**v)
                    self.queues[k] = AgentQueue()
            except Exception as e:
                print(f"Error loading state: {e}")

# --- Server Handler ---


class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, db_state=None, **kwargs):
        self.db_state = db_state
        # Serve from React Build Dir
        self.static_dir = Path(__file__).parent / "frontend/dist"
        super().__init__(*args, directory=str(self.static_dir), **kwargs)

    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        # API: Get All Agents
        if self.path == '/api/dashboard':
            self._send_json(self.db_state.get_all_agents())
            return

        # API: Poll Commands for Agent
        # /api/agents/{id}/commands
        match = re.match(r'/api/agents/([^/]+)/commands', self.path)
        if match:
            agent_id = match.group(1)
            cmds = self.db_state.get_agent_commands(agent_id)
            self._send_json({"commands": cmds})
            return

        super().do_GET()

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        data = json.loads(body)

        # API: Agent Heartbeat
        # /api/agents/{id}/heartbeat
        match = re.match(r'/api/agents/([^/]+)/heartbeat', self.path)
        if match:
            agent_id = match.group(1)
            self.db_state.update_agent(agent_id, data)
            self._send_json({"status": "ok"})
            return

        # API: Send Command to Agent (From Frontend)
        # /api/control
        if self.path == '/api/control':
            agent_id = data.get('agent_id')
            cmd = data.get('command')
            if agent_id and cmd:
                self.db_state.queue_command(agent_id, cmd)
                self._send_json({"status": "queued"})
            else:
                self.send_error(400, "Missing agent_id or command")
            return

        self.send_error(404)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass


def start_server(port=8000, persistence_file="dashboard_state.json"):
    db_state = DashboardState(persistence_file)

    def handler(*args, **kwargs):
        return DashboardRequestHandler(*args, db_state=db_state, **kwargs)
    server = ThreadedHTTPServer(('0.0.0.0', port), handler)
    print(f"Dashboard running on http://0.0.0.0:{port}")
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server, db_state


if __name__ == "__main__":
    s, _ = start_server()
    while True:
        time.sleep(1)

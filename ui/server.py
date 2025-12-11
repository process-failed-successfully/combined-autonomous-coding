
import http.server
import socketserver
import json
import threading
import time
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import os

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
        self.saver_thread = threading.Thread(target=self._background_saver, daemon=True)
        self.saver_thread.start()

    def _background_saver(self):
        while self.running:
            time.sleep(1)
            
            # Run cleanup every iteration (every 1s is fine, or modulo it)
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
        # Remove agents that haven't heartbeat in 30 seconds
        threshold = 30
        now = time.time()
        to_remove = []
        
        with self.lock:
            for agent_id, agent in self.agents.items():
                # If last_heartbeat is 0, it might be new, but we init with time.time() usually?
                # Actually AgentState default is 0.0. Let's assume we update it on first heartbeat.
                # If it's 0.0, we probably shouldn't kill it immediately unless it's really old persistence data?
                # Let's say if (now - last_heartbeat) > threshold
                if agent.last_heartbeat > 0 and (now - agent.last_heartbeat) > threshold:
                    to_remove.append(agent_id)
            
            for agent_id in to_remove:
                print(f"Removing stale agent: {agent_id}")
                del self.agents[agent_id]
                if agent_id in self.queues:
                    del self.queues[agent_id]
                self.dirty = True

    def update_agent(self, agent_id: str, data: dict):
        with self.lock:
            if agent_id not in self.agents:
                self.agents[agent_id] = AgentState(id=agent_id)
                self.queues[agent_id] = AgentQueue() # Init queue
            
            agent = self.agents[agent_id]
            for k, v in data.items():
                if hasattr(agent, k):
                    setattr(agent, k, v)
            agent.last_heartbeat = time.time()
            self.dirty = True

    def get_agent_commands(self, agent_id: str) -> List[str]:
        with self.lock:
            if agent_id in self.queues:
                cmds = self.queues[agent_id].commands
                self.queues[agent_id].commands = [] # Clear after reading
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
    handler = lambda *args, **kwargs: DashboardRequestHandler(*args, db_state=db_state, **kwargs)
    server = ThreadedHTTPServer(('0.0.0.0', port), handler)
    print(f"Dashboard running on http://0.0.0.0:{port}")
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server, db_state

if __name__ == "__main__":
    s, _ = start_server()
    while True:
        time.sleep(1)

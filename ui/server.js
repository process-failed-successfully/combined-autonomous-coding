const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 7654;
const DASHBOARD_STATE_FILE = path.join(__dirname, '../dashboard_state.json');

app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

// In-memory state
let agents = {};

// Load state on startup
try {
    if (fs.existsSync(DASHBOARD_STATE_FILE)) {
        const data = fs.readFileSync(DASHBOARD_STATE_FILE, 'utf8');
        if (data.trim()) {
            agents = JSON.parse(data);
        }
    }
} catch (err) {
    console.error('Error loading dashboard state:', err);
}

// Helper to save state
const saveState = () => {
    try {
        fs.writeFileSync(DASHBOARD_STATE_FILE, JSON.stringify(agents, null, 2));
    } catch (err) {
        console.error('Error saving dashboard state:', err);
    }
};

// --- Agent API Endpoints ---

// Heartbeat from Agent
app.post('/api/agents/:id/heartbeat', (req, res) => {
    const agentId = req.params.id;
    const update = req.body;

    if (!agents[agentId]) {
        agents[agentId] = {
            id: agentId,
            state: {},
            commands: [],
            last_seen: 0
        };
    }

    agents[agentId].last_seen = Date.now();
    // Merge state updates
    agents[agentId].state = { ...agents[agentId].state, ...update };

    // Clean up ancient agents? Maybe later. For now just persist.
    saveState();

    res.json({ status: 'ok' });
});

// Get Commands for Agent
app.get('/api/agents/:id/commands', (req, res) => {
    const agentId = req.params.id;

    if (agents[agentId] && agents[agentId].commands && agents[agentId].commands.length > 0) {
        const cmds = agents[agentId].commands;
        agents[agentId].commands = []; // Clear commands after sending
        saveState();
        res.json({ commands: cmds });
    } else {
        res.json({ commands: [] });
    }
});

// --- UI API Endpoints ---

// Get all agents for UI
app.get('/api/ui/agents', (req, res) => {
    // Add computed status (active/offline)
    const now = Date.now();
    const agentList = Object.values(agents).map(agent => {
        const isOnline = (now - agent.last_seen) < 15000; // 15 seconds threshold
        return {
            ...agent,
            status: isOnline ? 'Active' : 'Offline'
        };
    });
    res.json({ agents: agentList });
});

// Send command to agent from UI
app.post('/api/ui/command', (req, res) => {
    const { agent_id, command } = req.body;

    if (!agents[agent_id]) {
        return res.status(404).json({ error: 'Agent not found' });
    }

    if (!agents[agent_id].commands) {
        agents[agent_id].commands = [];
    }

    agents[agent_id].commands.push(command);
    saveState();

    res.json({ status: 'ok', message: `Command ${command} queued for ${agent_id}` });
});

app.listen(PORT, () => {
    console.log(`Dashboard server running on http://localhost:${PORT}`);
});

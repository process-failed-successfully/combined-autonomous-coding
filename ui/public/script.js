document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('agents-container');

    // Poll every 2 seconds
    setInterval(fetchAgents, 2000);
    fetchAgents(); // Initial fetch

    async function fetchAgents() {
        try {
            const response = await fetch('/api/ui/agents');
            const data = await response.json();
            renderAgents(data.agents);
        } catch (error) {
            console.error('Error fetching agents:', error);
            // Don't clear UI on transient error, just log
        }
    }

    function renderAgents(agents) {
        if (!agents || agents.length === 0) {
            container.innerHTML = '<p class="loading">No agents found.</p>';
            return;
        }

        // We re-render all for simplicity, can be optimized to diff later
        container.innerHTML = '';

        agents.forEach(agent => {
            const card = document.createElement('div');
            card.className = `agent-card ${agent.status === 'Active' ? 'active' : ''}`;

            // Build Controls based on state (simplified)
            // You might want to disable Resume if not paused, etc. but let's just show all for now.
            const controlsHtml = `
                <div class="agent-controls">
                    <button class="btn btn-pause" onclick="sendCommand('${agent.id}', 'pause')">Pause</button>
                    <button class="btn btn-resume" onclick="sendCommand('${agent.id}', 'resume')">Resume</button>
                    <button class="btn btn-skip" onclick="sendCommand('${agent.id}', 'skip')">Skip Step</button>
                    <button class="btn btn-stop" onclick="sendCommand('${agent.id}', 'stop')">Stop</button>
                </div>
            `;

            // Display interesting state props
            let stateDetails = '';
            if (agent.state) {
                 // Common properties in state
                 const props = ['step', 'status', 'current_file'];
                 props.forEach(prop => {
                     if (agent.state[prop]) {
                         stateDetails += `
                            <div class="detail-row">
                                <span class="detail-label">${prop}:</span>
                                <span class="detail-value">${agent.state[prop]}</span>
                            </div>
                         `;
                     }
                 });
            }

            // Build log view
            let logsHtml = '';
            if (agent.state && agent.state.logs && agent.state.logs.length > 0) {
                logsHtml = `
                    <div class="log-preview">
                        ${agent.state.logs.map(line => `<div>${line}</div>`).join('')}
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="agent-header">
                    <span class="agent-id">${agent.id}</span>
                    <span class="agent-status">${agent.status}</span>
                </div>
                <div class="agent-details">
                    ${stateDetails || '<div class="detail-row">Waiting for heartbeat...</div>'}
                </div>
                ${logsHtml}
                ${controlsHtml}
            `;

            container.appendChild(card);
        });
    }

    window.sendCommand = async (agentId, command) => {
        try {
            const res = await fetch('/api/ui/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: agentId, command: command })
            });
            const result = await res.json();
            console.log(result.message);
            alert(`Sent ${command} to ${agentId}`);
        } catch (error) {
            console.error('Error sending command:', error);
            alert('Failed to send command');
        }
    };
});

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

        // Optimization: Track seen agents to remove stale ones later
        const seenIds = new Set();

        agents.forEach(agent => {
            seenIds.add(agent.id);
            const cardId = `agent-${agent.id}`;
            let card = document.getElementById(cardId);
            const htmlContent = buildAgentCardHtml(agent);
            const className = `agent-card ${agent.status === 'Active' ? 'active' : ''}`;

            if (card) {
                // Update existing card only if content changed
                if (card.innerHTML !== htmlContent) {
                    card.innerHTML = htmlContent;
                }
                if (card.className !== className) {
                    card.className = className;
                }
            } else {
                // Create new card
                card = document.createElement('div');
                card.id = cardId;
                card.className = className;
                card.innerHTML = htmlContent;
                container.appendChild(card);
            }
        });

        // Clean up agents that are no longer present
        // Convert to array to avoid live collection issues during removal
        const currentCards = Array.from(container.getElementsByClassName('agent-card'));
        currentCards.forEach(card => {
            const agentId = card.id.replace('agent-', '');
            if (!seenIds.has(agentId)) {
                card.remove();
            }
        });

        // Remove loading message if it exists and we have agents
        const loadingMsg = container.querySelector('.loading');
        if (loadingMsg && agents.length > 0) {
            loadingMsg.remove();
        }
    }

    function escapeHtml(text) {
        if (text === null || text === undefined) return '';
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function buildAgentCardHtml(agent) {
        // Build Controls based on state (simplified)
        // Using data attributes prevents XSS in onclick handlers
        const controlsHtml = `
            <div class="agent-controls">
                <button class="btn btn-pause" data-id="${escapeHtml(agent.id)}" onclick="sendCommand(this.dataset.id, 'pause')">Pause</button>
                <button class="btn btn-resume" data-id="${escapeHtml(agent.id)}" onclick="sendCommand(this.dataset.id, 'resume')">Resume</button>
                <button class="btn btn-skip" data-id="${escapeHtml(agent.id)}" onclick="sendCommand(this.dataset.id, 'skip')">Skip Step</button>
                <button class="btn btn-stop" data-id="${escapeHtml(agent.id)}" onclick="sendCommand(this.dataset.id, 'stop')">Stop</button>
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
                            <span class="detail-label">${escapeHtml(prop)}:</span>
                            <span class="detail-value">${escapeHtml(agent.state[prop])}</span>
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
                    ${agent.state.logs.map(line => `<div>${escapeHtml(line)}</div>`).join('')}
                </div>
            `;
        }

        return `
            <div class="agent-header">
                <span class="agent-id">${escapeHtml(agent.id)}</span>
                <span class="agent-status">${escapeHtml(agent.status)}</span>
            </div>
            <div class="agent-details">
                ${stateDetails || '<div class="detail-row">Waiting for heartbeat...</div>'}
            </div>
            ${logsHtml}
            ${controlsHtml}
        `;
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

// Hrisa Code Web UI Application
const API_BASE = window.location.origin + '/api';
const WS_URL = `ws://${window.location.host}/ws`;

// Application State
const state = {
    agents: new Map(),
    selectedAgentId: null,
    statusFilters: new Set(['running', 'stuck']),
    roles: [],
    ws: null,
    wsReconnectAttempts: 0,
    wsMaxReconnectAttempts: 5,
};

// DOM Elements
const elements = {
    agentList: document.getElementById('agent-list'),
    detailPanel: document.getElementById('detail-panel'),
    detailContent: document.getElementById('detail-content'),
    createAgentBtn: document.getElementById('create-agent-btn'),
    createAgentModal: document.getElementById('create-agent-modal'),
    createAgentForm: document.getElementById('create-agent-form'),
    instructionModal: document.getElementById('instruction-modal'),
    instructionForm: document.getElementById('instruction-form'),
    connectionStatus: document.getElementById('connection-status'),
    statRunning: document.getElementById('stat-running'),
    statStuck: document.getElementById('stat-stuck'),
    statCompleted: document.getElementById('stat-completed'),
    closeDetailBtn: document.getElementById('close-detail-btn'),
    refreshBtn: document.getElementById('refresh-btn'),
    clearCompletedBtn: document.getElementById('clear-completed-btn'),
};

// WebSocket Connection
function connectWebSocket() {
    try {
        state.ws = new WebSocket(WS_URL);

        state.ws.onopen = () => {
            console.log('WebSocket connected');
            state.wsReconnectAttempts = 0;
            updateConnectionStatus('connected');
        };

        state.ws.onmessage = (event) => {
            // Ignore ping/pong messages
            if (event.data === 'pong' || event.data === 'ping') {
                return;
            }

            try {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            } catch (e) {
                console.warn('Failed to parse WebSocket message:', event.data, e);
            }
        };

        state.ws.onclose = () => {
            console.log('WebSocket closed');
            updateConnectionStatus('disconnected');

            // Attempt reconnection
            if (state.wsReconnectAttempts < state.wsMaxReconnectAttempts) {
                state.wsReconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, state.wsReconnectAttempts), 30000);
                console.log(`Reconnecting in ${delay}ms...`);
                setTimeout(connectWebSocket, delay);
            }
        };

        state.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        // Keep-alive ping
        setInterval(() => {
            if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                state.ws.send('ping');
            }
        }, 30000);

    } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        updateConnectionStatus('disconnected');
    }
}

function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'connected':
            console.log('WebSocket handshake complete');
            break;

        case 'agent_status':
            const { agent_id, agent } = message.data;
            state.agents.set(agent_id, agent);
            updateAgentCard(agent_id);
            updateStats();

            if (state.selectedAgentId === agent_id) {
                renderAgentDetail(agent_id);
            }
            break;

        case 'agent_message':
            const agentId = message.data.agent_id;
            const currentAgent = state.agents.get(agentId);
            if (currentAgent && state.selectedAgentId === agentId) {
                renderAgentDetail(agentId);
            }
            break;

        case 'agent_stuck':
            showNotification(
                `Agent ${message.data.agent_id.substring(0, 8)} is stuck!`,
                'warning'
            );
            break;
    }
}

function updateConnectionStatus(status) {
    const statusDot = elements.connectionStatus.querySelector('.status-dot');
    const statusText = elements.connectionStatus.querySelector('span:last-child');

    statusDot.className = `status-dot ${status}`;

    switch (status) {
        case 'connecting':
            statusText.textContent = 'Connecting...';
            break;
        case 'connected':
            statusText.textContent = 'Connected';
            break;
        case 'disconnected':
            statusText.textContent = 'Disconnected';
            break;
    }
}

// API Functions
async function loadRoles() {
    try {
        const response = await fetch(`${API_BASE}/roles`);
        if (!response.ok) throw new Error('Failed to fetch roles');
        state.roles = await response.json();

        // Populate role dropdown
        const roleSelect = document.getElementById('role-input');
        if (roleSelect) {
            roleSelect.innerHTML = state.roles.map(role =>
                `<option value="${role.id}">${role.icon} ${role.name}</option>`
            ).join('');
        }
    } catch (error) {
        console.error('Error loading roles:', error);
    }
}

async function fetchAgents() {
    try {
        const response = await fetch(`${API_BASE}/agents`);
        if (!response.ok) throw new Error('Failed to fetch agents');
        const agents = await response.json();

        state.agents.clear();
        agents.forEach(agent => {
            state.agents.set(agent.id, agent);
        });

        renderAgentList();
        updateStats();
    } catch (error) {
        console.error('Error fetching agents:', error);
        showNotification('Failed to load agents', 'error');
    }
}

async function createAgent(task, workingDir, model, role, tags) {
    try {
        const response = await fetch(`${API_BASE}/agents`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task,
                working_dir: workingDir || null,
                model: model || null,
                role: role || 'general',
                tags: tags || [],
            }),
        });

        if (!response.ok) throw new Error('Failed to create agent');
        const agent = await response.json();

        // Start the agent
        await startAgent(agent.id);

        showNotification('Agent created and started', 'success');
        return agent;
    } catch (error) {
        console.error('Error creating agent:', error);
        showNotification('Failed to create agent', 'error');
        throw error;
    }
}

async function startAgent(agentId) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/start`, {
            method: 'POST',
        });

        if (!response.ok) throw new Error('Failed to start agent');
    } catch (error) {
        console.error('Error starting agent:', error);
        throw error;
    }
}

async function sendInstruction(agentId, instruction) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/instruction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction }),
        });

        if (!response.ok) throw new Error('Failed to send instruction');
        showNotification('Instruction sent', 'success');
    } catch (error) {
        console.error('Error sending instruction:', error);
        showNotification('Failed to send instruction', 'error');
    }
}

async function cancelAgent(agentId) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/cancel`, {
            method: 'POST',
        });

        if (!response.ok) throw new Error('Failed to cancel agent');
        showNotification('Agent cancelled', 'success');
    } catch (error) {
        console.error('Error cancelling agent:', error);
        showNotification('Failed to cancel agent', 'error');
    }
}

async function deleteAgent(agentId) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}`, {
            method: 'DELETE',
        });

        if (!response.ok) throw new Error('Failed to delete agent');

        state.agents.delete(agentId);
        if (state.selectedAgentId === agentId) {
            state.selectedAgentId = null;
            closeDetailPanel();
        }

        renderAgentList();
        updateStats();
        showNotification('Agent deleted', 'success');
    } catch (error) {
        console.error('Error deleting agent:', error);
        showNotification('Failed to delete agent', 'error');
    }
}

async function fetchAgentMessages(agentId) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/messages`);
        if (!response.ok) throw new Error('Failed to fetch messages');
        return await response.json();
    } catch (error) {
        console.error('Error fetching messages:', error);
        return [];
    }
}

async function fetchAgentLogs(agentId) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/logs`);
        if (!response.ok) throw new Error('Failed to fetch logs');
        return await response.json();
    } catch (error) {
        console.error('Error fetching logs:', error);
        return [];
    }
}

async function fetchAgentArtifacts(agentId) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/artifacts`);
        if (!response.ok) throw new Error('Failed to fetch artifacts');
        return await response.json();
    } catch (error) {
        console.error('Error fetching artifacts:', error);
        return [];
    }
}

// Rendering Functions
function getRoleInfo(roleId) {
    const role = state.roles.find(r => r.id === roleId);
    return role || { id: 'general', name: 'General', icon: '⚙️', color: '#6b7280' };
}

function renderAgentList() {
    const filteredAgents = Array.from(state.agents.values())
        .filter(agent => state.statusFilters.has(agent.status))
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    if (filteredAgents.length === 0) {
        elements.agentList.innerHTML = '<div class="empty-state"><p>No agents match the current filters.</p></div>';
        return;
    }

    elements.agentList.innerHTML = filteredAgents.map(agent => {
        const roleInfo = getRoleInfo(agent.role);
        return `
        <div class="agent-card ${state.selectedAgentId === agent.id ? 'selected' : ''}"
             data-agent-id="${agent.id}"
             onclick="selectAgent('${agent.id}')">
            <div class="agent-card-header">
                <div class="agent-id">${agent.id.substring(0, 8)}</div>
                <div class="agent-status ${agent.status}">${agent.status}</div>
            </div>
            <div class="agent-role" style="background: ${roleInfo.color}20; color: ${roleInfo.color}; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; margin: 8px 0; display: inline-block;">
                ${roleInfo.icon} ${roleInfo.name}
            </div>
            <div class="agent-task">${escapeHtml(agent.task.substring(0, 150))}${agent.task.length > 150 ? '...' : ''}</div>
            <div class="agent-meta">
                <span>🤖 ${agent.model}</span>
                <span>📁 ${agent.working_dir.split('/').pop()}</span>
                <span>💬 ${agent.message_count}</span>
            </div>
            ${agent.progress.total_steps > 0 ? `
                <div class="agent-progress">
                    <div class="progress-bar">
                        <div class="progress-fill ${agent.status === 'stuck' ? 'stuck' : ''}"
                             style="width: ${(agent.progress.completed_steps / agent.progress.total_steps * 100)}%"></div>
                    </div>
                    <div class="progress-stats">
                        <span>📊 ${agent.progress.completed_steps}/${agent.progress.total_steps} steps</span>
                        <span>🔧 ${agent.progress.tool_calls} tools</span>
                        ${agent.progress.loop_detections > 0 ? `<span>🔄 ${agent.progress.loop_detections} loops</span>` : ''}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
    }).join('');
}

function updateAgentCard(agentId) {
    const card = document.querySelector(`[data-agent-id="${agentId}"]`);
    if (card) {
        // Re-render the entire list to ensure consistency
        renderAgentList();
    } else {
        // New agent, add to list
        renderAgentList();
    }
}

async function selectAgent(agentId) {
    state.selectedAgentId = agentId;
    renderAgentList();
    openDetailPanel();
    await renderAgentDetail(agentId);
}

async function renderAgentDetail(agentId) {
    const agent = state.agents.get(agentId);
    if (!agent) return;

    const messages = await fetchAgentMessages(agentId);
    const logs = await fetchAgentLogs(agentId);
    const artifacts = await fetchAgentArtifacts(agentId);
    const roleInfo = getRoleInfo(agent.role);

    elements.detailContent.innerHTML = `
        <div class="detail-section">
            <h3>Agent Information</h3>
            <div class="detail-info">
                <div class="detail-info-item">
                    <span class="detail-info-label">ID:</span>
                    <span class="detail-info-value">${agent.id}</span>
                </div>
                <div class="detail-info-item">
                    <span class="detail-info-label">Status:</span>
                    <span class="detail-info-value">
                        <span class="agent-status ${agent.status}">${agent.status}</span>
                    </span>
                </div>
                <div class="detail-info-item">
                    <span class="detail-info-label">Role:</span>
                    <span class="detail-info-value">
                        <span style="background: ${roleInfo.color}20; color: ${roleInfo.color}; padding: 4px 8px; border-radius: 4px; display: inline-block;">
                            ${roleInfo.icon} ${roleInfo.name}
                        </span>
                    </span>
                </div>
                <div class="detail-info-item">
                    <span class="detail-info-label">Model:</span>
                    <span class="detail-info-value">${agent.model}</span>
                </div>
                <div class="detail-info-item">
                    <span class="detail-info-label">Created:</span>
                    <span class="detail-info-value">${formatDate(agent.created_at)}</span>
                </div>
                <div class="detail-info-item">
                    <span class="detail-info-label">Working Dir:</span>
                    <span class="detail-info-value">${agent.working_dir}</span>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h3>Task</h3>
            <div class="detail-info-item">
                <span class="detail-info-value">${escapeHtml(agent.task)}</span>
            </div>
        </div>

        ${agent.stuck_reason ? `
            <div class="detail-section">
                <h3>Stuck Reason</h3>
                <div class="detail-info-item" style="background: var(--accent-warning); color: #000;">
                    <span class="detail-info-value">${escapeHtml(agent.stuck_reason)}</span>
                </div>
            </div>
        ` : ''}

        ${agent.error ? `
            <div class="detail-section">
                <h3>Error</h3>
                <div class="detail-info-item" style="background: var(--accent-danger); color: #fff;">
                    <span class="detail-info-value">${escapeHtml(agent.error)}</span>
                </div>
            </div>
        ` : ''}

        <div class="detail-section">
            <h3>Progress</h3>
            <div class="detail-info">
                <div class="detail-info-item">
                    <span class="detail-info-label">Steps:</span>
                    <span class="detail-info-value">${agent.progress.completed_steps}/${agent.progress.total_steps}</span>
                </div>
                <div class="detail-info-item">
                    <span class="detail-info-label">Tool Calls:</span>
                    <span class="detail-info-value">${agent.progress.tool_calls}</span>
                </div>
                <div class="detail-info-item">
                    <span class="detail-info-label">Loop Detections:</span>
                    <span class="detail-info-value">${agent.progress.loop_detections}</span>
                </div>
                <div class="detail-info-item">
                    <span class="detail-info-label">Errors:</span>
                    <span class="detail-info-value">${agent.progress.errors}</span>
                </div>
                <div class="detail-info-item">
                    <span class="detail-info-label">Last Activity:</span>
                    <span class="detail-info-value">${formatDate(agent.progress.last_activity)}</span>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h3>Execution Logs (${logs.length})</h3>
            <div class="log-list" style="max-height: 300px; overflow-y: auto; background: var(--sand-100); padding: 12px; border-radius: 6px; font-family: monospace; font-size: 0.9em;">
                ${logs.length > 0 ? logs.map(log => {
                    const levelColors = {
                        'info': 'var(--sand-800)',
                        'error': 'var(--accent-danger)',
                        'debug': 'var(--sand-600)',
                        'tool': 'var(--brand-500)',
                        'iteration': 'var(--terracotta-500)'
                    };
                    const color = levelColors[log.level] || 'var(--sand-700)';
                    return `
                    <div class="log-entry" style="margin-bottom: 8px; padding: 6px; background: var(--sand-50); border-left: 3px solid ${color};">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="color: ${color}; font-weight: 600;">[${log.level.toUpperCase()}]</span>
                            <span style="color: var(--sand-600); font-size: 0.85em;">${formatTime(log.timestamp)}</span>
                        </div>
                        <div style="color: var(--sand-900);">${escapeHtml(log.message)}</div>
                        ${log.metadata ? `<div style="color: var(--sand-600); font-size: 0.85em; margin-top: 4px;">${JSON.stringify(log.metadata)}</div>` : ''}
                    </div>
                `;
                }).join('') : '<div class="empty-state"><p>No logs yet</p></div>'}
            </div>
        </div>

        <div class="detail-section">
            <h3>Artifacts (${artifacts.length})</h3>
            <div class="artifacts-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px;">
                ${artifacts.length > 0 ? artifacts.map(artifact => {
                    const typeIcons = {
                        'code': '💻',
                        'document': '📄',
                        'data': '📊',
                        'diagram': '📐',
                        'file': '📁',
                        'json': '📋',
                        'markdown': '📝'
                    };
                    const icon = typeIcons[artifact.type] || '📦';
                    const typeColors = {
                        'code': 'var(--brand-500)',
                        'document': 'var(--terracotta-500)',
                        'data': 'var(--sand-700)',
                        'diagram': '#8b5cf6',
                        'file': 'var(--sand-600)',
                        'json': '#10b981',
                        'markdown': '#f59e0b'
                    };
                    const color = typeColors[artifact.type] || 'var(--sand-600)';
                    return `
                    <div class="artifact-card" style="background: var(--sand-100); border: 1px solid var(--sand-300); border-radius: 8px; padding: 12px;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 1.5em;">${icon}</span>
                                <div>
                                    <div style="font-weight: 600; color: var(--sand-900);">${escapeHtml(artifact.name)}</div>
                                    <div style="font-size: 0.85em; color: ${color};">${artifact.type}${artifact.language ? ` (${artifact.language})` : ''}</div>
                                </div>
                            </div>
                        </div>
                        ${artifact.description ? `<div style="font-size: 0.9em; color: var(--sand-700); margin-bottom: 8px;">${escapeHtml(artifact.description)}</div>` : ''}
                        <div style="background: var(--sand-50); border-radius: 4px; padding: 8px; max-height: 150px; overflow-y: auto; font-family: monospace; font-size: 0.85em; color: var(--sand-800);">
                            ${escapeHtml(artifact.content.substring(0, 300))}${artifact.content.length > 300 ? '...' : ''}
                        </div>
                        <div style="margin-top: 8px; font-size: 0.8em; color: var(--sand-600);">
                            Created: ${formatTime(artifact.created_at)}
                        </div>
                    </div>
                `;
                }).join('') : '<div class="empty-state"><p>No artifacts yet</p></div>'}
            </div>
        </div>

        <div class="detail-section">
            <h3>Messages (${messages.length})</h3>
            <div class="message-list">
                ${messages.length > 0 ? messages.map(msg => `
                    <div class="message ${msg.role}">
                        <div class="message-header">
                            <span class="message-role">${msg.role}</span>
                            <span class="message-time">${formatTime(msg.timestamp)}</span>
                        </div>
                        <div class="message-content">${escapeHtml(msg.content.substring(0, 500))}${msg.content.length > 500 ? '...' : ''}</div>
                    </div>
                `).join('') : '<div class="empty-state"><p>No messages yet</p></div>'}
            </div>
        </div>

        ${agent.output ? `
            <div class="detail-section">
                <h3>Output</h3>
                <div class="detail-info-item">
                    <span class="detail-info-value" style="white-space: pre-wrap;">${escapeHtml(agent.output)}</span>
                </div>
            </div>
        ` : ''}

        <div class="detail-actions">
            ${agent.status === 'running' || agent.status === 'stuck' ? `
                <button class="btn btn-primary" onclick="openInstructionModal('${agent.id}')">
                    💬 Send Instruction
                </button>
                <button class="btn btn-danger" onclick="confirmCancelAgent('${agent.id}')">
                    ⏹️ Cancel
                </button>
            ` : ''}
            <button class="btn btn-secondary" onclick="confirmDeleteAgent('${agent.id}')">
                🗑️ Delete
            </button>
        </div>
    `;
}

function openDetailPanel() {
    elements.detailPanel.classList.add('open');
    document.querySelector('.main-content').classList.add('detail-open');
}

function closeDetailPanel() {
    elements.detailPanel.classList.remove('open');
    document.querySelector('.main-content').classList.remove('detail-open');
    state.selectedAgentId = null;
    renderAgentList();
}

function updateStats() {
    const agents = Array.from(state.agents.values());

    elements.statRunning.textContent = agents.filter(a => a.status === 'running').length;
    elements.statStuck.textContent = agents.filter(a => a.status === 'stuck').length;
    elements.statCompleted.textContent = agents.filter(a => a.status === 'completed').length;
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString();
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showNotification(message, type = 'info') {
    // Simple console notification for now
    // Could be enhanced with a toast UI component
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Modal Functions
function openModal(modalId) {
    document.getElementById(modalId).classList.add('open');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('open');
}

function openInstructionModal(agentId) {
    document.getElementById('instruction-form').dataset.agentId = agentId;
    openModal('instruction-modal');
}

function confirmCancelAgent(agentId) {
    if (confirm('Are you sure you want to cancel this agent?')) {
        cancelAgent(agentId);
    }
}

function confirmDeleteAgent(agentId) {
    if (confirm('Are you sure you want to delete this agent?')) {
        deleteAgent(agentId);
    }
}

// Event Listeners
elements.createAgentBtn.addEventListener('click', () => {
    openModal('create-agent-modal');
});

elements.createAgentForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const task = document.getElementById('task-input').value;
    const workingDir = document.getElementById('working-dir-input').value;
    const model = document.getElementById('model-input').value;
    const role = document.getElementById('role-input').value;
    const tagsInput = document.getElementById('tags-input').value;
    const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()) : [];

    // Close modal immediately for better UX
    closeModal('create-agent-modal');
    elements.createAgentForm.reset();

    try {
        await createAgent(task, workingDir, model, role, tags);
    } catch (error) {
        // Error already handled in createAgent
    }
});

elements.instructionForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const agentId = e.target.dataset.agentId;
    const instruction = document.getElementById('instruction-input').value;

    await sendInstruction(agentId, instruction);
    closeModal('instruction-modal');
    elements.instructionForm.reset();
});

elements.closeDetailBtn.addEventListener('click', closeDetailPanel);

elements.refreshBtn.addEventListener('click', fetchAgents);

elements.clearCompletedBtn.addEventListener('click', async () => {
    if (!confirm('Delete all completed agents?')) return;

    const completedAgents = Array.from(state.agents.values())
        .filter(a => a.status === 'completed');

    for (const agent of completedAgents) {
        await deleteAgent(agent.id);
    }
});

// Modal close buttons
document.getElementById('modal-close-btn').addEventListener('click', () => {
    closeModal('create-agent-modal');
});

document.getElementById('modal-cancel-btn').addEventListener('click', () => {
    closeModal('create-agent-modal');
});

document.getElementById('instruction-modal-close-btn').addEventListener('click', () => {
    closeModal('instruction-modal');
});

document.getElementById('instruction-modal-cancel-btn').addEventListener('click', () => {
    closeModal('instruction-modal');
});

// Status filters
document.querySelectorAll('.status-filter').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            state.statusFilters.add(e.target.value);
        } else {
            state.statusFilters.delete(e.target.value);
        }
        renderAgentList();
    });
});

// Close modals on background click
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('open');
        }
    });
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadRoles();
    connectWebSocket();
    fetchAgents();

    // Refresh agents every 10 seconds
    setInterval(fetchAgents, 10000);
});

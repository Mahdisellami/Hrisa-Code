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
    // Pagination
    currentPage: 1,
    pageSize: 50,
    totalPages: 1,
    totalAgents: 0,
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

        case 'agent_stream':
            handleStreamChunk(message.data.agent_id, message.data.chunk);
            break;
    }
}

function handleStreamChunk(agentId, chunk) {
    // If viewing this agent, append chunk to a streaming display
    if (state.selectedAgentId === agentId) {
        let streamContainer = document.getElementById(`stream-${agentId}`);
        if (!streamContainer) {
            // Create streaming container if it doesn't exist
            const detailContent = document.getElementById('detail-content');
            if (detailContent) {
                const streamSection = document.createElement('div');
                streamSection.innerHTML = `
                    <div class="detail-section">
                        <h3>Live Response Stream</h3>
                        <div id="stream-${agentId}" style="background: var(--sand-100); border-radius: 6px; padding: 12px; font-family: monospace; font-size: 0.9em; max-height: 300px; overflow-y: auto; white-space: pre-wrap; color: var(--sand-900);"></div>
                    </div>
                `;
                detailContent.insertBefore(streamSection, detailContent.firstChild);
                streamContainer = document.getElementById(`stream-${agentId}`);
            }
        }

        if (streamContainer) {
            streamContainer.textContent += chunk;
            // Auto-scroll to bottom
            streamContainer.scrollTop = streamContainer.scrollHeight;
        }
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

async function fetchAgents(page = null) {
    try {
        const currentPage = page || state.currentPage;
        const response = await fetch(`${API_BASE}/agents?page=${currentPage}&page_size=${state.pageSize}`);
        if (!response.ok) throw new Error('Failed to fetch agents');
        const data = await response.json();

        // Update pagination state
        state.currentPage = data.page;
        state.totalPages = data.total_pages;
        state.totalAgents = data.total;

        state.agents.clear();
        data.agents.forEach(agent => {
            state.agents.set(agent.id, agent);
        });

        renderAgentList();
        renderPagination();
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

async function fetchAgentState(agentId) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/state`);
        if (!response.ok) throw new Error('Failed to fetch state');
        return await response.json();
    } catch (error) {
        console.error('Error fetching state:', error);
        return { current_state: 'unknown', transitions: [] };
    }
}

async function fetchAgentMemory(agentId) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/memory`);
        if (!response.ok) throw new Error('Failed to fetch memory');
        return await response.json();
    } catch (error) {
        console.error('Error fetching memory:', error);
        return { decisions: [], context: {}, intermediate_outputs: [], state_transitions: [], working_memory: [] };
    }
}

// Rendering Functions
function getRoleInfo(roleId) {
    const role = state.roles.find(r => r.id === roleId);
    return role || { id: 'general', name: 'General', icon: '⚙️', color: '#6b7280' };
}

function renderPagination() {
    const paginationContainer = document.getElementById('pagination-controls');
    if (!paginationContainer) return;

    if (state.totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }

    const maxButtons = 7; // Show max 7 page buttons
    let startPage = Math.max(1, state.currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(state.totalPages, startPage + maxButtons - 1);

    // Adjust start if we're near the end
    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    let paginationHTML = `
        <div style="display: flex; align-items: center; gap: 8px; justify-content: center; padding: 16px;">
            <button
                class="btn btn-secondary btn-small"
                onclick="changePage(${state.currentPage - 1})"
                ${state.currentPage === 1 ? 'disabled' : ''}
                style="padding: 6px 12px;"
            >
                ← Prev
            </button>
            <div style="display: flex; gap: 4px;">
    `;

    if (startPage > 1) {
        paginationHTML += `<button class="btn btn-secondary btn-small" onclick="changePage(1)" style="padding: 6px 10px;">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span style="padding: 6px; color: var(--sand-600);">...</span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const isActive = i === state.currentPage;
        paginationHTML += `
            <button
                class="btn ${isActive ? 'btn-primary' : 'btn-secondary'} btn-small"
                onclick="changePage(${i})"
                ${isActive ? 'disabled' : ''}
                style="padding: 6px 10px; min-width: 36px;"
            >
                ${i}
            </button>
        `;
    }

    if (endPage < state.totalPages) {
        if (endPage < state.totalPages - 1) {
            paginationHTML += `<span style="padding: 6px; color: var(--sand-600);">...</span>`;
        }
        paginationHTML += `<button class="btn btn-secondary btn-small" onclick="changePage(${state.totalPages})" style="padding: 6px 10px;">${state.totalPages}</button>`;
    }

    paginationHTML += `
            </div>
            <button
                class="btn btn-secondary btn-small"
                onclick="changePage(${state.currentPage + 1})"
                ${state.currentPage === state.totalPages ? 'disabled' : ''}
                style="padding: 6px 12px;"
            >
                Next →
            </button>
            <span style="color: var(--sand-600); font-size: 0.85em; margin-left: 12px;">
                Page ${state.currentPage} of ${state.totalPages} (${state.totalAgents} total)
            </span>
        </div>
    `;

    paginationContainer.innerHTML = paginationHTML;
}

async function changePage(page) {
    if (page < 1 || page > state.totalPages) return;
    state.currentPage = page;
    await fetchAgents(page);
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
                <div style="display: flex; gap: 6px; align-items: center;">
                    <div class="agent-status ${agent.status}">${agent.status}</div>
                    ${agent.current_state ? `<div style="background: var(--brand-500); color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.7em; font-weight: 600;">${agent.current_state.substring(0, 3).toUpperCase()}</div>` : ''}
                </div>
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
    const agentState = await fetchAgentState(agentId);
    const agentMemory = await fetchAgentMemory(agentId);
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

        ${agent.parent_agent_id || agent.child_agent_ids.length > 0 ? `
            <div class="detail-section">
                <h3>Workflow Chain</h3>
                ${renderWorkflowTree(agent)}
            </div>
        ` : ''}

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
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3>Artifacts (${artifacts.length})</h3>
                ${artifacts.length > 0 ? `
                    <button class="btn btn-secondary btn-small" onclick="downloadAllArtifacts('${agent.id}')" style="font-size: 0.85em; padding: 6px 12px;">
                        📦 Download All
                    </button>
                ` : ''}
            </div>
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
                            <button
                                onclick="downloadArtifact('${agent.id}', '${artifact.id}')"
                                style="background: var(--brand-500); color: white; border: none; border-radius: 4px; padding: 6px 10px; cursor: pointer; font-size: 0.85em;"
                                title="Download artifact"
                            >
                                ⬇️
                            </button>
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
            <h3>State Machine</h3>
            <div style="background: var(--sand-100); border-radius: 8px; padding: 12px;">
                <div class="detail-info-item" style="margin-bottom: 12px;">
                    <span class="detail-info-label">Current State:</span>
                    <span class="detail-info-value">
                        <span style="background: var(--brand-500); color: white; padding: 4px 12px; border-radius: 16px; display: inline-block; font-weight: 600;">
                            ${agentState.current_state.toUpperCase()}
                        </span>
                    </span>
                </div>

                ${agentState.transitions.length > 0 ? `
                    <div style="margin: 16px 0;">
                        <h4 style="color: var(--sand-700); font-size: 0.9em; margin-bottom: 12px;">State Flow Diagram</h4>
                        ${renderStateFlowDiagram(agentState)}
                    </div>
                ` : ''}

                <div style="margin-top: 12px;">
                    <h4 style="color: var(--sand-700); font-size: 0.9em; margin-bottom: 8px;">State Transitions (${agentState.transitions.length})</h4>
                    <div style="max-height: 200px; overflow-y: auto;">
                        ${agentState.transitions.length > 0 ? agentState.transitions.map(t => `
                            <div style="background: var(--sand-50); border-left: 3px solid var(--brand-500); padding: 8px; margin-bottom: 6px; border-radius: 4px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                    <span style="color: var(--sand-800); font-weight: 600;">
                                        ${t.from_state ? `${t.from_state} →` : ''} ${t.to_state}
                                    </span>
                                    <span style="color: var(--sand-600); font-size: 0.85em;">${formatTime(t.timestamp)}</span>
                                </div>
                                ${t.reason ? `<div style="color: var(--sand-700); font-size: 0.9em;">${escapeHtml(t.reason)}</div>` : ''}
                            </div>
                        `).join('') : '<div class="empty-state"><p>No state transitions yet</p></div>'}
                    </div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h3>Progress & Metrics</h3>
            ${renderProgressMetrics(agent, agentState, logs)}
        </div>

        <div class="detail-section">
            <h3>Memory Timeline</h3>
            ${renderMemoryTimeline(agentMemory, agentState)}
        </div>

        <div class="detail-section">
            <h3>Agent Memory (Detailed)</h3>
            <div style="background: var(--sand-100); border-radius: 8px; padding: 12px;">
                <div style="margin-bottom: 16px;">
                    <h4 style="color: var(--sand-700); font-size: 0.9em; margin-bottom: 8px;">Working Memory (${agentMemory.working_memory.length})</h4>
                    <div style="background: var(--sand-50); border-radius: 4px; padding: 8px; max-height: 150px; overflow-y: auto;">
                        ${agentMemory.working_memory.length > 0 ? agentMemory.working_memory.map(item => `
                            <div style="padding: 4px 0; border-bottom: 1px solid var(--sand-200); color: var(--sand-800);">
                                ${escapeHtml(item)}
                            </div>
                        `).join('') : '<div class="empty-state"><p>No working memory items</p></div>'}
                    </div>
                </div>
                <div style="margin-bottom: 16px;">
                    <h4 style="color: var(--sand-700); font-size: 0.9em; margin-bottom: 8px;">Decisions (${agentMemory.decisions.length})</h4>
                    <div style="max-height: 200px; overflow-y: auto;">
                        ${agentMemory.decisions.length > 0 ? agentMemory.decisions.map(decision => `
                            <div style="background: var(--sand-50); border-left: 3px solid var(--terracotta-500); padding: 8px; margin-bottom: 6px; border-radius: 4px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                    <span style="color: var(--terracotta-600); font-weight: 600;">${decision.type}</span>
                                    <span style="color: var(--sand-600); font-size: 0.85em;">${formatTime(decision.timestamp)}</span>
                                </div>
                                <div style="color: var(--sand-800); margin-bottom: 4px;">${escapeHtml(decision.description)}</div>
                                ${decision.rationale ? `<div style="color: var(--sand-700); font-size: 0.9em; font-style: italic;">${escapeHtml(decision.rationale)}</div>` : ''}
                            </div>
                        `).join('') : '<div class="empty-state"><p>No decisions recorded</p></div>'}
                    </div>
                </div>
                <div style="margin-bottom: 16px;">
                    <h4 style="color: var(--sand-700); font-size: 0.9em; margin-bottom: 8px;">Intermediate Outputs (${agentMemory.intermediate_outputs.length})</h4>
                    <div style="max-height: 200px; overflow-y: auto;">
                        ${agentMemory.intermediate_outputs.length > 0 ? agentMemory.intermediate_outputs.map(output => `
                            <div style="background: var(--sand-50); border-left: 3px solid var(--brand-500); padding: 8px; margin-bottom: 6px; border-radius: 4px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                    <span style="color: var(--brand-600); font-weight: 600;">${output.type}</span>
                                    <span style="color: var(--sand-600); font-size: 0.85em;">${formatTime(output.timestamp)}</span>
                                </div>
                                <div style="background: var(--sand-100); border-radius: 4px; padding: 6px; max-height: 100px; overflow-y: auto; font-family: monospace; font-size: 0.85em; color: var(--sand-800);">
                                    ${escapeHtml(output.content.substring(0, 200))}${output.content.length > 200 ? '...' : ''}
                                </div>
                            </div>
                        `).join('') : '<div class="empty-state"><p>No intermediate outputs</p></div>'}
                    </div>
                </div>
                <div>
                    <h4 style="color: var(--sand-700); font-size: 0.9em; margin-bottom: 8px;">Context</h4>
                    <div style="background: var(--sand-50); border-radius: 4px; padding: 8px; max-height: 150px; overflow-y: auto; font-family: monospace; font-size: 0.85em;">
                        ${Object.keys(agentMemory.context).length > 0 ? `
                            <pre style="margin: 0; color: var(--sand-800);">${JSON.stringify(agentMemory.context, null, 2)}</pre>
                        ` : '<div class="empty-state"><p>No context data</p></div>'}
                    </div>
                </div>
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
            ${agent.status === 'completed' || agent.status === 'failed' ? `
                <button class="btn btn-primary" onclick="openChainModal('${agent.id}')">
                    🔗 Create Follow-up Agent
                </button>
                <button class="btn btn-secondary" onclick="replayAgent('${agent.id}')">
                    🔄 Replay
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

function renderStateFlowDiagram(agentState) {
    const states = agentState.transitions.map(t => t.to_state);
    const currentState = agentState.current_state.toLowerCase();

    return `
        <div style="background: var(--sand-50); border-radius: 6px; padding: 16px; overflow-x: auto;">
            <div style="display: flex; align-items: center; gap: 8px; min-width: max-content;">
                ${states.map((state, index) => {
                    const isCurrent = state === currentState;
                    const stateColor = isCurrent ? 'var(--brand-500)' : 'var(--sand-400)';
                    const textColor = isCurrent ? 'white' : 'var(--sand-700)';
                    const fontSize = isCurrent ? '0.9em' : '0.85em';

                    return `
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="background: ${stateColor}; color: ${textColor}; padding: 8px 12px; border-radius: 6px; font-weight: ${isCurrent ? '600' : '500'}; font-size: ${fontSize}; text-transform: uppercase; min-width: 90px; text-align: center; box-shadow: ${isCurrent ? '0 2px 4px rgba(0,0,0,0.1)' : 'none'};">
                                ${state.replace('_', ' ')}
                            </div>
                            ${index < states.length - 1 ? `
                                <div style="color: var(--sand-400); font-size: 1.2em;">→</div>
                            ` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
}

function renderWorkflowTreeNode(agent, currentAgentId, level = 0) {
    const isCurrent = agent.id === currentAgentId;
    const roleInfo = getRoleInfo(agent.role);
    const statusColor = {
        'running': 'var(--brand-500)',
        'completed': 'var(--success-500)',
        'failed': 'var(--danger-500)',
        'stuck': 'var(--warning-500)',
        'pending': 'var(--sand-400)',
    }[agent.status] || 'var(--sand-400)';

    const indent = level * 32;
    const hasChildren = agent.child_agent_ids && agent.child_agent_ids.length > 0;

    return `
        <div style="margin-left: ${indent}px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 10px; border-radius: 6px; background: ${isCurrent ? 'var(--terracotta-50)' : 'var(--sand-50)'}; border: 2px solid ${isCurrent ? 'var(--terracotta-400)' : 'var(--sand-200)'}; transition: all 0.2s;" onclick="selectAgent('${agent.id}')" onmouseover="this.style.borderColor='var(--brand-400)'" onmouseout="this.style.borderColor='${isCurrent ? 'var(--terracotta-400)' : 'var(--sand-200)'}'">
                ${level > 0 ? `<span style="color: var(--sand-400); margin-right: 4px;">└─</span>` : ''}
                <div style="width: 8px; height: 8px; border-radius: 50%; background: ${statusColor};"></div>
                <span style="color: ${roleInfo.color}; font-size: 1.1em;">${roleInfo.icon}</span>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: var(--sand-800); font-size: 0.9em;">
                        ${agent.id.substring(0, 8)}${isCurrent ? ' (Current)' : ''}
                    </div>
                    <div style="font-size: 0.8em; color: var(--sand-600); margin-top: 2px;">
                        Step ${agent.workflow_step} • ${roleInfo.name} • ${agent.status}
                    </div>
                </div>
                ${hasChildren ? `<span style="color: var(--sand-500); font-size: 0.85em;">${agent.child_agent_ids.length} child${agent.child_agent_ids.length > 1 ? 'ren' : ''}</span>` : ''}
            </div>
            ${hasChildren ? `
                <div style="margin-top: 4px;">
                    ${agent.child_agent_ids.map(childId => {
                        const childAgent = state.agents.get(childId);
                        return childAgent ? renderWorkflowTreeNode(childAgent, currentAgentId, level + 1) : '';
                    }).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

function renderWorkflowTree(agent) {
    // Find the root agent (agent without parent)
    let rootAgent = agent;
    while (rootAgent.parent_agent_id) {
        const parent = state.agents.get(rootAgent.parent_agent_id);
        if (!parent) break;
        rootAgent = parent;
    }

    return `
        <div style="background: var(--sand-50); border-radius: 8px; padding: 16px; overflow-x: auto;">
            <div style="margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--sand-200);">
                <span style="color: var(--sand-700); font-weight: 600; font-size: 0.9em;">Workflow Execution Tree</span>
            </div>
            ${renderWorkflowTreeNode(rootAgent, agent.id, 0)}
        </div>
    `;
}

// Timeline state for pagination
const timelineState = {
    items: [],
    displayCount: 20,
    filter: 'all', // 'all', 'decision', 'output', 'state'
};

function renderMemoryTimeline(agentMemory, agentState) {
    // Combine all memory items into a single timeline
    const allItems = [];

    // Add decisions
    agentMemory.decisions.forEach(decision => {
        allItems.push({
            timestamp: new Date(decision.timestamp),
            type: 'decision',
            icon: '🎯',
            color: 'var(--terracotta-500)',
            bgColor: 'var(--terracotta-50)',
            title: decision.type || 'Decision',
            content: decision.description,
            details: decision.rationale,
        });
    });

    // Add intermediate outputs
    agentMemory.intermediate_outputs.forEach(output => {
        allItems.push({
            timestamp: new Date(output.timestamp),
            type: 'output',
            icon: '📤',
            color: 'var(--brand-500)',
            bgColor: 'var(--brand-50)',
            title: output.type || 'Output',
            content: output.content.substring(0, 150),
            details: output.content.length > 150 ? `...${output.content.length} chars total` : null,
        });
    });

    // Add state transitions
    agentState.transitions.forEach(transition => {
        allItems.push({
            timestamp: new Date(transition.timestamp),
            type: 'state',
            icon: '🔄',
            color: 'var(--purple-500)',
            bgColor: 'var(--purple-50)',
            title: 'State Change',
            content: `${transition.from_state || 'start'} → ${transition.to_state}`,
            details: transition.reason,
        });
    });

    // Sort by timestamp (newest first)
    allItems.sort((a, b) => b.timestamp - a.timestamp);

    // Store in state
    timelineState.items = allItems;

    if (allItems.length === 0) {
        return '<div class="empty-state"><p>No timeline data available</p></div>';
    }

    // Apply filter
    const filteredItems = timelineState.filter === 'all'
        ? allItems
        : allItems.filter(item => item.type === timelineState.filter);

    // Limit to displayCount
    const displayedItems = filteredItems.slice(0, timelineState.displayCount);
    const hasMore = filteredItems.length > timelineState.displayCount;

    return `
        <div style="background: var(--sand-50); border-radius: 8px; padding: 16px; max-height: 500px; overflow-y: auto;" id="memory-timeline-container">
            <!-- Header with filters -->
            <div style="margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--sand-200); position: sticky; top: 0; background: var(--sand-50); z-index: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="color: var(--sand-700); font-weight: 600; font-size: 0.9em;">
                        Memory Timeline (${filteredItems.length} ${timelineState.filter === 'all' ? 'events' : timelineState.filter + 's'})
                    </span>
                    <div style="display: flex; gap: 4px;">
                        <button
                            class="btn btn-small ${timelineState.filter === 'all' ? 'btn-primary' : 'btn-secondary'}"
                            onclick="filterTimeline('all')"
                            style="padding: 4px 8px; font-size: 0.8em;"
                        >
                            All
                        </button>
                        <button
                            class="btn btn-small ${timelineState.filter === 'decision' ? 'btn-primary' : 'btn-secondary'}"
                            onclick="filterTimeline('decision')"
                            style="padding: 4px 8px; font-size: 0.8em;"
                        >
                            🎯 Decisions
                        </button>
                        <button
                            class="btn btn-small ${timelineState.filter === 'output' ? 'btn-primary' : 'btn-secondary'}"
                            onclick="filterTimeline('output')"
                            style="padding: 4px 8px; font-size: 0.8em;"
                        >
                            📤 Outputs
                        </button>
                        <button
                            class="btn btn-small ${timelineState.filter === 'state' ? 'btn-primary' : 'btn-secondary'}"
                            onclick="filterTimeline('state')"
                            style="padding: 4px 8px; font-size: 0.8em;"
                        >
                            🔄 States
                        </button>
                    </div>
                </div>
            </div>

            <div style="position: relative; padding-left: 32px;" id="timeline-items-container">
                <!-- Timeline line -->
                <div style="position: absolute; left: 16px; top: 0; bottom: 0; width: 2px; background: var(--sand-300);"></div>

                ${displayedItems.map((item, index) => renderTimelineItem(item)).join('')}

                ${hasMore ? `
                    <div style="text-align: center; margin-top: 16px;">
                        <button
                            class="btn btn-secondary btn-small"
                            onclick="loadMoreTimelineItems()"
                            style="padding: 8px 16px;"
                        >
                            Load More (${filteredItems.length - timelineState.displayCount} remaining)
                        </button>
                    </div>
                ` : ''}

                ${!hasMore && displayedItems.length > 0 ? `
                    <div style="text-align: center; margin-top: 16px; color: var(--sand-600); font-size: 0.85em;">
                        — End of timeline —
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

function renderTimelineItem(item) {
    return `
        <div style="position: relative; margin-bottom: 20px;">
            <!-- Timeline dot -->
            <div style="position: absolute; left: -24px; width: 16px; height: 16px; border-radius: 50%; background: ${item.color}; border: 3px solid var(--sand-50); z-index: 2;"></div>

            <!-- Timeline card -->
            <div style="background: ${item.bgColor}; border-left: 3px solid ${item.color}; border-radius: 6px; padding: 12px; transition: transform 0.2s;" onmouseover="this.style.transform='translateX(4px)'" onmouseout="this.style.transform='translateX(0)'">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="font-size: 1.2em;">${item.icon}</span>
                        <span style="color: ${item.color}; font-weight: 600; font-size: 0.9em;">${item.title}</span>
                    </div>
                    <span style="color: var(--sand-600); font-size: 0.75em;">${formatTime(item.timestamp.toISOString())}</span>
                </div>
                <div style="color: var(--sand-800); font-size: 0.9em; line-height: 1.4;">
                    ${escapeHtml(item.content)}
                </div>
                ${item.details ? `
                    <div style="color: var(--sand-600); font-size: 0.8em; margin-top: 6px; font-style: italic; border-top: 1px solid ${item.color}40; padding-top: 6px;">
                        ${escapeHtml(item.details)}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

function filterTimeline(filter) {
    timelineState.filter = filter;
    timelineState.displayCount = 20; // Reset display count on filter change
    // Re-render the timeline
    const selectedAgent = state.agents.get(state.selectedAgentId);
    if (selectedAgent) {
        renderAgentDetail(state.selectedAgentId);
    }
}

function loadMoreTimelineItems() {
    timelineState.displayCount += 20;
    // Re-render the timeline
    const selectedAgent = state.agents.get(state.selectedAgentId);
    if (selectedAgent) {
        renderAgentDetail(state.selectedAgentId);
    }
}

function renderProgressMetrics(agent, agentState, logs) {
    const stateDistribution = {};
    agentState.transitions.forEach(t => {
        stateDistribution[t.to_state] = (stateDistribution[t.to_state] || 0) + 1;
    });

    const totalTransitions = agentState.transitions.length;
    const stateColors = {
        'initializing': 'var(--sand-400)',
        'planning': 'var(--brand-400)',
        'executing': 'var(--brand-500)',
        'thinking': 'var(--purple-400)',
        'tool_use': 'var(--terracotta-500)',
        'reflecting': 'var(--purple-500)',
        'paused': 'var(--warning-500)',
        'waiting_approval': 'var(--warning-400)',
        'finalizing': 'var(--success-500)',
    };

    // Count tool calls from logs
    const toolCalls = logs.filter(log => log.event_type === 'tool_call').length;
    const toolResults = logs.filter(log => log.event_type === 'tool_result').length;
    const errors = logs.filter(log => log.event_type === 'error').length;
    const warnings = logs.filter(log => log.event_type === 'warning').length;

    // Calculate execution time
    const createdAt = new Date(agent.created_at);
    const now = new Date();
    const elapsedSeconds = Math.floor((now - createdAt) / 1000);
    const elapsedMinutes = Math.floor(elapsedSeconds / 60);
    const elapsedHours = Math.floor(elapsedMinutes / 60);

    return `
        <div style="background: var(--sand-50); border-radius: 8px; padding: 16px;">
            <div style="margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--sand-200);">
                <span style="color: var(--sand-700); font-weight: 600; font-size: 0.9em;">Progress Metrics</span>
            </div>

            <!-- State Distribution Bar Chart -->
            <div style="margin-bottom: 20px;">
                <div style="color: var(--sand-600); font-size: 0.85em; margin-bottom: 8px; font-weight: 500;">State Distribution</div>
                <div style="display: flex; height: 24px; border-radius: 6px; overflow: hidden; background: var(--sand-200);">
                    ${Object.entries(stateDistribution).map(([state, count]) => {
                        const percentage = (count / totalTransitions) * 100;
                        return `<div style="background: ${stateColors[state] || 'var(--sand-400)'}; width: ${percentage}%; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.7em; font-weight: 600;" title="${state}: ${count} times (${percentage.toFixed(1)}%)">${percentage >= 15 ? count : ''}</div>`;
                    }).join('')}
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px;">
                    ${Object.entries(stateDistribution).map(([state, count]) => {
                        return `<div style="display: flex; align-items: center; gap: 4px; font-size: 0.75em;">
                            <div style="width: 12px; height: 12px; border-radius: 2px; background: ${stateColors[state] || 'var(--sand-400)'}"></div>
                            <span style="color: var(--sand-700);">${state.replace('_', ' ')}: ${count}</span>
                        </div>`;
                    }).join('')}
                </div>
            </div>

            <!-- Activity Metrics Grid -->
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px;">
                <div style="background: var(--sand-100); border-radius: 6px; padding: 12px; border-left: 3px solid var(--terracotta-500);">
                    <div style="color: var(--sand-600); font-size: 0.75em; margin-bottom: 4px;">Tool Calls</div>
                    <div style="color: var(--sand-800); font-size: 1.5em; font-weight: 600;">${toolCalls}</div>
                </div>
                <div style="background: var(--sand-100); border-radius: 6px; padding: 12px; border-left: 3px solid var(--success-500);">
                    <div style="color: var(--sand-600); font-size: 0.75em; margin-bottom: 4px;">Tool Results</div>
                    <div style="color: var(--sand-800); font-size: 1.5em; font-weight: 600;">${toolResults}</div>
                </div>
                <div style="background: var(--sand-100); border-radius: 6px; padding: 12px; border-left: 3px solid var(--danger-500);">
                    <div style="color: var(--sand-600); font-size: 0.75em; margin-bottom: 4px;">Errors</div>
                    <div style="color: var(--sand-800); font-size: 1.5em; font-weight: 600;">${errors}</div>
                </div>
                <div style="background: var(--sand-100); border-radius: 6px; padding: 12px; border-left: 3px solid var(--warning-500);">
                    <div style="color: var(--sand-600); font-size: 0.75em; margin-bottom: 4px;">Warnings</div>
                    <div style="color: var(--sand-800); font-size: 1.5em; font-weight: 600;">${warnings}</div>
                </div>
            </div>

            <!-- Execution Time -->
            <div style="background: var(--brand-50); border-radius: 6px; padding: 12px;">
                <div style="color: var(--brand-700); font-size: 0.75em; margin-bottom: 4px;">Total Execution Time</div>
                <div style="color: var(--brand-900); font-size: 1.3em; font-weight: 600;">
                    ${elapsedHours > 0 ? `${elapsedHours}h ` : ''}${elapsedMinutes % 60}m ${elapsedSeconds % 60}s
                </div>
                <div style="color: var(--brand-600); font-size: 0.7em; margin-top: 4px;">
                    Started: ${formatDate(agent.created_at)}
                </div>
            </div>

            <!-- State Transitions Count -->
            <div style="margin-top: 12px; padding: 10px; background: var(--sand-100); border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: var(--sand-700); font-size: 0.85em;">Total State Transitions:</span>
                <span style="color: var(--sand-900); font-weight: 600; font-size: 1.1em;">${totalTransitions}</span>
            </div>
        </div>
    `;
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

function openChainModal(agentId) {
    const agent = state.agents.get(agentId);
    if (!agent) return;

    document.getElementById('chain-agent-form').dataset.parentAgentId = agentId;

    // Populate role dropdown with options
    const roleSelect = document.getElementById('chain-role-input');
    roleSelect.innerHTML = '<option value="">Inherit from parent</option>' +
        state.roles.map(role => `<option value="${role.id}">${role.icon} ${role.name}</option>`).join('');

    // Suggest a follow-up task based on parent's role and status
    const taskInput = document.getElementById('chain-task-input');
    if (agent.status === 'completed') {
        taskInput.placeholder = `Example: Now ${getSuggestedFollowUpTask(agent.role)}`;
    } else if (agent.status === 'failed') {
        taskInput.placeholder = `Example: Fix the issues and retry the task`;
    }

    openModal('chain-agent-modal');
}

function getSuggestedFollowUpTask(role) {
    const suggestions = {
        'requirements_engineer': 'create the architecture design based on these requirements',
        'architect': 'implement the solution following this architecture',
        'coder': 'write comprehensive unit tests for this code',
        'tester': 'review the test coverage and identify any gaps',
        'reviewer': 'implement the suggested improvements',
        'devops': 'create monitoring and alerting for this deployment',
        'general': 'create tests for this code'
    };
    return suggestions[role] || 'continue with the next step';
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

document.getElementById('chain-agent-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const parentAgentId = e.target.dataset.parentAgentId;
    const task = document.getElementById('chain-task-input').value;
    const role = document.getElementById('chain-role-input').value || null;
    const autoStart = document.getElementById('chain-auto-start-input').checked;

    try {
        const response = await fetch(`${API_BASE}/agents/${parentAgentId}/chain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task,
                role,
                auto_start: autoStart,
            }),
        });

        if (!response.ok) throw new Error('Failed to create chained agent');

        const childAgent = await response.json();

        closeModal('chain-agent-modal');
        e.target.reset();

        // Refresh agents and select the new child agent
        await fetchAgents();
        selectAgent(childAgent.id);

        showNotification(`Follow-up agent created successfully! ${autoStart ? '(Will auto-start when parent completes)' : ''}`, 'success');

    } catch (error) {
        console.error('Error creating chained agent:', error);
        showNotification('Failed to create chained agent', 'error');
    }
});

// Session Management Event Listeners
document.getElementById('save-session-btn').addEventListener('click', () => {
    openModal('save-session-modal');
});

document.getElementById('load-session-btn').addEventListener('click', async () => {
    await loadSessionsList();
    openModal('load-session-modal');
});

document.getElementById('save-session-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('session-name-input').value;
    const description = document.getElementById('session-description-input').value || null;

    try {
        const response = await fetch(`${API_BASE}/sessions/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description }),
        });

        if (!response.ok) throw new Error('Failed to save session');

        const session = await response.json();

        closeModal('save-session-modal');
        e.target.reset();

        showNotification(`Session "${session.name}" saved successfully!`, 'success');

    } catch (error) {
        console.error('Error saving session:', error);
        showNotification('Failed to save session', 'error');
    }
});

document.getElementById('save-session-modal-close-btn').addEventListener('click', () => {
    closeModal('save-session-modal');
});

document.getElementById('save-session-modal-cancel-btn').addEventListener('click', () => {
    closeModal('save-session-modal');
});

document.getElementById('load-session-modal-close-btn').addEventListener('click', () => {
    closeModal('load-session-modal');
});

async function loadSessionsList() {
    const sessionsListDiv = document.getElementById('sessions-list');
    sessionsListDiv.innerHTML = '<p style="color: var(--sand-600); text-align: center;">Loading sessions...</p>';

    try {
        const response = await fetch(`${API_BASE}/sessions`);
        if (!response.ok) throw new Error('Failed to load sessions');

        const sessions = await response.json();

        if (sessions.length === 0) {
            sessionsListDiv.innerHTML = '<div class="empty-state"><p>No saved sessions yet</p></div>';
            return;
        }

        sessionsListDiv.innerHTML = sessions.map(session => `
            <div style="background: var(--sand-100); border: 1px solid var(--sand-300); border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                    <div>
                        <h4 style="color: var(--sand-900); margin: 0 0 4px 0;">${escapeHtml(session.name)}</h4>
                        ${session.description ? `<p style="color: var(--sand-600); font-size: 0.9em; margin: 4px 0;">${escapeHtml(session.description)}</p>` : ''}
                        <div style="color: var(--sand-600); font-size: 0.85em; margin-top: 8px;">
                            ${session.agent_count} agent${session.agent_count !== 1 ? 's' : ''} • ${session.total_artifacts} artifact${session.total_artifacts !== 1 ? 's' : ''}<br>
                            Saved: ${formatDate(session.created_at)}
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button
                            onclick="loadSession('${session.id}')"
                            class="btn btn-primary btn-small"
                            style="font-size: 0.85em; padding: 6px 12px;"
                        >
                            📂 Load
                        </button>
                        <button
                            onclick="deleteSession('${session.id}')"
                            class="btn btn-secondary btn-small"
                            style="font-size: 0.85em; padding: 6px 12px;"
                        >
                            🗑️
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading sessions:', error);
        sessionsListDiv.innerHTML = '<div class="empty-state"><p style="color: var(--danger-500);">Failed to load sessions</p></div>';
    }
}

async function loadSession(sessionId) {
    if (!confirm('Loading this session will replace all current agents. Continue?')) return;

    try {
        const response = await fetch(`${API_BASE}/sessions/${sessionId}/load`, {
            method: 'POST',
        });

        if (!response.ok) throw new Error('Failed to load session');

        closeModal('load-session-modal');
        await fetchAgents();

        showNotification('Session loaded successfully!', 'success');

    } catch (error) {
        console.error('Error loading session:', error);
        showNotification('Failed to load session', 'error');
    }
}

async function deleteSession(sessionId) {
    if (!confirm('Are you sure you want to delete this session?')) return;

    try {
        const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
            method: 'DELETE',
        });

        if (!response.ok) throw new Error('Failed to delete session');

        await loadSessionsList();

        showNotification('Session deleted successfully!', 'success');

    } catch (error) {
        console.error('Error deleting session:', error);
        showNotification('Failed to delete session', 'error');
    }
}

async function replayAgent(agentId) {
    if (!confirm('This will create a new agent with the same task and start it. Continue?')) return;

    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/replay`, {
            method: 'POST',
        });

        if (!response.ok) throw new Error('Failed to replay agent');

        const result = await response.json();

        await fetchAgents();
        selectAgent(result.new_agent_id);

        showNotification(`Agent replayed! New agent started.`, 'success');

    } catch (error) {
        console.error('Error replaying agent:', error);
        showNotification('Failed to replay agent', 'error');
    }
}

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

document.getElementById('chain-modal-close-btn').addEventListener('click', () => {
    closeModal('chain-agent-modal');
});

document.getElementById('chain-modal-cancel-btn').addEventListener('click', () => {
    closeModal('chain-agent-modal');
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

// Artifact Download Functions
function downloadArtifact(agentId, artifactId) {
    const url = `${API_BASE}/agents/${agentId}/artifacts/${artifactId}/download`;
    window.open(url, '_blank');
}

function downloadAllArtifacts(agentId) {
    const url = `${API_BASE}/agents/${agentId}/artifacts/download-all`;
    window.open(url, '_blank');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadRoles();
    connectWebSocket();
    fetchAgents();

    // Refresh agents every 10 seconds
    setInterval(fetchAgents, 10000);
});

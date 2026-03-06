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
    // Teams
    teams: [],
    selectedTeamId: null,
    viewMode: 'agents', // 'agents' or 'teams'
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

// Toast Notification System
const toastQueue = [];
let toastIdCounter = 0;

function showToast(message, type = 'info', title = null, duration = 4000) {
    const toastId = `toast-${toastIdCounter++}`;
    const container = document.getElementById('toast-container');

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const titles = {
        success: title || 'Success',
        error: title || 'Error',
        warning: title || 'Warning',
        info: title || 'Info'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.id = toastId;
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-title">${titles[type]}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="closeToast('${toastId}')" aria-label="Close">✕</button>
    `;

    container.appendChild(toast);
    toastQueue.push(toastId);

    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            closeToast(toastId);
        }, duration);
    }

    return toastId;
}

function closeToast(toastId) {
    const toast = document.getElementById(toastId);
    if (!toast) return;

    toast.classList.add('removing');
    setTimeout(() => {
        toast.remove();
        const index = toastQueue.indexOf(toastId);
        if (index > -1) {
            toastQueue.splice(index, 1);
        }
    }, 200);
}

// Shorthand toast functions
function toastSuccess(message, title = null) {
    return showToast(message, 'success', title);
}

function toastError(message, title = null) {
    return showToast(message, 'error', title);
}

function toastWarning(message, title = null) {
    return showToast(message, 'warning', title);
}

function toastInfo(message, title = null) {
    return showToast(message, 'info', title);
}

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

async function renderInterAgentMessages(agentId) {
    const container = document.getElementById(`inter-agent-messages-${agentId}`);
    if (!container) return;

    const messages = await fetchAgentMessages(agentId);

    if (messages.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No inter-agent messages yet</p></div>';
        return;
    }

    const agentList = Array.from(state.agents.values());
    const getAgentName = (id) => {
        const agent = agentList.find(a => a.id === id);
        return agent ? `${agent.id.substring(0, 8)} (${getRoleInfo(agent.role).name})` : id.substring(0, 8);
    };

    const messageTypeIcons = {
        'request': '📨',
        'response': '📬',
        'notification': '🔔',
        'question': '❓',
    };

    const messageTypeColors = {
        'request': 'var(--brand-500)',
        'response': 'var(--success-500)',
        'notification': 'var(--terracotta-500)',
        'question': 'var(--purple-500)',
    };

    container.innerHTML = `
        <div style="background: var(--sand-50); border-radius: 8px; padding: 16px; max-height: 400px; overflow-y: auto;">
            ${messages.map(msg => {
                const isIncoming = msg.to_agent_id === agentId;
                const icon = messageTypeIcons[msg.message_type] || '💬';
                const color = messageTypeColors[msg.message_type] || 'var(--sand-500)';

                return `
                    <div style="background: ${isIncoming ? 'var(--brand-50)' : 'var(--sand-100)'}; border-left: 3px solid ${color}; border-radius: 6px; padding: 12px; margin-bottom: 12px; ${!msg.read && isIncoming ? 'border: 2px solid var(--brand-400);' : ''}">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                            <div>
                                <span style="font-size: 1.2em; margin-right: 6px;">${icon}</span>
                                <span style="color: ${color}; font-weight: 600; font-size: 0.9em; text-transform: uppercase;">${msg.message_type}</span>
                                ${!msg.read && isIncoming ? '<span style="background: var(--brand-500); color: white; font-size: 0.7em; padding: 2px 6px; border-radius: 10px; margin-left: 8px;">NEW</span>' : ''}
                            </div>
                            <span style="color: var(--sand-600); font-size: 0.75em;">${formatTime(msg.timestamp)}</span>
                        </div>
                        <div style="margin-bottom: 8px;">
                            <span style="color: var(--sand-700); font-size: 0.85em;">
                                ${isIncoming ? '← From' : '→ To'}: <strong>${getAgentName(isIncoming ? msg.from_agent_id : msg.to_agent_id)}</strong>
                            </span>
                        </div>
                        <div style="color: var(--sand-900); line-height: 1.4;">
                            ${escapeHtml(msg.content)}
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
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
                    <div class="badge ${getPriorityBadgeClass(agent.priority)}" style="font-size: 0.7em;">P${agent.priority}</div>
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
            <h3>Priority & Scheduling</h3>
            <div class="detail-info">
                ${renderPriorityControls(agent.id, agent.priority)}
                ${agent.scheduled_start_time ? `
                    <div class="detail-info-item" style="margin-top: 12px;">
                        <span class="detail-info-label">⏰ Scheduled Start:</span>
                        <span class="detail-info-value">${formatDate(agent.scheduled_start_time)}</span>
                    </div>
                ` : ''}
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
            <h3>Inter-Agent Messages</h3>
            <div id="inter-agent-messages-${agent.id}">
                <p style="color: var(--sand-600); text-align: center;">Loading messages...</p>
            </div>
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

        <div class="detail-section">
            <h3>Export Options</h3>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <button class="btn btn-secondary btn-small" onclick="exportAgentData('${agent.id}', 'json')">
                    📄 Export JSON
                </button>
                <button class="btn btn-secondary btn-small" onclick="exportAgentData('${agent.id}', 'markdown')">
                    📝 Export Markdown
                </button>
                <button class="btn btn-secondary btn-small" onclick="exportAgentLogs('${agent.id}')">
                    📋 Export Logs
                </button>
            </div>
        </div>
    `;

    // Load inter-agent messages asynchronously
    renderInterAgentMessages(agentId);
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

// Auto-recommend model when task description changes
document.getElementById('task-input')?.addEventListener('blur', async () => {
    autoRecommendModel();
});

elements.createAgentForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const task = document.getElementById('task-input').value;
    const workingDir = document.getElementById('working-dir-input').value;
    const model = document.getElementById('model-input-select')?.value || document.getElementById('model-input')?.value;
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

document.getElementById('create-team-modal-close-btn')?.addEventListener('click', () => {
    closeModal('create-team-modal');
});

document.getElementById('create-team-modal-cancel-btn')?.addEventListener('click', () => {
    closeModal('create-team-modal');
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

// Team Management Functions
async function fetchTeams() {
    try {
        const response = await fetch(`${API_BASE}/teams`);
        if (response.ok) {
            state.teams = await response.json();
            if (state.viewMode === 'teams') {
                renderTeamList();
            }
        }
    } catch (error) {
        console.error('Failed to fetch teams:', error);
    }
}

async function createTeam(name, description, sharedGoal, leadAgentId, memberAgentIds) {
    try {
        const response = await fetch(`${API_BASE}/teams`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                description,
                shared_goal: sharedGoal,
                lead_agent_id: leadAgentId || null,
                member_agent_ids: memberAgentIds || [],
            }),
        });

        if (response.ok) {
            const team = await response.json();
            await fetchTeams();
            return team;
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create team');
        }
    } catch (error) {
        console.error('Failed to create team:', error);
        throw error;
    }
}

async function getTeamMembers(teamId) {
    try {
        const response = await fetch(`${API_BASE}/teams/${teamId}/members`);
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Failed to fetch team members:', error);
    }
    return null;
}

async function addAgentToTeam(teamId, agentId) {
    try {
        const response = await fetch(`${API_BASE}/teams/${teamId}/members`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ agent_id: agentId }),
        });

        if (response.ok) {
            await fetchTeams();
            await fetchAgents();
            return true;
        }
    } catch (error) {
        console.error('Failed to add agent to team:', error);
    }
    return false;
}

async function removeAgentFromTeam(teamId, agentId) {
    try {
        const response = await fetch(`${API_BASE}/teams/${teamId}/members/${agentId}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            await fetchTeams();
            await fetchAgents();
            return true;
        }
    } catch (error) {
        console.error('Failed to remove agent from team:', error);
    }
    return false;
}

async function disbandTeam(teamId) {
    try {
        const response = await fetch(`${API_BASE}/teams/${teamId}/disband`, {
            method: 'POST',
        });

        if (response.ok) {
            await fetchTeams();
            await fetchAgents();
            return true;
        }
    } catch (error) {
        console.error('Failed to disband team:', error);
    }
    return false;
}

function renderTeamList() {
    const listContainer = document.getElementById('agent-list');

    if (state.teams.length === 0) {
        listContainer.innerHTML = '<div class="empty-state"><p>No teams yet. Create one to get started!</p></div>';
        return;
    }

    const teamCards = state.teams
        .filter(team => team.status === 'active')
        .map(team => {
            const memberCount = team.member_agent_ids.length + (team.lead_agent_id ? 1 : 0);
            return `
                <div class="agent-card" onclick="showTeamDetail('${team.id}')">
                    <div class="agent-card-header">
                        <h3>👥 ${escapeHtml(team.name)}</h3>
                        <span class="badge badge-active">${memberCount} members</span>
                    </div>
                    <div class="agent-card-body">
                        <p class="agent-task">${escapeHtml(team.shared_goal)}</p>
                        <p class="agent-description">${escapeHtml(team.description)}</p>
                    </div>
                    <div class="agent-card-footer">
                        <span class="agent-meta">Created: ${formatDate(team.created_at)}</span>
                    </div>
                </div>
            `;
        }).join('');

    listContainer.innerHTML = teamCards;
}

async function showTeamDetail(teamId) {
    state.selectedTeamId = teamId;
    const team = state.teams.find(t => t.id === teamId);
    if (!team) return;

    const members = await getTeamMembers(teamId);

    let html = `
        <div class="detail-section">
            <h3>👥 Team: ${escapeHtml(team.name)}</h3>
            <p><strong>Goal:</strong> ${escapeHtml(team.shared_goal)}</p>
            <p><strong>Description:</strong> ${escapeHtml(team.description)}</p>
            <p><strong>Status:</strong> <span class="badge badge-${team.status}">${team.status}</span></p>
            <p><strong>Created:</strong> ${formatDate(team.created_at)}</p>
        </div>

        <div class="detail-section">
            <h3>Team Members (${members.total_members})</h3>
    `;

    if (members.lead) {
        html += `
            <div class="team-member">
                <div class="team-member-header">
                    <strong>👑 Team Lead</strong>
                </div>
                <div class="agent-card mini" onclick="showAgentDetailFromTeam('${members.lead.id}')">
                    <div class="agent-card-header">
                        <h4>${escapeHtml(members.lead.task)}</h4>
                        <span class="badge badge-${members.lead.status}">${members.lead.status}</span>
                    </div>
                    <p class="agent-meta">Role: ${members.lead.role || 'general'}</p>
                </div>
            </div>
        `;
    }

    if (members.members && members.members.length > 0) {
        html += '<div class="team-member-header"><strong>Team Members</strong></div>';
        members.members.forEach(agent => {
            html += `
                <div class="agent-card mini" onclick="showAgentDetailFromTeam('${agent.id}')">
                    <div class="agent-card-header">
                        <h4>${escapeHtml(agent.task)}</h4>
                        <span class="badge badge-${agent.status}">${agent.status}</span>
                    </div>
                    <p class="agent-meta">Role: ${agent.role || 'general'}</p>
                    <button class="btn btn-danger btn-small" onclick="event.stopPropagation(); removeTeamMember('${teamId}', '${agent.id}')">Remove</button>
                </div>
            `;
        });
    }

    html += `
        </div>
        <div class="detail-actions">
            <button class="btn btn-secondary" onclick="switchToAgentsView()">Back to Agents</button>
            <button class="btn btn-danger" onclick="confirmDisbandTeam('${teamId}')">Disband Team</button>
        </div>
    `;

    elements.detailContent.innerHTML = html;
    elements.detailPanel.classList.add('open');
}

function showAgentDetailFromTeam(agentId) {
    state.viewMode = 'agents';
    renderAgentList();
    selectAgent(agentId);
}

async function removeTeamMember(teamId, agentId) {
    if (confirm('Remove this agent from the team?')) {
        const success = await removeAgentFromTeam(teamId, agentId);
        if (success) {
            showTeamDetail(teamId);
        }
    }
}

async function confirmDisbandTeam(teamId) {
    if (confirm('Are you sure you want to disband this team? This action cannot be undone.')) {
        const success = await disbandTeam(teamId);
        if (success) {
            elements.detailPanel.classList.remove('open');
            switchToTeamsView();
        }
    }
}

function switchToTeamsView() {
    state.viewMode = 'teams';
    document.getElementById('view-agents-btn').classList.remove('active');
    document.getElementById('view-teams-btn').classList.add('active');
    document.getElementById('create-agent-btn').style.display = 'none';
    document.getElementById('create-team-btn').style.display = 'block';
    renderTeamList();
}

function switchToAgentsView() {
    state.viewMode = 'agents';
    document.getElementById('view-teams-btn').classList.remove('active');
    document.getElementById('view-agents-btn').classList.add('active');
    document.getElementById('create-team-btn').style.display = 'none';
    document.getElementById('create-agent-btn').style.display = 'block';
    renderAgentList();
}

// Advanced Visualization Functions
async function showPerformanceCharts() {
    const listContainer = document.getElementById('agent-list');
    const agents = Array.from(state.agents.values());

    if (agents.length === 0) {
        listContainer.innerHTML = '<div class="empty-state"><p>No performance data to display</p></div>';
        return;
    }

    // Prepare data for charts
    const now = Date.now();
    const last24h = now - (24 * 60 * 60 * 1000);
    const last7d = now - (7 * 24 * 60 * 60 * 1000);

    // Group agents by creation time (hourly buckets for last 24h)
    const hourlyBuckets = {};
    for (let i = 0; i < 24; i++) {
        const bucketTime = last24h + (i * 60 * 60 * 1000);
        hourlyBuckets[bucketTime] = { created: 0, completed: 0, failed: 0, active: 0 };
    }

    agents.forEach(agent => {
        const createdTime = new Date(agent.created_at).getTime();
        if (createdTime >= last24h) {
            const bucketKey = Math.floor((createdTime - last24h) / (60 * 60 * 1000)) * (60 * 60 * 1000) + last24h;
            if (hourlyBuckets[bucketKey]) {
                hourlyBuckets[bucketKey].created++;
                if (agent.status === 'completed') hourlyBuckets[bucketKey].completed++;
                if (agent.status === 'failed') hourlyBuckets[bucketKey].failed++;
                if (agent.status === 'running') hourlyBuckets[bucketKey].active++;
            }
        }
    });

    // Calculate success rates
    const successRates = Object.keys(hourlyBuckets).map(key => {
        const bucket = hourlyBuckets[key];
        const total = bucket.completed + bucket.failed;
        return {
            time: parseInt(key),
            rate: total > 0 ? (bucket.completed / total) * 100 : 0,
            total: total,
        };
    });

    // Average response times (mock data based on model metrics)
    const modelMetrics = await fetchAllModelMetrics();
    const avgResponseTime = modelMetrics.length > 0
        ? modelMetrics.reduce((sum, m) => sum + m.average_response_time, 0) / modelMetrics.length
        : 0;

    const chartsHTML = `
        <div style="padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0;">Performance Charts</h2>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary btn-small" onclick="switchToAgentsView()">Back to List</button>
                </div>
            </div>

            <!-- Key Metrics Cards -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
                <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 20px; border-radius: 8px; color: white;">
                    <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Total Agents</div>
                    <div style="font-size: 32px; font-weight: 700;">${agents.length}</div>
                </div>
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 20px; border-radius: 8px; color: white;">
                    <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Completed</div>
                    <div style="font-size: 32px; font-weight: 700;">${agents.filter(a => a.status === 'completed').length}</div>
                </div>
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 20px; border-radius: 8px; color: white;">
                    <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Running/Stuck</div>
                    <div style="font-size: 32px; font-weight: 700;">${agents.filter(a => a.status === 'running' || a.status === 'stuck').length}</div>
                </div>
                <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 20px; border-radius: 8px; color: white;">
                    <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Failed</div>
                    <div style="font-size: 32px; font-weight: 700;">${agents.filter(a => a.status === 'failed').length}</div>
                </div>
            </div>

            <!-- Agent Creation Rate Chart -->
            <div style="background: white; border: 1px solid var(--sand-300); border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="margin-top: 0; margin-bottom: 16px;">Agent Creation Rate (Last 24 Hours)</h3>
                <div style="position: relative; height: 200px;">
                    ${renderLineChart(
                        Object.keys(hourlyBuckets).map(k => parseInt(k)),
                        Object.values(hourlyBuckets).map(b => b.created),
                        'chart-creation-rate',
                        '#3b82f6'
                    )}
                </div>
            </div>

            <!-- Success Rate Chart -->
            <div style="background: white; border: 1px solid var(--sand-300); border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="margin-top: 0; margin-bottom: 16px;">Success Rate (Last 24 Hours)</h3>
                <div style="position: relative; height: 200px;">
                    ${renderLineChart(
                        successRates.map(r => r.time),
                        successRates.map(r => r.rate),
                        'chart-success-rate',
                        '#10b981',
                        '%'
                    )}
                </div>
            </div>

            <!-- Status Distribution -->
            <div style="background: white; border: 1px solid var(--sand-300); border-radius: 8px; padding: 20px;">
                <h3 style="margin-top: 0; margin-bottom: 16px;">Status Distribution</h3>
                <div style="position: relative; height: 200px;">
                    ${renderPieChart([
                        { label: 'Running', value: agents.filter(a => a.status === 'running').length, color: 'var(--brand-500)' },
                        { label: 'Completed', value: agents.filter(a => a.status === 'completed').length, color: '#10b981' },
                        { label: 'Stuck', value: agents.filter(a => a.status === 'stuck').length, color: '#f59e0b' },
                        { label: 'Failed', value: agents.filter(a => a.status === 'failed').length, color: '#ef4444' },
                        { label: 'Pending', value: agents.filter(a => a.status === 'pending').length, color: '#6b7280' },
                    ], 'chart-status-distribution')}
                </div>
            </div>

            ${modelMetrics.length > 0 ? `
                <div style="background: white; border: 1px solid var(--sand-300); border-radius: 8px; padding: 20px; margin-top: 20px;">
                    <h3 style="margin-top: 0; margin-bottom: 16px;">Model Performance Comparison</h3>
                    <div style="max-height: 400px; overflow-y: auto;">
                        ${modelMetrics.sort((a, b) => b.success_rate - a.success_rate).map(model => `
                            <div style="margin-bottom: 16px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                    <span style="font-size: 13px; font-weight: 600;">${escapeHtml(model.model_name)}</span>
                                    <span style="font-size: 13px; color: var(--sand-600);">${model.success_rate.toFixed(1)}%</span>
                                </div>
                                <div style="background: var(--sand-200); height: 8px; border-radius: 4px; overflow: hidden;">
                                    <div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); height: 100%; width: ${model.success_rate}%; transition: width 0.3s;"></div>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 11px; color: var(--sand-600);">
                                    <span>${model.total_requests} requests</span>
                                    <span>${model.average_response_time.toFixed(2)}s avg</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;

    listContainer.innerHTML = chartsHTML;
}

function renderLineChart(xValues, yValues, id, color, unit = '') {
    if (xValues.length === 0 || yValues.length === 0) {
        return '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--sand-600);">No data available</div>';
    }

    const width = 800;
    const height = 200;
    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;

    const maxY = Math.max(...yValues, 1);
    const minY = Math.min(...yValues, 0);
    const yRange = maxY - minY || 1;

    // Generate path
    const points = xValues.map((x, i) => {
        const xPos = padding + (i / (xValues.length - 1)) * chartWidth;
        const yPos = height - padding - ((yValues[i] - minY) / yRange) * chartHeight;
        return `${xPos},${yPos}`;
    });

    const pathD = `M ${points.join(' L ')}`;

    return `
        <svg width="100%" height="200" viewBox="0 0 ${width} ${height}">
            <!-- Grid lines -->
            ${[0, 0.25, 0.5, 0.75, 1].map(ratio => {
                const y = height - padding - (ratio * chartHeight);
                const value = (minY + ratio * yRange).toFixed(1);
                return `
                    <line x1="${padding}" y1="${y}" x2="${width - padding}" y2="${y}" stroke="var(--sand-300)" stroke-width="1" stroke-dasharray="4,4" />
                    <text x="${padding - 5}" y="${y + 4}" text-anchor="end" font-size="10" fill="var(--sand-600)">${value}${unit}</text>
                `;
            }).join('')}

            <!-- Line -->
            <path d="${pathD}" fill="none" stroke="${color}" stroke-width="2" />

            <!-- Points -->
            ${points.map((point, i) => {
                const [x, y] = point.split(',');
                return `<circle cx="${x}" cy="${y}" r="3" fill="${color}" />`;
            }).join('')}

            <!-- X-axis labels -->
            ${xValues.map((x, i) => {
                if (i % Math.ceil(xValues.length / 6) !== 0) return '';
                const xPos = padding + (i / (xValues.length - 1)) * chartWidth;
                const time = new Date(x);
                return `<text x="${xPos}" y="${height - 10}" text-anchor="middle" font-size="10" fill="var(--sand-600)">${time.getHours()}:00</text>`;
            }).join('')}
        </svg>
    `;
}

function renderPieChart(data, id) {
    const total = data.reduce((sum, d) => sum + d.value, 0);
    if (total === 0) {
        return '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--sand-600);">No data available</div>';
    }

    const centerX = 150;
    const centerY = 100;
    const radius = 80;

    let currentAngle = -90;
    const slices = data.filter(d => d.value > 0).map(d => {
        const percentage = (d.value / total) * 100;
        const angle = (d.value / total) * 360;
        const startAngle = currentAngle;
        const endAngle = currentAngle + angle;

        const startRad = (startAngle * Math.PI) / 180;
        const endRad = (endAngle * Math.PI) / 180;

        const x1 = centerX + radius * Math.cos(startRad);
        const y1 = centerY + radius * Math.sin(startRad);
        const x2 = centerX + radius * Math.cos(endRad);
        const y2 = centerY + radius * Math.sin(endRad);

        const largeArc = angle > 180 ? 1 : 0;

        currentAngle = endAngle;

        return {
            ...d,
            path: `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`,
            percentage: percentage.toFixed(1),
        };
    });

    return `
        <div style="display: flex; align-items: center; gap: 32px;">
            <svg width="300" height="200" viewBox="0 0 300 200">
                ${slices.map((slice, i) => `
                    <path d="${slice.path}" fill="${slice.color}" stroke="white" stroke-width="2" />
                `).join('')}
            </svg>
            <div style="flex: 1;">
                ${slices.map(slice => `
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <div style="width: 16px; height: 16px; border-radius: 3px; background: ${slice.color};"></div>
                        <span style="font-size: 13px; color: var(--sand-700);">${slice.label}</span>
                        <span style="margin-left: auto; font-weight: 600; color: var(--sand-900);">${slice.value} (${slice.percentage}%)</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

async function showActivityTimeline() {
    const listContainer = document.getElementById('agent-list');
    const agents = Array.from(state.agents.values());

    if (agents.length === 0) {
        listContainer.innerHTML = '<div class="empty-state"><p>No agent activity to display</p></div>';
        return;
    }

    // Collect all activities from all agents
    const activities = [];

    agents.forEach(agent => {
        // Agent creation
        activities.push({
            timestamp: new Date(agent.created_at),
            type: 'agent_created',
            agent_id: agent.id,
            agent_status: agent.status,
            data: { task: agent.task, model: agent.model, role: agent.role },
        });

        // State transitions (if available via memory or stored)
        if (agent.progress.last_activity) {
            activities.push({
                timestamp: new Date(agent.progress.last_activity),
                type: 'activity',
                agent_id: agent.id,
                agent_status: agent.status,
                data: {
                    current_state: agent.current_state,
                    tool_calls: agent.progress.tool_calls,
                    completed_steps: agent.progress.completed_steps,
                },
            });
        }

        // Error events
        if (agent.error) {
            activities.push({
                timestamp: new Date(agent.progress.last_activity || agent.created_at),
                type: 'error',
                agent_id: agent.id,
                agent_status: agent.status,
                data: { error: agent.error },
            });
        }

        // Stuck events
        if (agent.stuck_reason) {
            activities.push({
                timestamp: new Date(agent.progress.last_activity || agent.created_at),
                type: 'stuck',
                agent_id: agent.id,
                agent_status: agent.status,
                data: { reason: agent.stuck_reason },
            });
        }

        // Completion
        if (agent.status === 'completed' || agent.status === 'failed') {
            activities.push({
                timestamp: new Date(agent.progress.last_activity || agent.created_at),
                type: agent.status === 'completed' ? 'agent_completed' : 'agent_failed',
                agent_id: agent.id,
                agent_status: agent.status,
                data: { output: agent.output },
            });
        }
    });

    // Sort by timestamp (newest first)
    activities.sort((a, b) => b.timestamp - a.timestamp);

    // Limit to most recent 100 activities
    const recentActivities = activities.slice(0, 100);

    // Render timeline
    const timelineHTML = `
        <div style="padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0;">Activity Timeline</h2>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary btn-small" onclick="switchToAgentsView()">Back to List</button>
                </div>
            </div>

            <div style="background: var(--sand-100); border: 1px solid var(--sand-300); border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                <div style="display: flex; gap: 24px; font-size: 13px; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="display: inline-block; width: 12px; height: 12px; border-radius: 2px; background: #3b82f6;"></span>
                        <span>Agent Created</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="display: inline-block; width: 12px; height: 12px; border-radius: 2px; background: #10b981;"></span>
                        <span>Completed</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="display: inline-block; width: 12px; height: 12px; border-radius: 2px; background: var(--brand-500);"></span>
                        <span>Activity</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="display: inline-block; width: 12px; height: 12px; border-radius: 2px; background: #f59e0b;"></span>
                        <span>Stuck</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="display: inline-block; width: 12px; height: 12px; border-radius: 2px; background: #ef4444;"></span>
                        <span>Error/Failed</span>
                    </div>
                </div>
            </div>

            <div style="position: relative;">
                <!-- Timeline line -->
                <div style="position: absolute; left: 30px; top: 0; bottom: 0; width: 2px; background: var(--sand-300);"></div>

                <!-- Timeline items -->
                <div style="padding-left: 60px;">
                    ${recentActivities.map((activity, index) => {
                        const typeConfig = {
                            'agent_created': { icon: '✨', color: '#3b82f6', label: 'Agent Created' },
                            'agent_completed': { icon: '✅', color: '#10b981', label: 'Completed' },
                            'agent_failed': { icon: '❌', color: '#ef4444', label: 'Failed' },
                            'activity': { icon: '⚡', color: 'var(--brand-500)', label: 'Activity' },
                            'error': { icon: '🚨', color: '#ef4444', label: 'Error' },
                            'stuck': { icon: '⏸️', color: '#f59e0b', label: 'Stuck' },
                        };
                        const config = typeConfig[activity.type] || { icon: '●', color: '#6b7280', label: 'Event' };

                        return `
                            <div style="position: relative; margin-bottom: 24px;">
                                <!-- Timeline dot -->
                                <div style="position: absolute; left: -44px; top: 4px; width: 24px; height: 24px; border-radius: 50%; background: ${config.color}; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-size: 12px;">
                                    ${config.icon}
                                </div>

                                <!-- Timeline content -->
                                <div style="background: white; border: 1px solid var(--sand-300); border-left: 4px solid ${config.color}; border-radius: 6px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            <span style="font-weight: 600; color: var(--sand-900);">${config.label}</span>
                                            <span style="font-size: 12px; color: var(--sand-600); cursor: pointer;" onclick="selectAgent('${activity.agent_id}')" title="Click to view agent">
                                                Agent: ${activity.agent_id.substring(0, 8)}
                                            </span>
                                        </div>
                                        <span style="font-size: 12px; color: var(--sand-600);">${formatTime(activity.timestamp.toISOString())}</span>
                                    </div>

                                    ${activity.type === 'agent_created' ? `
                                        <div style="font-size: 13px; color: var(--sand-700);">
                                            <strong>Task:</strong> ${escapeHtml(activity.data.task.substring(0, 100))}${activity.data.task.length > 100 ? '...' : ''}
                                        </div>
                                        <div style="font-size: 12px; color: var(--sand-600); margin-top: 4px;">
                                            Model: ${activity.data.model} | Role: ${activity.data.role || 'general'}
                                        </div>
                                    ` : ''}

                                    ${activity.type === 'activity' ? `
                                        <div style="font-size: 13px; color: var(--sand-700);">
                                            State: <strong>${activity.data.current_state}</strong> |
                                            Tool Calls: ${activity.data.tool_calls} |
                                            Steps: ${activity.data.completed_steps}
                                        </div>
                                    ` : ''}

                                    ${activity.type === 'error' ? `
                                        <div style="background: #fef2f2; padding: 8px; border-radius: 4px; font-size: 12px; font-family: monospace; color: #991b1b;">
                                            ${escapeHtml(activity.data.error.substring(0, 200))}${activity.data.error.length > 200 ? '...' : ''}
                                        </div>
                                    ` : ''}

                                    ${activity.type === 'stuck' ? `
                                        <div style="background: #fef3c7; padding: 8px; border-radius: 4px; font-size: 12px; color: #92400e;">
                                            ${escapeHtml(activity.data.reason)}
                                        </div>
                                    ` : ''}

                                    ${activity.type === 'agent_completed' && activity.data.output ? `
                                        <div style="font-size: 13px; color: var(--sand-700);">
                                            ${escapeHtml(activity.data.output.substring(0, 150))}${activity.data.output.length > 150 ? '...' : ''}
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>

                ${recentActivities.length === 100 ? `
                    <div style="text-align: center; padding: 16px; color: var(--sand-600); font-size: 13px;">
                        Showing most recent 100 activities
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    listContainer.innerHTML = timelineHTML;
}

async function showAgentNetworkGraph() {
    const listContainer = document.getElementById('agent-list');

    const agents = Array.from(state.agents.values());
    const teams = state.teams;

    if (agents.length === 0) {
        listContainer.innerHTML = '<div class="empty-state"><p>No agents to visualize</p></div>';
        return;
    }

    // Create graph visualization
    const graphHTML = `
        <div style="padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0;">Agent Network Graph</h2>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary btn-small" onclick="switchToAgentsView()">Back to List</button>
                </div>
            </div>

            <div style="background: var(--sand-100); border: 1px solid var(--sand-300); border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                <div style="display: flex; gap: 24px; font-size: 13px;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: var(--brand-500);"></div>
                        <span>Running</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: #10b981;"></div>
                        <span>Completed</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: #f59e0b;"></div>
                        <span>Stuck</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: #ef4444;"></div>
                        <span>Failed</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: #6b7280;"></div>
                        <span>Pending</span>
                    </div>
                    <div style="margin-left: 20px;">→ Parent-Child</div>
                    <div>⟷ Team Members</div>
                    <div>💬 Messages</div>
                </div>
            </div>

            <div id="network-graph-container" style="background: white; border: 2px solid var(--sand-300); border-radius: 8px; min-height: 600px; position: relative; overflow: hidden;">
                <svg id="network-graph-svg" width="100%" height="600" style="display: block;"></svg>
            </div>

            <div id="network-stats" style="margin-top: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
            </div>
        </div>
    `;

    listContainer.innerHTML = graphHTML;

    // Render the network graph
    renderNetworkGraph(agents, teams);
}

function renderNetworkGraph(agents, teams) {
    const svg = document.getElementById('network-graph-svg');
    if (!svg) return;

    const width = svg.clientWidth || 800;
    const height = 600;
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);

    // Clear existing content
    svg.innerHTML = '';

    // Build graph data structure
    const nodes = [];
    const edges = [];

    // Create nodes for each agent
    agents.forEach(agent => {
        nodes.push({
            id: agent.id,
            label: agent.id.substring(0, 8),
            status: agent.status,
            role: agent.role,
            team_id: agent.team_id,
            x: Math.random() * (width - 100) + 50,
            y: Math.random() * (height - 100) + 50,
        });
    });

    // Create edges for parent-child relationships
    agents.forEach(agent => {
        if (agent.parent_agent_id) {
            edges.push({
                source: agent.parent_agent_id,
                target: agent.id,
                type: 'parent-child',
            });
        }
    });

    // Create edges for team relationships
    teams.forEach(team => {
        if (team.status === 'active') {
            const teamMembers = [team.lead_agent_id, ...team.member_agent_ids].filter(id => id);
            for (let i = 0; i < teamMembers.length; i++) {
                for (let j = i + 1; j < teamMembers.length; j++) {
                    edges.push({
                        source: teamMembers[i],
                        target: teamMembers[j],
                        type: 'team',
                    });
                }
            }
        }
    });

    // Simple force-directed layout (basic clustering)
    const iterations = 100;
    for (let iter = 0; iter < iterations; iter++) {
        // Apply forces
        nodes.forEach(node => {
            let fx = 0, fy = 0;

            // Repulsion from other nodes
            nodes.forEach(other => {
                if (node.id !== other.id) {
                    const dx = node.x - other.x;
                    const dy = node.y - other.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                    const force = 500 / (dist * dist);
                    fx += (dx / dist) * force;
                    fy += (dy / dist) * force;
                }
            });

            // Attraction to connected nodes
            edges.forEach(edge => {
                if (edge.source === node.id || edge.target === node.id) {
                    const other = nodes.find(n => n.id === (edge.source === node.id ? edge.target : edge.source));
                    if (other) {
                        const dx = other.x - node.x;
                        const dy = other.y - node.y;
                        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                        const force = dist * 0.01;
                        fx += (dx / dist) * force;
                        fy += (dy / dist) * force;
                    }
                }
            });

            // Apply force
            node.x += fx * 0.1;
            node.y += fy * 0.1;

            // Keep within bounds
            node.x = Math.max(40, Math.min(width - 40, node.x));
            node.y = Math.max(40, Math.min(height - 40, node.y));
        });
    }

    // Render edges
    edges.forEach(edge => {
        const source = nodes.find(n => n.id === edge.source);
        const target = nodes.find(n => n.id === edge.target);
        if (!source || !target) return;

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', source.x);
        line.setAttribute('y1', source.y);
        line.setAttribute('x2', target.x);
        line.setAttribute('y2', target.y);

        if (edge.type === 'parent-child') {
            line.setAttribute('stroke', '#3b82f6');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('marker-end', 'url(#arrowhead)');
        } else if (edge.type === 'team') {
            line.setAttribute('stroke', '#10b981');
            line.setAttribute('stroke-width', '1');
            line.setAttribute('stroke-dasharray', '4,4');
        }

        svg.appendChild(line);
    });

    // Define arrowhead marker
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    marker.setAttribute('id', 'arrowhead');
    marker.setAttribute('markerWidth', '10');
    marker.setAttribute('markerHeight', '10');
    marker.setAttribute('refX', '9');
    marker.setAttribute('refY', '3');
    marker.setAttribute('orient', 'auto');
    const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    polygon.setAttribute('points', '0 0, 10 3, 0 6');
    polygon.setAttribute('fill', '#3b82f6');
    marker.appendChild(polygon);
    defs.appendChild(marker);
    svg.insertBefore(defs, svg.firstChild);

    // Render nodes
    nodes.forEach(node => {
        const statusColors = {
            'running': 'var(--brand-500)',
            'completed': '#10b981',
            'stuck': '#f59e0b',
            'failed': '#ef4444',
            'pending': '#6b7280',
        };
        const color = statusColors[node.status] || '#6b7280';

        // Node circle
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', node.x);
        circle.setAttribute('cy', node.y);
        circle.setAttribute('r', '20');
        circle.setAttribute('fill', color);
        circle.setAttribute('stroke', 'white');
        circle.setAttribute('stroke-width', '3');
        circle.style.cursor = 'pointer';
        circle.onclick = () => selectAgent(node.id);

        // Add hover effect
        circle.onmouseover = function() {
            this.setAttribute('r', '24');
            this.setAttribute('stroke-width', '4');
        };
        circle.onmouseout = function() {
            this.setAttribute('r', '20');
            this.setAttribute('stroke-width', '3');
        };

        svg.appendChild(circle);

        // Node label
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', node.x);
        text.setAttribute('y', node.y + 35);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-size', '11');
        text.setAttribute('font-weight', '600');
        text.setAttribute('fill', 'var(--sand-800)');
        text.textContent = node.label;
        text.style.pointerEvents = 'none';
        svg.appendChild(text);
    });

    // Render statistics
    const statsContainer = document.getElementById('network-stats');
    if (statsContainer) {
        const totalNodes = nodes.length;
        const totalEdges = edges.length;
        const parentChildEdges = edges.filter(e => e.type === 'parent-child').length;
        const teamEdges = edges.filter(e => e.type === 'team').length;

        statsContainer.innerHTML = `
            <div style="background: var(--sand-100); padding: 16px; border-radius: 8px;">
                <div style="font-size: 11px; color: var(--sand-600); margin-bottom: 4px;">Total Agents</div>
                <div style="font-size: 24px; font-weight: 600; color: var(--sand-900);">${totalNodes}</div>
            </div>
            <div style="background: var(--sand-100); padding: 16px; border-radius: 8px;">
                <div style="font-size: 11px; color: var(--sand-600); margin-bottom: 4px;">Connections</div>
                <div style="font-size: 24px; font-weight: 600; color: var(--sand-900);">${totalEdges}</div>
            </div>
            <div style="background: var(--sand-100); padding: 16px; border-radius: 8px;">
                <div style="font-size: 11px; color: var(--sand-600); margin-bottom: 4px;">Workflows</div>
                <div style="font-size: 24px; font-weight: 600; color: #3b82f6;">${parentChildEdges}</div>
            </div>
            <div style="background: var(--sand-100); padding: 16px; border-radius: 8px;">
                <div style="font-size: 11px; color: var(--sand-600); margin-bottom: 4px;">Team Links</div>
                <div style="font-size: 24px; font-weight: 600; color: #10b981;">${teamEdges}</div>
            </div>
        `;
    }
}

// Model Fallback Functions
async function fetchFallbackConfig() {
    try {
        const response = await fetch(`${API_BASE}/models/fallback/config`);
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Failed to fetch fallback config:', error);
    }
    return null;
}

async function updateFallbackConfig(config) {
    try {
        const response = await fetch(`${API_BASE}/models/fallback/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config),
        });
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Failed to update fallback config:', error);
    }
    return null;
}

async function fetchFallbackEvents(agentId = null, limit = 50) {
    try {
        const url = agentId
            ? `${API_BASE}/models/fallback/events?agent_id=${agentId}&limit=${limit}`
            : `${API_BASE}/models/fallback/events?limit=${limit}`;
        const response = await fetch(url);
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Failed to fetch fallback events:', error);
    }
    return [];
}

async function fetchFallbackStatistics() {
    try {
        const response = await fetch(`${API_BASE}/models/fallback/statistics`);
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Failed to fetch fallback statistics:', error);
    }
    return null;
}

async function showFallbackSettings() {
    const listContainer = document.getElementById('agent-list');
    const config = await fetchFallbackConfig();
    const stats = await fetchFallbackStatistics();
    const events = await fetchFallbackEvents(null, 20);

    if (!config) {
        listContainer.innerHTML = '<div class="empty-state"><p>Failed to load fallback configuration</p></div>';
        return;
    }

    const settingsHTML = `
        <div style="padding: 20px; max-width: 900px;">
            <h2 style="margin-bottom: 20px;">Model Fallback & Retry Settings</h2>

            <div style="background: var(--sand-100); border: 1px solid var(--sand-300); border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="margin-top: 0;">Configuration</h3>
                <form id="fallback-config-form">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                        <div>
                            <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                                <input type="checkbox" id="fallback-enabled" ${config.enabled ? 'checked' : ''}>
                                <span><strong>Enable Fallback</strong></span>
                            </label>

                            <label style="display: block; margin-bottom: 12px;">
                                <span style="display: block; margin-bottom: 4px; font-size: 14px; color: var(--sand-700);">Max Retries</span>
                                <input type="number" id="fallback-max-retries" value="${config.max_retries}" min="0" max="10" style="width: 100%; padding: 8px; border: 1px solid var(--sand-300); border-radius: 4px;">
                            </label>

                            <label style="display: block; margin-bottom: 12px;">
                                <span style="display: block; margin-bottom: 4px; font-size: 14px; color: var(--sand-700);">Retry Delay (seconds)</span>
                                <input type="number" id="fallback-retry-delay" value="${config.retry_delay}" min="0.1" max="60" step="0.1" style="width: 100%; padding: 8px; border: 1px solid var(--sand-300); border-radius: 4px;">
                            </label>

                            <label style="display: block; margin-bottom: 12px;">
                                <span style="display: block; margin-bottom: 4px; font-size: 14px; color: var(--sand-700);">Timeout (seconds)</span>
                                <input type="number" id="fallback-timeout" value="${config.timeout_seconds}" min="10" max="600" style="width: 100%; padding: 8px; border: 1px solid var(--sand-300); border-radius: 4px;">
                            </label>
                        </div>

                        <div>
                            <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                                <input type="checkbox" id="fallback-auto-timeout" ${config.auto_switch_on_timeout ? 'checked' : ''}>
                                <span>Auto-switch on timeout</span>
                            </label>

                            <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                                <input type="checkbox" id="fallback-auto-error" ${config.auto_switch_on_error ? 'checked' : ''}>
                                <span>Auto-switch on error</span>
                            </label>

                            <label style="display: block;">
                                <span style="display: block; margin-bottom: 4px; font-size: 14px; color: var(--sand-700);">Fallback Models (comma-separated)</span>
                                <textarea id="fallback-models" rows="4" style="width: 100%; padding: 8px; border: 1px solid var(--sand-300); border-radius: 4px; font-family: monospace; font-size: 12px;">${config.fallback_models.join(', ')}</textarea>
                                <small style="color: var(--sand-600);">Models will be tried in order when primary fails</small>
                            </label>
                        </div>
                    </div>

                    <div style="display: flex; gap: 8px;">
                        <button type="submit" class="btn btn-primary">Save Configuration</button>
                        <button type="button" class="btn btn-secondary" onclick="switchToAgentsView()">Cancel</button>
                    </div>
                </form>
            </div>

            ${stats && stats.total_events > 0 ? `
                <div style="background: var(--sand-100); border: 1px solid var(--sand-300); border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0;">Fallback Statistics</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px;">
                        <div style="background: var(--sand-50); padding: 12px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--sand-600); margin-bottom: 4px;">Total Events</div>
                            <div style="font-size: 24px; font-weight: 600; color: var(--sand-900);">${stats.total_events}</div>
                        </div>
                        <div style="background: var(--sand-50); padding: 12px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--sand-600); margin-bottom: 4px;">Most Reliable</div>
                            <div style="font-size: 14px; font-weight: 600; color: #10b981;">${stats.most_reliable_model || 'N/A'}</div>
                        </div>
                        <div style="background: var(--sand-50); padding: 12px; border-radius: 6px;">
                            <div style="font-size: 11px; color: var(--sand-600); margin-bottom: 4px;">Most Problematic</div>
                            <div style="font-size: 14px; font-weight: 600; color: #ef4444;">${stats.most_problematic_model || 'N/A'}</div>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                        <div>
                            <h4 style="font-size: 14px; margin-bottom: 8px;">By Reason</h4>
                            ${Object.entries(stats.by_reason).map(([reason, count]) => `
                                <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid var(--sand-200);">
                                    <span style="text-transform: capitalize;">${reason}</span>
                                    <span style="font-weight: 600;">${count}</span>
                                </div>
                            `).join('')}
                        </div>
                        <div>
                            <h4 style="font-size: 14px; margin-bottom: 8px;">By Model</h4>
                            ${Object.entries(stats.by_model).slice(0, 5).map(([model, count]) => `
                                <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid var(--sand-200);">
                                    <span style="font-size: 12px;">${escapeHtml(model)}</span>
                                    <span style="font-weight: 600;">${count}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            ` : ''}

            ${events.length > 0 ? `
                <div style="background: var(--sand-100); border: 1px solid var(--sand-300); border-radius: 8px; padding: 20px;">
                    <h3 style="margin-top: 0;">Recent Fallback Events (${events.length})</h3>
                    <div style="max-height: 400px; overflow-y: auto;">
                        ${events.map(event => {
                            const reasonColors = {
                                'timeout': '#f59e0b',
                                'error': '#ef4444',
                                'unavailable': '#6b7280'
                            };
                            const color = reasonColors[event.reason] || '#6b7280';

                            return `
                                <div style="background: var(--sand-50); border-left: 3px solid ${color}; padding: 12px; margin-bottom: 8px; border-radius: 4px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                        <span style="font-weight: 600; color: var(--sand-900);">${escapeHtml(event.primary_model)} → ${escapeHtml(event.fallback_model)}</span>
                                        <span style="font-size: 12px; color: var(--sand-600);">${formatTime(event.timestamp)}</span>
                                    </div>
                                    <div style="display: flex; gap: 12px; font-size: 12px; color: var(--sand-700);">
                                        <span>Agent: ${event.agent_id.substring(0, 8)}</span>
                                        <span style="color: ${color}; font-weight: 600;">Reason: ${event.reason}</span>
                                        <span>Retry: ${event.retry_attempt}</span>
                                    </div>
                                    ${event.error_message ? `
                                        <div style="margin-top: 8px; padding: 8px; background: var(--sand-100); border-radius: 4px; font-size: 11px; font-family: monospace; color: #ef4444;">
                                            ${escapeHtml(event.error_message.substring(0, 200))}${event.error_message.length > 200 ? '...' : ''}
                                        </div>
                                    ` : ''}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;

    listContainer.innerHTML = settingsHTML;

    // Add form submit handler
    document.getElementById('fallback-config-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveFallbackConfig();
    });
}

async function saveFallbackConfig() {
    const config = {
        enabled: document.getElementById('fallback-enabled').checked,
        max_retries: parseInt(document.getElementById('fallback-max-retries').value),
        retry_delay: parseFloat(document.getElementById('fallback-retry-delay').value),
        timeout_seconds: parseInt(document.getElementById('fallback-timeout').value),
        auto_switch_on_timeout: document.getElementById('fallback-auto-timeout').checked,
        auto_switch_on_error: document.getElementById('fallback-auto-error').checked,
        fallback_models: document.getElementById('fallback-models').value
            .split(',')
            .map(m => m.trim())
            .filter(m => m.length > 0),
    };

    const result = await updateFallbackConfig(config);
    if (result) {
        toastSuccess('Fallback configuration saved successfully!');
        await showFallbackSettings(); // Refresh the view
    } else {
        toastError('Failed to save fallback configuration');
    }
}

// Model Selection Functions
let availableModelsWithInfo = [];

async function fetchAvailableModelsWithInfo() {
    try {
        const response = await fetch(`${API_BASE}/models/available-with-info`);
        if (response.ok) {
            availableModelsWithInfo = await response.json();
            return availableModelsWithInfo;
        }
    } catch (error) {
        console.error('Failed to fetch models with info:', error);
    }
    return [];
}

async function getModelRecommendation(taskDescription) {
    try {
        const response = await fetch(`${API_BASE}/models/recommend?task_description=${encodeURIComponent(taskDescription)}`, {
            method: 'POST',
        });
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Failed to get model recommendation:', error);
    }
    return null;
}

function renderModelSelector(containerId, selectedModel = null) {
    const container = document.getElementById(containerId);
    if (!container || availableModelsWithInfo.length === 0) return;

    // Group models by availability
    const available = availableModelsWithInfo.filter(m => m.available);
    const unavailable = availableModelsWithInfo.filter(m => !m.available);

    let html = '<option value="">Default (from config)</option>';

    if (available.length > 0) {
        html += '<optgroup label="Available Models">';
        available.forEach(model => {
            const selected = model.name === selectedModel ? 'selected' : '';
            const qualityBadge = model.quality_tier === 'excellent' ? '⭐' :
                                model.quality_tier === 'good' ? '✓' : '';
            const speedBadge = model.speed_tier === 'fast' ? '⚡' :
                              model.speed_tier === 'medium' ? '◆' : '◇';
            html += `<option value="${model.name}" ${selected} data-info='${JSON.stringify(model)}'>${qualityBadge} ${speedBadge} ${model.name}${model.parameter_count ? ` (${model.parameter_count})` : ''}</option>`;
        });
        html += '</optgroup>';
    }

    if (unavailable.length > 0) {
        html += '<optgroup label="Not Downloaded (pull required)">';
        unavailable.forEach(model => {
            html += `<option value="${model.name}" disabled data-info='${JSON.stringify(model)}'>${model.name}${model.parameter_count ? ` (${model.parameter_count})` : ''} - Not Available</option>`;
        });
        html += '</optgroup>';
    }

    container.innerHTML = html;
}

function showModelInfo(modelName) {
    if (!modelName) {
        hideModelInfo();
        return;
    }

    const model = availableModelsWithInfo.find(m => m.name === modelName);
    if (!model) return;

    const infoContainer = document.getElementById('model-info-display');
    if (!infoContainer) return;

    const qualityColor = model.quality_tier === 'excellent' ? '#10b981' :
                        model.quality_tier === 'good' ? '#3b82f6' : '#6b7280';
    const speedColor = model.speed_tier === 'fast' ? '#10b981' :
                      model.speed_tier === 'medium' ? '#f59e0b' : '#ef4444';

    infoContainer.innerHTML = `
        <div style="background: var(--sand-50); border: 1px solid var(--sand-300); border-radius: 6px; padding: 12px; margin-top: 8px;">
            <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                <span style="background: ${qualityColor}20; color: ${qualityColor}; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">
                    Quality: ${model.quality_tier}
                </span>
                <span style="background: ${speedColor}20; color: ${speedColor}; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">
                    Speed: ${model.speed_tier}
                </span>
                ${model.parameter_count ? `<span style="background: var(--sand-200); color: var(--sand-700); padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${model.parameter_count}</span>` : ''}
            </div>
            <div style="font-size: 13px; color: var(--sand-800); margin-bottom: 6px;">
                <strong>Strengths:</strong> ${escapeHtml(model.strengths)}
            </div>
            ${model.weaknesses ? `
                <div style="font-size: 13px; color: var(--sand-700); margin-bottom: 6px;">
                    <strong>Weaknesses:</strong> ${escapeHtml(model.weaknesses)}
                </div>
            ` : ''}
            ${model.recommended_for.length > 0 ? `
                <div style="font-size: 12px; color: var(--sand-600);">
                    <strong>Best for:</strong> ${model.recommended_for.join(', ')}
                </div>
            ` : ''}
        </div>
    `;
    infoContainer.style.display = 'block';
}

function hideModelInfo() {
    const infoContainer = document.getElementById('model-info-display');
    if (infoContainer) {
        infoContainer.style.display = 'none';
    }
}

async function autoRecommendModel() {
    const taskInput = document.getElementById('task-input');
    const modelSelect = document.getElementById('model-input-select');

    if (!taskInput || !modelSelect || !taskInput.value) return;

    const recommendation = await getModelRecommendation(taskInput.value);
    if (recommendation && recommendation.recommended_model) {
        modelSelect.value = recommendation.recommended_model;
        showModelInfo(recommendation.recommended_model);

        // Show recommendation banner
        const banner = document.getElementById('model-recommendation-banner');
        if (banner) {
            banner.textContent = `💡 Recommended: ${recommendation.recommended_model} - ${recommendation.reason}`;
            banner.style.display = 'block';
            banner.style.background = 'var(--brand-50)';
            banner.style.color = 'var(--brand-700)';
            banner.style.padding = '8px 12px';
            banner.style.borderRadius = '4px';
            banner.style.fontSize = '12px';
            banner.style.marginTop = '8px';
        }
    }
}

// Model Performance Functions
async function fetchAllModelMetrics() {
    try {
        const response = await fetch(`${API_BASE}/models/metrics`);
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Failed to fetch model metrics:', error);
    }
    return [];
}

async function fetchModelLeaderboard(sortBy = 'success_rate', limit = 10) {
    try {
        const response = await fetch(`${API_BASE}/models/leaderboard?sort_by=${sortBy}&limit=${limit}`);
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Failed to fetch model leaderboard:', error);
    }
    return [];
}

async function compareModels(modelNames) {
    try {
        const response = await fetch(`${API_BASE}/models/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(modelNames),
        });
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Failed to compare models:', error);
    }
    return null;
}

async function resetModelMetrics(modelName = null) {
    try {
        const url = modelName
            ? `${API_BASE}/models/${modelName}/metrics/reset`
            : `${API_BASE}/models/metrics/reset-all`;
        const response = await fetch(url, { method: 'POST' });
        if (response.ok) {
            return true;
        }
    } catch (error) {
        console.error('Failed to reset model metrics:', error);
    }
    return false;
}

async function showModelPerformanceDashboard() {
    const listContainer = document.getElementById('agent-list');
    const metrics = await fetchAllModelMetrics();

    if (metrics.length === 0) {
        listContainer.innerHTML = '<div class="empty-state"><p>No model performance data available yet</p></div>';
        return;
    }

    let dashboardHTML = `
        <div style="padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0;">Model Performance Dashboard</h2>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary btn-small" onclick="refreshModelDashboard()">Refresh</button>
                    <button class="btn btn-danger btn-small" onclick="confirmResetAllMetrics()">Reset All</button>
                </div>
            </div>

            <div class="model-metrics-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px;">
    `;

    metrics.forEach(model => {
        const successClass = model.success_rate >= 90 ? 'success' : model.success_rate >= 70 ? 'warning' : 'danger';
        const responseTimeColor = model.average_response_time < 2 ? '#10b981' : model.average_response_time < 5 ? '#f59e0b' : '#ef4444';

        dashboardHTML += `
            <div class="model-metric-card" style="background: var(--sand-100); border: 1px solid var(--sand-300); border-radius: 8px; padding: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                    <h3 style="margin: 0; font-size: 16px; color: var(--sand-900);">${escapeHtml(model.model_name)}</h3>
                    <span class="badge badge-${successClass}" style="font-size: 11px;">${model.success_rate.toFixed(1)}%</span>
                </div>

                <div class="metric-stat-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                    <div style="background: var(--sand-50); padding: 8px; border-radius: 4px;">
                        <div style="font-size: 11px; color: var(--sand-600); margin-bottom: 4px;">Total Requests</div>
                        <div style="font-size: 18px; font-weight: 600; color: var(--sand-900);">${model.total_requests}</div>
                    </div>
                    <div style="background: var(--sand-50); padding: 8px; border-radius: 4px;">
                        <div style="font-size: 11px; color: var(--sand-600); margin-bottom: 4px;">Avg Response</div>
                        <div style="font-size: 18px; font-weight: 600; color: ${responseTimeColor};">${model.average_response_time.toFixed(2)}s</div>
                    </div>
                </div>

                <div style="background: var(--sand-50); padding: 8px; border-radius: 4px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-size: 11px; color: var(--sand-600);">Success / Failed</span>
                        <span style="font-size: 11px; color: var(--sand-700);">${model.successful_requests} / ${model.failed_requests}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 11px; color: var(--sand-600);">Avg Tokens</span>
                        <span style="font-size: 11px; color: var(--sand-700);">${model.average_tokens_per_request.toFixed(0)}</span>
                    </div>
                </div>

                ${model.last_used ? `
                    <div style="font-size: 11px; color: var(--sand-600); margin-bottom: 8px;">
                        Last used: ${formatTime(model.last_used)}
                    </div>
                ` : ''}

                ${model.error_messages.length > 0 ? `
                    <details style="margin-top: 8px; font-size: 12px;">
                        <summary style="color: var(--danger-500); cursor: pointer;">Recent Errors (${model.error_messages.length})</summary>
                        <div style="margin-top: 8px; max-height: 100px; overflow-y: auto; background: var(--danger-50); padding: 8px; border-radius: 4px;">
                            ${model.error_messages.map(err => `<div style="margin-bottom: 4px; color: var(--danger-700);">${escapeHtml(err)}</div>`).join('')}
                        </div>
                    </details>
                ` : ''}

                <div style="display: flex; gap: 8px; margin-top: 12px;">
                    <button class="btn btn-secondary btn-small" onclick="showModelDetails('${escapeHtml(model.model_name)}')" style="flex: 1;">Details</button>
                    <button class="btn btn-danger btn-small" onclick="resetModelMetrics('${escapeHtml(model.model_name)}').then(refreshModelDashboard)">Reset</button>
                </div>
            </div>
        `;
    });

    dashboardHTML += `
            </div>
        </div>
    `;

    listContainer.innerHTML = dashboardHTML;
}

async function refreshModelDashboard() {
    await showModelPerformanceDashboard();
}

async function confirmResetAllMetrics() {
    if (confirm('Are you sure you want to reset all model performance metrics? This action cannot be undone.')) {
        const success = await resetModelMetrics();
        if (success) {
            await refreshModelDashboard();
        }
    }
}

async function showModelDetails(modelName) {
    // Switch to detail panel and show model-specific metrics
    toastInfo(`Model details for ${modelName} - Full detail view coming soon!`, 'Model Details');
}

// Priority and Scheduling Functions
async function setAgentPriority(agentId, priority) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/priority`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ priority }),
        });

        if (response.ok) {
            await fetchAgents();
            return true;
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to set priority');
        }
    } catch (error) {
        console.error('Failed to set agent priority:', error);
        throw error;
    }
}

async function scheduleAgent(agentId, startTime) {
    try {
        const response = await fetch(`${API_BASE}/agents/${agentId}/schedule`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start_time: startTime }),
        });

        if (response.ok) {
            await fetchAgents();
            return true;
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to schedule agent');
        }
    } catch (error) {
        console.error('Failed to schedule agent:', error);
        throw error;
    }
}

async function fetchPriorityQueue() {
    try {
        const response = await fetch(`${API_BASE}/agents/priority-queue`);
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Failed to fetch priority queue:', error);
    }
    return [];
}

async function bulkSetPriority(agentIds, priority) {
    try {
        const response = await fetch(`${API_BASE}/agents/bulk-priority`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ agent_ids: agentIds, priority }),
        });

        if (response.ok) {
            await fetchAgents();
            return await response.json();
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to bulk set priority');
        }
    } catch (error) {
        console.error('Failed to bulk set priority:', error);
        throw error;
    }
}

function getPriorityBadgeClass(priority) {
    if (priority <= 2) return 'priority-urgent';
    if (priority <= 4) return 'priority-high';
    if (priority <= 6) return 'priority-medium';
    return 'priority-low';
}

function getPriorityLabel(priority) {
    if (priority <= 2) return 'Urgent';
    if (priority <= 4) return 'High';
    if (priority <= 6) return 'Medium';
    return 'Low';
}

async function showPriorityQueueView() {
    const queue = await fetchPriorityQueue();
    const listContainer = document.getElementById('agent-list');

    if (queue.length === 0) {
        listContainer.innerHTML = '<div class="empty-state"><p>No agents in priority queue</p></div>';
        return;
    }

    const queueHTML = queue.map((agent, index) => `
        <div class="agent-card priority-queue-card" onclick="selectAgent('${agent.id}')">
            <div class="queue-position">#${index + 1}</div>
            <div class="agent-card-header">
                <h3>${escapeHtml(agent.task)}</h3>
                <div class="priority-badges">
                    <span class="badge badge-${agent.status}">${agent.status}</span>
                    <span class="badge ${getPriorityBadgeClass(agent.priority)}">
                        P${agent.priority}: ${getPriorityLabel(agent.priority)}
                    </span>
                </div>
            </div>
            <div class="agent-card-body">
                <p class="agent-meta">Role: ${agent.role || 'general'}</p>
                ${agent.scheduled_start_time ? `<p class="agent-meta">⏰ Scheduled: ${formatDate(agent.scheduled_start_time)}</p>` : ''}
                <p class="agent-meta">Created: ${formatDate(agent.created_at)}</p>
            </div>
        </div>
    `).join('');

    listContainer.innerHTML = queueHTML;
}

function renderPriorityControls(agentId, currentPriority) {
    const priorities = [
        { value: 1, label: 'P1: Critical' },
        { value: 2, label: 'P2: Urgent' },
        { value: 3, label: 'P3: High' },
        { value: 4, label: 'P4: High' },
        { value: 5, label: 'P5: Medium (Default)' },
        { value: 6, label: 'P6: Medium' },
        { value: 7, label: 'P7: Low' },
        { value: 8, label: 'P8: Low' },
        { value: 9, label: 'P9: Very Low' },
        { value: 10, label: 'P10: Lowest' },
    ];

    return `
        <div class="priority-controls">
            <label for="priority-select-${agentId}"><strong>Priority:</strong></label>
            <select id="priority-select-${agentId}" class="priority-select" onchange="updateAgentPriority('${agentId}', this.value)">
                ${priorities.map(p => `
                    <option value="${p.value}" ${p.value === currentPriority ? 'selected' : ''}>
                        ${p.label}
                    </option>
                `).join('')}
            </select>
        </div>
    `;
}

async function updateAgentPriority(agentId, priority) {
    try {
        await setAgentPriority(agentId, parseInt(priority));
        if (state.selectedAgentId === agentId) {
            selectAgent(agentId); // Refresh detail view
        }
    } catch (error) {
        toastError(`Failed to update priority: ${error.message}`);
    }
}

// Populate team creation form with available agents
function populateTeamAgentSelections() {
    const leadSelect = document.getElementById('team-lead-input');
    const membersList = document.getElementById('team-members-list');

    if (!leadSelect || !membersList) return;

    const agents = Array.from(state.agents.values());

    // Populate lead dropdown
    leadSelect.innerHTML = '<option value="">No Lead</option>';
    agents.forEach(agent => {
        const option = document.createElement('option');
        option.value = agent.id;
        option.textContent = `${agent.id} - ${agent.task.substring(0, 50)}${agent.task.length > 50 ? '...' : ''}`;
        leadSelect.appendChild(option);
    });

    // Populate members checkboxes
    if (agents.length === 0) {
        membersList.innerHTML = '<p style="color: var(--sand-600); text-align: center;">No agents available</p>';
    } else {
        membersList.innerHTML = agents.map(agent => `
            <label style="display: block; padding: 4px 0; cursor: pointer;">
                <input type="checkbox" class="team-member-checkbox" value="${agent.id}">
                ${agent.id} - ${escapeHtml(agent.task.substring(0, 60))}${agent.task.length > 60 ? '...' : ''}
            </label>
        `).join('');
    }
}

// Resource Usage Visualization
async function showResourceUsageView() {
    const listContainer = document.getElementById('agent-list');
    const agents = Array.from(state.agents.values());

    if (agents.length === 0) {
        listContainer.innerHTML = '<div class="empty-state"><p>No agents to analyze resource usage.</p></div>';
        return;
    }

    // Calculate resource metrics for each agent
    const agentMetrics = agents.map(agent => {
        const created = new Date(agent.created_at);
        const now = Date.now();
        const duration = (now - created.getTime()) / 1000; // seconds
        const durationMinutes = duration / 60;
        const durationHours = duration / 3600;

        // Calculate rates
        const toolCallRate = durationMinutes > 0 ? agent.progress.tool_calls / durationMinutes : 0;
        const completionRate = agent.progress.total_steps > 0 ? (agent.progress.completed_steps / agent.progress.total_steps) * 100 : 0;
        const errorRate = agent.progress.tool_calls > 0 ? (agent.progress.errors / agent.progress.tool_calls) * 100 : 0;

        // Estimate resource consumption score (higher = more resources)
        const resourceScore = (agent.progress.tool_calls * 1) +
                            (agent.messages.length * 0.5) +
                            (agent.artifacts.length * 2) +
                            (durationMinutes * 0.1);

        return {
            agent,
            duration,
            durationMinutes,
            durationHours,
            toolCallRate,
            completionRate,
            errorRate,
            resourceScore,
            toolCalls: agent.progress.tool_calls,
            messages: agent.messages.length,
            artifacts: agent.artifacts.length,
            errors: agent.progress.errors
        };
    });

    // Sort by resource score descending
    agentMetrics.sort((a, b) => b.resourceScore - a.resourceScore);
    const topConsumers = agentMetrics.slice(0, 10);

    // Calculate total stats
    const totalDuration = agentMetrics.reduce((sum, m) => sum + m.duration, 0);
    const totalToolCalls = agentMetrics.reduce((sum, m) => sum + m.toolCalls, 0);
    const totalMessages = agentMetrics.reduce((sum, m) => sum + m.messages, 0);
    const totalArtifacts = agentMetrics.reduce((sum, m) => sum + m.artifacts, 0);
    const avgCompletionRate = agentMetrics.length > 0
        ? agentMetrics.reduce((sum, m) => sum + m.completionRate, 0) / agentMetrics.length
        : 0;

    // Time distribution buckets
    const timeBuckets = [
        { label: '<1min', count: agentMetrics.filter(m => m.durationMinutes < 1).length },
        { label: '1-5min', count: agentMetrics.filter(m => m.durationMinutes >= 1 && m.durationMinutes < 5).length },
        { label: '5-15min', count: agentMetrics.filter(m => m.durationMinutes >= 5 && m.durationMinutes < 15).length },
        { label: '15-60min', count: agentMetrics.filter(m => m.durationMinutes >= 15 && m.durationMinutes < 60).length },
        { label: '>1hr', count: agentMetrics.filter(m => m.durationMinutes >= 60).length }
    ];

    const resourceHTML = `
        <div style="padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                <h2 style="margin: 0; font-size: 24px; font-weight: 700;">Resource Usage Dashboard</h2>
                <button class="btn btn-secondary btn-small" onclick="fetchAgents()">🔄 Refresh</button>
            </div>

            <!-- Summary Cards -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
                <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 20px; border-radius: 12px; color: white;">
                    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; opacity: 0.9; margin-bottom: 8px;">Total Runtime</div>
                    <div style="font-size: 32px; font-weight: 700;">${formatDuration(totalDuration)}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">${agents.length} agents tracked</div>
                </div>
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 20px; border-radius: 12px; color: white;">
                    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; opacity: 0.9; margin-bottom: 8px;">Tool Calls</div>
                    <div style="font-size: 32px; font-weight: 700;">${totalToolCalls.toLocaleString()}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">Avg ${(totalToolCalls / agents.length).toFixed(1)} per agent</div>
                </div>
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 20px; border-radius: 12px; color: white;">
                    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; opacity: 0.9; margin-bottom: 8px;">Messages</div>
                    <div style="font-size: 32px; font-weight: 700;">${totalMessages.toLocaleString()}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">${totalArtifacts} artifacts created</div>
                </div>
                <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 20px; border-radius: 12px; color: white;">
                    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; opacity: 0.9; margin-bottom: 8px;">Avg Completion</div>
                    <div style="font-size: 32px; font-weight: 700;">${avgCompletionRate.toFixed(0)}%</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">Task progress rate</div>
                </div>
            </div>

            <!-- Top Resource Consumers -->
            <div style="background: var(--sand-100); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
                <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">Top Resource Consumers</h3>
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    ${topConsumers.map((m, idx) => {
                        const statusColor = {
                            'running': '#3b82f6',
                            'completed': '#10b981',
                            'failed': '#ef4444',
                            'stuck': '#f59e0b'
                        }[m.agent.status] || '#6b7280';

                        return `
                            <div style="background: white; border-radius: 8px; padding: 16px; border-left: 4px solid ${statusColor}; cursor: pointer;" onclick="showAgentDetail('${m.agent.id}')">
                                <div style="display: flex; justify-content: space-between; align-items: start;">
                                    <div style="flex: 1; min-width: 0;">
                                        <div style="font-weight: 600; font-size: 14px; color: var(--sand-900); margin-bottom: 4px;">
                                            #${idx + 1} ${m.agent.id}
                                        </div>
                                        <div style="font-size: 12px; color: var(--sand-600); margin-bottom: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                            ${escapeHtml(m.agent.task.substring(0, 80))}${m.agent.task.length > 80 ? '...' : ''}
                                        </div>
                                        <div style="display: flex; gap: 16px; flex-wrap: wrap; font-size: 11px; color: var(--sand-600);">
                                            <span title="Tool calls">🔧 ${m.toolCalls}</span>
                                            <span title="Messages">💬 ${m.messages}</span>
                                            <span title="Artifacts">📄 ${m.artifacts}</span>
                                            <span title="Runtime">⏱️ ${formatDuration(m.duration)}</span>
                                            <span title="Tool call rate">📊 ${m.toolCallRate.toFixed(1)} calls/min</span>
                                        </div>
                                    </div>
                                    <div style="text-align: right; margin-left: 16px;">
                                        <div style="font-size: 20px; font-weight: 700; color: ${statusColor};">${m.resourceScore.toFixed(0)}</div>
                                        <div style="font-size: 10px; color: var(--sand-600); text-transform: uppercase;">Score</div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px;">
                <!-- Time Distribution -->
                <div style="background: var(--sand-100); border-radius: 12px; padding: 20px;">
                    <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">Runtime Distribution</h3>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        ${timeBuckets.map(bucket => {
                            const maxCount = Math.max(...timeBuckets.map(b => b.count));
                            const percentage = maxCount > 0 ? (bucket.count / maxCount) * 100 : 0;
                            return `
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <div style="width: 80px; font-size: 12px; font-weight: 600; color: var(--sand-700);">${bucket.label}</div>
                                    <div style="flex: 1; background: var(--sand-200); border-radius: 4px; height: 24px; overflow: hidden;">
                                        <div style="background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); height: 100%; width: ${percentage}%; transition: width 0.3s; display: flex; align-items: center; padding: 0 8px;">
                                            <span style="font-size: 11px; font-weight: 600; color: white;">${bucket.count}</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- Efficiency Metrics -->
                <div style="background: var(--sand-100); border-radius: 12px; padding: 20px;">
                    <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">Efficiency Metrics</h3>
                    <div style="display: flex; flex-direction: column; gap: 16px;">
                        ${[
                            {
                                label: 'Avg Tool Calls/Minute',
                                value: totalDuration > 0 ? (totalToolCalls / (totalDuration / 60)).toFixed(2) : '0',
                                icon: '🔧',
                                color: '#3b82f6'
                            },
                            {
                                label: 'Avg Messages/Agent',
                                value: (totalMessages / agents.length).toFixed(1),
                                icon: '💬',
                                color: '#10b981'
                            },
                            {
                                label: 'Artifact Creation Rate',
                                value: totalDuration > 0 ? ((totalArtifacts / (totalDuration / 3600)).toFixed(2) + '/hr') : '0/hr',
                                icon: '📄',
                                color: '#f59e0b'
                            },
                            {
                                label: 'Avg Error Rate',
                                value: (agentMetrics.reduce((sum, m) => sum + m.errorRate, 0) / agentMetrics.length).toFixed(1) + '%',
                                icon: '⚠️',
                                color: '#ef4444'
                            }
                        ].map(metric => `
                            <div style="background: white; border-radius: 8px; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span style="font-size: 20px;">${metric.icon}</span>
                                    <span style="font-size: 13px; color: var(--sand-700);">${metric.label}</span>
                                </div>
                                <div style="font-size: 18px; font-weight: 700; color: ${metric.color};">${metric.value}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>

            <!-- Activity Heatmap (Tool Calls over Time) -->
            <div style="background: var(--sand-100); border-radius: 12px; padding: 20px;">
                <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">Activity Intensity</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(60px, 1fr)); gap: 8px;">
                    ${agents.map(agent => {
                        const intensity = Math.min(agent.progress.tool_calls / 50, 1); // Normalize to 0-1
                        const color = intensity > 0.7 ? '#ef4444' : intensity > 0.4 ? '#f59e0b' : intensity > 0.1 ? '#3b82f6' : '#6b7280';
                        const bgOpacity = 0.1 + (intensity * 0.9);

                        return `
                            <div
                                style="background: ${color}${Math.round(bgOpacity * 255).toString(16).padStart(2, '0')}; border-radius: 8px; padding: 12px; cursor: pointer; transition: transform 0.2s; text-align: center;"
                                onclick="showAgentDetail('${agent.id}')"
                                onmouseover="this.style.transform='scale(1.05)'"
                                onmouseout="this.style.transform='scale(1)'"
                                title="${agent.id}: ${agent.progress.tool_calls} tool calls"
                            >
                                <div style="font-size: 10px; color: var(--sand-600); margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${agent.id.substring(0, 8)}</div>
                                <div style="font-size: 16px; font-weight: 700; color: ${color};">${agent.progress.tool_calls}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
                <div style="margin-top: 12px; display: flex; align-items: center; gap: 16px; font-size: 11px; color: var(--sand-600);">
                    <span>Intensity: </span>
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <div style="width: 12px; height: 12px; background: #6b7280; border-radius: 2px;"></div>
                        <span>Low</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <div style="width: 12px; height: 12px; background: #3b82f6; border-radius: 2px;"></div>
                        <span>Medium</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <div style="width: 12px; height: 12px; background: #f59e0b; border-radius: 2px;"></div>
                        <span>High</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <div style="width: 12px; height: 12px; background: #ef4444; border-radius: 2px;"></div>
                        <span>Very High</span>
                    </div>
                </div>
            </div>
        </div>
    `;

    listContainer.innerHTML = resourceHTML;
}

// Helper function to format duration
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.round(seconds % 60);
        return `${mins}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${mins}m`;
    }
}

// System Metrics Dashboard - Comprehensive Overview
async function showSystemMetricsDashboard() {
    const listContainer = document.getElementById('agent-list');
    const agents = Array.from(state.agents.values());
    const teams = state.teams || [];

    // Fetch model metrics
    let modelMetrics = [];
    try {
        const response = await fetch(`${API_BASE}/models/metrics`);
        modelMetrics = await response.json();
    } catch (error) {
        console.error('Failed to fetch model metrics:', error);
    }

    // Calculate comprehensive system metrics
    const now = Date.now();
    const last24h = now - (24 * 60 * 60 * 1000);
    const last7d = now - (7 * 24 * 60 * 60 * 1000);

    // Agent stats
    const agentStats = {
        total: agents.length,
        running: agents.filter(a => a.status === 'running').length,
        completed: agents.filter(a => a.status === 'completed').length,
        failed: agents.filter(a => a.status === 'failed').length,
        stuck: agents.filter(a => a.status === 'stuck').length,
        recent24h: agents.filter(a => new Date(a.created_at).getTime() > last24h).length,
        recent7d: agents.filter(a => new Date(a.created_at).getTime() > last7d).length
    };

    // Performance stats
    const totalToolCalls = agents.reduce((sum, a) => sum + a.progress.tool_calls, 0);
    const totalMessages = agents.reduce((sum, a) => sum + a.messages.length, 0);
    const totalArtifacts = agents.reduce((sum, a) => sum + a.artifacts.length, 0);
    const totalErrors = agents.reduce((sum, a) => sum + a.progress.errors, 0);
    const totalLoopDetections = agents.reduce((sum, a) => sum + a.progress.loop_detections, 0);

    const successRate = agentStats.total > 0
        ? (agentStats.completed / agentStats.total) * 100
        : 0;
    const errorRate = totalToolCalls > 0
        ? (totalErrors / totalToolCalls) * 100
        : 0;

    // Time-based metrics
    const avgDuration = agents.length > 0
        ? agents.reduce((sum, a) => sum + (now - new Date(a.created_at).getTime()) / 1000, 0) / agents.length
        : 0;

    // Model stats
    const modelUsage = {};
    agents.forEach(agent => {
        modelUsage[agent.model] = (modelUsage[agent.model] || 0) + 1;
    });
    const topModels = Object.entries(modelUsage)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

    // Team stats
    const teamStats = {
        total: teams.length,
        active: teams.filter(t => t.status === 'active').length,
        avgMembersPerTeam: teams.length > 0
            ? teams.reduce((sum, t) => sum + (t.member_agent_ids?.length || 0), 0) / teams.length
            : 0
    };

    // System health indicators
    const healthScore = calculateSystemHealth(agentStats, successRate, errorRate, totalLoopDetections);

    const dashboardHTML = `
        <div style="padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                <h2 style="margin: 0; font-size: 24px; font-weight: 700;">System Metrics Dashboard</h2>
                <div style="display: flex; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: ${healthScore.color}20; border-radius: 8px; border: 2px solid ${healthScore.color};">
                        <span style="font-size: 20px;">${healthScore.icon}</span>
                        <div>
                            <div style="font-size: 10px; text-transform: uppercase; color: var(--sand-600); font-weight: 600;">System Health</div>
                            <div style="font-size: 16px; font-weight: 700; color: ${healthScore.color};">${healthScore.label}</div>
                        </div>
                    </div>
                    <button class="btn btn-secondary btn-small" onclick="fetchAgents(); showSystemMetricsDashboard();">🔄 Refresh</button>
                </div>
            </div>

            <!-- Key Performance Indicators -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
                <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; opacity: 0.9; margin-bottom: 8px;">Total Agents</div>
                    <div style="font-size: 36px; font-weight: 700;">${agentStats.total}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">↑ ${agentStats.recent24h} in last 24h</div>
                </div>
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; opacity: 0.9; margin-bottom: 8px;">Success Rate</div>
                    <div style="font-size: 36px; font-weight: 700;">${successRate.toFixed(0)}%</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">${agentStats.completed} completed</div>
                </div>
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; opacity: 0.9; margin-bottom: 8px;">Active Now</div>
                    <div style="font-size: 36px; font-weight: 700;">${agentStats.running}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">${agentStats.stuck} stuck</div>
                </div>
                <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; opacity: 0.9; margin-bottom: 8px;">Tool Calls</div>
                    <div style="font-size: 36px; font-weight: 700;">${totalToolCalls.toLocaleString()}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">${(totalToolCalls / Math.max(agentStats.total, 1)).toFixed(0)} per agent</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-bottom: 24px;">
                <!-- Agent Status Distribution -->
                <div style="background: var(--sand-100); border-radius: 12px; padding: 20px;">
                    <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">Agent Status Distribution</h3>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        ${[
                            { label: 'Running', count: agentStats.running, color: '#3b82f6', icon: '🏃' },
                            { label: 'Completed', count: agentStats.completed, color: '#10b981', icon: '✅' },
                            { label: 'Stuck', count: agentStats.stuck, color: '#f59e0b', icon: '⚠️' },
                            { label: 'Failed', count: agentStats.failed, color: '#ef4444', icon: '❌' }
                        ].map(status => {
                            const percentage = agentStats.total > 0 ? (status.count / agentStats.total) * 100 : 0;
                            return `
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <span style="font-size: 20px;">${status.icon}</span>
                                    <div style="flex: 1;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                            <span style="font-size: 13px; font-weight: 600; color: var(--sand-700);">${status.label}</span>
                                            <span style="font-size: 13px; font-weight: 600; color: ${status.color};">${status.count} (${percentage.toFixed(0)}%)</span>
                                        </div>
                                        <div style="background: var(--sand-200); border-radius: 4px; height: 8px; overflow: hidden;">
                                            <div style="background: ${status.color}; height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- Quick Stats -->
                <div style="background: var(--sand-100); border-radius: 12px; padding: 20px;">
                    <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">Quick Stats</h3>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        ${[
                            { icon: '💬', label: 'Messages', value: totalMessages.toLocaleString() },
                            { icon: '📄', label: 'Artifacts', value: totalArtifacts.toLocaleString() },
                            { icon: '⚠️', label: 'Errors', value: `${totalErrors} (${errorRate.toFixed(1)}%)` },
                            { icon: '🔄', label: 'Loop Detections', value: totalLoopDetections.toLocaleString() },
                            { icon: '⏱️', label: 'Avg Duration', value: formatDuration(avgDuration) },
                            { icon: '👥', label: 'Teams', value: `${teamStats.active}/${teamStats.total}` }
                        ].map(stat => `
                            <div style="background: white; border-radius: 8px; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span style="font-size: 18px;">${stat.icon}</span>
                                    <span style="font-size: 12px; color: var(--sand-600);">${stat.label}</span>
                                </div>
                                <span style="font-size: 14px; font-weight: 700; color: var(--sand-900);">${stat.value}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px;">
                <!-- Top Models -->
                <div style="background: var(--sand-100); border-radius: 12px; padding: 20px;">
                    <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">Top Models by Usage</h3>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        ${topModels.length > 0 ? topModels.map(([ model, count], idx) => {
                            const percentage = (count / agentStats.total) * 100;
                            const modelInfo = modelMetrics.find(m => m.model_name === model);
                            return `
                                <div style="background: white; border-radius: 8px; padding: 12px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            <span style="font-size: 18px; font-weight: 700; color: var(--sand-400);">#${idx + 1}</span>
                                            <span style="font-size: 13px; font-weight: 600; color: var(--sand-900);">${model}</span>
                                        </div>
                                        <span style="font-size: 13px; font-weight: 600; color: #3b82f6;">${count} (${percentage.toFixed(0)}%)</span>
                                    </div>
                                    ${modelInfo ? `
                                        <div style="font-size: 10px; color: var(--sand-600); display: flex; gap: 12px;">
                                            <span>Success: ${modelInfo.success_rate.toFixed(0)}%</span>
                                            <span>Avg Time: ${modelInfo.average_response_time.toFixed(1)}s</span>
                                        </div>
                                    ` : ''}
                                </div>
                            `;
                        }).join('') : '<p style="color: var(--sand-600); text-align: center;">No model data</p>'}
                    </div>
                </div>

                <!-- Activity Timeline (Last 24h) -->
                <div style="background: var(--sand-100); border-radius: 12px; padding: 20px;">
                    <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">Activity Timeline (24h)</h3>
                    <div style="display: flex; align-items: end; gap: 4px; height: 150px;">
                        ${Array.from({ length: 24 }, (_, i) => {
                            const hourStart = last24h + (i * 60 * 60 * 1000);
                            const hourEnd = hourStart + (60 * 60 * 1000);
                            const hourAgents = agents.filter(a => {
                                const created = new Date(a.created_at).getTime();
                                return created >= hourStart && created < hourEnd;
                            });
                            const maxCount = Math.max(...Array.from({ length: 24 }, (_, j) => {
                                const hStart = last24h + (j * 60 * 60 * 1000);
                                const hEnd = hStart + (60 * 60 * 1000);
                                return agents.filter(a => {
                                    const c = new Date(a.created_at).getTime();
                                    return c >= hStart && c < hEnd;
                                }).length;
                            }), 1);
                            const height = (hourAgents.length / maxCount) * 100;
                            return `
                                <div
                                    style="flex: 1; background: linear-gradient(to top, #3b82f6, #60a5fa); border-radius: 4px 4px 0 0; height: ${height}%; min-height: 4px; transition: all 0.3s; cursor: pointer;"
                                    title="${new Date(hourStart).toLocaleTimeString([], { hour: '2-digit' })}: ${hourAgents.length} agents"
                                    onmouseover="this.style.background='linear-gradient(to top, #2563eb, #3b82f6)'"
                                    onmouseout="this.style.background='linear-gradient(to top, #3b82f6, #60a5fa)'"
                                ></div>
                            `;
                        }).join('')}
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 10px; color: var(--sand-600);">
                        <span>${new Date(last24h).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        <span>Now</span>
                    </div>
                </div>
            </div>

            <!-- System Recommendations -->
            ${generateSystemRecommendations(agentStats, successRate, errorRate, totalLoopDetections, healthScore)}
        </div>
    `;

    listContainer.innerHTML = dashboardHTML;
}

// Calculate system health score
function calculateSystemHealth(agentStats, successRate, errorRate, loopDetections) {
    let score = 100;
    let issues = [];

    // Success rate impact
    if (successRate < 50) {
        score -= 30;
        issues.push('Low success rate');
    } else if (successRate < 70) {
        score -= 15;
        issues.push('Moderate success rate');
    }

    // Error rate impact
    if (errorRate > 10) {
        score -= 20;
        issues.push('High error rate');
    } else if (errorRate > 5) {
        score -= 10;
        issues.push('Moderate error rate');
    }

    // Stuck agents impact
    const stuckRate = agentStats.total > 0 ? (agentStats.stuck / agentStats.total) * 100 : 0;
    if (stuckRate > 20) {
        score -= 25;
        issues.push('Many stuck agents');
    } else if (stuckRate > 10) {
        score -= 12;
        issues.push('Some stuck agents');
    }

    // Loop detections impact
    if (loopDetections > agentStats.total * 0.5) {
        score -= 15;
        issues.push('Frequent loop detections');
    }

    // Determine health level
    let health;
    if (score >= 80) {
        health = { label: 'Excellent', color: '#10b981', icon: '💚', level: 'excellent' };
    } else if (score >= 60) {
        health = { label: 'Good', color: '#3b82f6', icon: '💙', level: 'good' };
    } else if (score >= 40) {
        health = { label: 'Fair', color: '#f59e0b', icon: '💛', level: 'fair' };
    } else {
        health = { label: 'Poor', color: '#ef4444', icon: '💔', level: 'poor' };
    }

    health.score = Math.max(0, score);
    health.issues = issues;

    return health;
}

// Generate system recommendations
function generateSystemRecommendations(agentStats, successRate, errorRate, loopDetections, healthScore) {
    const recommendations = [];

    if (healthScore.score >= 80) {
        recommendations.push({
            type: 'success',
            icon: '✅',
            title: 'System Running Smoothly',
            message: 'All metrics are within healthy ranges. Keep up the great work!'
        });
    }

    if (successRate < 70) {
        recommendations.push({
            type: 'warning',
            icon: '⚠️',
            title: 'Low Success Rate Detected',
            message: 'Consider reviewing task complexity and model selection. Failed agents may need clearer instructions.'
        });
    }

    if (errorRate > 5) {
        recommendations.push({
            type: 'warning',
            icon: '🔧',
            title: 'High Error Rate',
            message: 'Review agent logs for common errors. Consider enabling model fallback to improve reliability.'
        });
    }

    const stuckRate = agentStats.total > 0 ? (agentStats.stuck / agentStats.total) * 100 : 0;
    if (stuckRate > 10) {
        recommendations.push({
            type: 'warning',
            icon: '⏸️',
            title: 'Stuck Agents Need Attention',
            message: `${agentStats.stuck} agents are stuck. Review loop detections and consider manual intervention or timeout adjustments.`
        });
    }

    if (loopDetections > agentStats.total * 0.3) {
        recommendations.push({
            type: 'info',
            icon: '🔄',
            title: 'Frequent Loop Detections',
            message: 'Agents may be repeating actions. Review task instructions and ensure clear success criteria.'
        });
    }

    if (agentStats.running > 10) {
        recommendations.push({
            type: 'info',
            icon: '⚡',
            title: 'High Concurrent Load',
            message: `${agentStats.running} agents running concurrently. Monitor system resources and consider priority queuing.`
        });
    }

    if (recommendations.length === 0) {
        recommendations.push({
            type: 'info',
            icon: '📊',
            title: 'No Issues Detected',
            message: 'System metrics look healthy. Continue monitoring for optimal performance.'
        });
    }

    const colorMap = {
        success: '#10b981',
        warning: '#f59e0b',
        info: '#3b82f6',
        error: '#ef4444'
    };

    return `
        <div style="background: var(--sand-100); border-radius: 12px; padding: 20px;">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">System Recommendations</h3>
            <div style="display: flex; flex-direction: column; gap: 12px;">
                ${recommendations.map(rec => `
                    <div style="background: white; border-left: 4px solid ${colorMap[rec.type]}; border-radius: 8px; padding: 16px;">
                        <div style="display: flex; align-items: start; gap: 12px;">
                            <span style="font-size: 24px; flex-shrink: 0;">${rec.icon}</span>
                            <div style="flex: 1;">
                                <div style="font-size: 14px; font-weight: 600; color: var(--sand-900); margin-bottom: 4px;">${rec.title}</div>
                                <div style="font-size: 12px; color: var(--sand-600); line-height: 1.5;">${rec.message}</div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Export & Reporting Functions


async function exportSession() {
    try {
        const response = await fetch(`${API_BASE}/export/session?include_artifacts=true&include_logs=true`);
        if (!response.ok) throw new Error('Export failed');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `hrisa-session-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        toastSuccess('Session exported successfully!', 'Export Complete');
    } catch (error) {
        console.error('Export error:', error);
        toastError(`Export failed: ${error.message}`, 'Export Failed');
    }
}


async function exportAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/export/analytics`);
        if (!response.ok) throw new Error('Export failed');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `hrisa-analytics-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        toastSuccess('Analytics exported successfully!', 'Export Complete');
    } catch (error) {
        console.error('Export error:', error);
        toastError(`Export failed: ${error.message}`, 'Export Failed');
    }
}


async function exportAgentData(agentId, format = 'json') {
    try {
        const response = await fetch(`${API_BASE}/export/agent/${agentId}?format=${format}`);
        if (!response.ok) throw new Error('Export failed');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        const extension = format === 'markdown' ? 'md' : 'json';
        a.href = url;
        a.download = `agent-${agentId}-${new Date().toISOString().split('T')[0]}.${extension}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        toastSuccess(`Agent data exported as ${format.toUpperCase()}!`, 'Export Complete');
    } catch (error) {
        console.error('Export error:', error);
        toastError(`Export failed: ${error.message}`, 'Export Failed');
    }
}


async function exportAgentLogs(agentId) {
    try {
        const response = await fetch(`${API_BASE}/export/logs/${agentId}`);
        if (!response.ok) throw new Error('Export failed');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `agent-${agentId}-logs-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        toastSuccess('Agent logs exported successfully!', 'Export Complete');
    } catch (error) {
        console.error('Export error:', error);
        toastError(`Export failed: ${error.message}`, 'Export Failed');
    }
}


// Override openModal to populate forms when opening modals
const originalOpenModal = window.openModal || openModal;
window.openModal = function(modalId) {
    if (modalId === 'create-team-modal') {
        populateTeamAgentSelections();
    } else if (modalId === 'create-agent-modal') {
        renderModelSelector('model-input-select');
        hideModelInfo();
        // Clear previous recommendation
        const banner = document.getElementById('model-recommendation-banner');
        if (banner) banner.style.display = 'none';
    }
    if (typeof originalOpenModal === 'function') {
        originalOpenModal(modalId);
    } else {
        document.getElementById(modalId).classList.add('open');
    }
};

// Create Team Form Handler
document.getElementById('create-team-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('team-name-input').value;
    const description = document.getElementById('team-description-input').value;
    const sharedGoal = document.getElementById('team-goal-input').value;
    const leadAgentId = document.getElementById('team-lead-input').value || null;

    // Get selected member agent IDs
    const memberCheckboxes = document.querySelectorAll('.team-member-checkbox:checked');
    const memberAgentIds = Array.from(memberCheckboxes).map(cb => cb.value);

    try {
        await createTeam(name, description, sharedGoal, leadAgentId, memberAgentIds);
        closeModal('create-team-modal');
        document.getElementById('create-team-form').reset();
        toastSuccess('Team created successfully!', 'Team Created');
    } catch (error) {
        toastError(`Failed to create team: ${error.message}`, 'Team Creation Failed');
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    loadRoles();
    connectWebSocket();
    fetchAgents();
    fetchTeams();
    await fetchAvailableModelsWithInfo();

    // Refresh agents and teams every 10 seconds
    setInterval(() => {
        fetchAgents();
        fetchTeams();
    }, 10000);
});

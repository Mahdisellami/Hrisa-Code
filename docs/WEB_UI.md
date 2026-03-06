# Hrisa Code Web UI Documentation

Comprehensive guide for the web-based agent management interface.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Features](#features)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [WebSocket Events](#websocket-events)
- [Usage Guide](#usage-guide)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Overview

The Hrisa Code Web UI provides a visual interface for managing multiple GenAI coding agents simultaneously. It offers real-time progress tracking, stuck detection, and the ability to intervene with instructions when agents need guidance.

### Key Capabilities

- **Multi-Agent Management**: Create and manage multiple agents concurrently
- **Real-Time Updates**: WebSocket-based live progress tracking
- **Stuck Detection**: Automatic detection when agents aren't making progress
- **User Intervention**: Send instructions to guide stuck agents
- **Progress Visualization**: Visual progress bars and statistics
- **Message History**: View all agent conversations
- **Output Viewing**: See agent outputs and results

## Getting Started

### Prerequisites

- Hrisa Code installed: `pip install -e ".[web]"`
- Ollama running: `ollama serve`
- At least one Ollama model pulled

### Starting the Server

```bash
# Start on default port (8000)
hrisa web

# Custom port
hrisa web --port 3000

# Development mode with auto-reload
hrisa web --reload
```

### Accessing the UI

Open your browser to:
- **Main UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Features

### 1. Dashboard Overview

The main dashboard displays:
- **System Statistics**: Running, stuck, and completed agent counts
- **Connection Status**: WebSocket connection indicator
- **Agent List**: All agents with status and progress
- **Filters**: Show/hide agents by status

### 2. Agent Creation

Create new agents with:
- **Task Description**: What you want the agent to do
- **Working Directory**: Where the agent should operate
- **Model Selection**: Which Ollama model to use
- **Tags**: Categorize agents for filtering

Example tasks:
```
"Analyze the codebase and generate a comprehensive README.md"
"Refactor the authentication module for better testability"
"Find and fix all TODO comments in the src/ directory"
"Generate API documentation for all endpoints"
```

### 3. Real-Time Progress Tracking

For each agent, see:
- **Current Status**: pending, running, stuck, completed, failed
- **Progress Bar**: Visual representation of completion
- **Step Count**: Completed vs total steps
- **Tool Calls**: Number of tools used
- **Loop Detections**: Times agent repeated same action
- **Last Activity**: When agent last did something

### 4. Stuck Detection

Agents are automatically marked as "stuck" when:
- No activity for 120 seconds (configurable)
- Repeatedly calling same tool
- Not making forward progress

When stuck, you can:
- Send clarifying instructions
- Cancel and restart with better prompt
- Delete if no longer needed

### 5. User Intervention

Send instructions to agents via:
- **Instruction Modal**: Rich text input
- **Real-Time Delivery**: Instruction added to conversation
- **Status Update**: Agent resumes from stuck state

Example instructions:
```
"Focus on the authentication module in src/auth/"
"Skip the tests directory and just document the main code"
"Use a more concise format for the documentation"
```

### 6. Message History

View complete conversation:
- User messages (your tasks and instructions)
- Assistant messages (agent responses)
- System messages (status updates)
- Tool calls and results

### 7. Output Viewing

See final results:
- Complete agent output
- Error messages if failed
- Success/completion status

## Architecture

### Backend (FastAPI)

```
src/hrisa_code/web/
├── __init__.py              # Package exports
├── server.py                # FastAPI application & API routes
├── agent_manager.py         # Agent orchestration & lifecycle
└── static/                  # Frontend files
    ├── index.html           # Main UI structure
    ├── styles.css           # Styling
    └── app.js               # Frontend logic
```

### Components

**1. WebAgentManager** (`agent_manager.py`)
- Manages multiple concurrent agents
- Tracks agent state and progress
- Detects stuck conditions
- Provides callbacks for UI updates

**2. FastAPI Server** (`server.py`)
- REST API for agent CRUD operations
- WebSocket endpoint for real-time updates
- Static file serving for frontend
- Request/response models

**3. Frontend** (`static/`)
- Single-page application (HTML/JS/CSS)
- WebSocket client for live updates
- API client for agent management
- Responsive design

### Data Flow

```
User Action (Browser)
    ↓
API Request (REST)
    ↓
WebAgentManager
    ↓
Agent Instance (core.planning.agent)
    ↓
Ollama LLM + Tools
    ↓
WebSocket Events (Real-time)
    ↓
Browser UI Update
```

## API Reference

### REST Endpoints

#### GET /api/stats
Get system statistics.

**Response:**
```json
{
  "total_agents": 10,
  "running_agents": 2,
  "stuck_agents": 1,
  "completed_agents": 5,
  "failed_agents": 1,
  "cancelled_agents": 1
}
```

#### GET /api/agents
List all agents.

**Query Parameters:**
- `status` (optional): Filter by status
- `tags` (optional): Comma-separated tags

**Response:**
```json
[
  {
    "id": "uuid",
    "task": "Generate README.md",
    "status": "running",
    "created_at": "2026-03-03T...",
    "working_dir": "/path/to/project",
    "model": "qwen2.5-coder:32b",
    "progress": {
      "total_steps": 10,
      "completed_steps": 5,
      "current_step": "Analyzing codebase",
      "tool_calls": 15,
      "loop_detections": 0,
      "errors": 0,
      "last_activity": "2026-03-03T..."
    },
    "output": "",
    "error": null,
    "stuck_reason": null,
    "tags": ["documentation"],
    "message_count": 25
  }
]
```

#### GET /api/agents/{agent_id}
Get specific agent details.

**Response:** Single agent object (same as list)

#### GET /api/agents/{agent_id}/messages
Get agent conversation history.

**Query Parameters:**
- `offset` (default: 0): Skip N messages
- `limit` (default: 100): Max messages to return

**Response:**
```json
[
  {
    "timestamp": "2026-03-03T...",
    "role": "user",
    "content": "Generate README.md",
    "tool_calls": null,
    "tool_results": null
  },
  {
    "timestamp": "2026-03-03T...",
    "role": "assistant",
    "content": "I'll analyze the codebase...",
    "tool_calls": [...],
    "tool_results": null
  }
]
```

#### POST /api/agents
Create a new agent.

**Request Body:**
```json
{
  "task": "Generate comprehensive README.md",
  "working_dir": "/path/to/project",  // optional
  "model": "qwen2.5-coder:32b",       // optional
  "tags": ["documentation", "readme"]  // optional
}
```

**Response:** Agent object

#### POST /api/agents/{agent_id}/start
Start an agent.

**Response:**
```json
{
  "status": "started",
  "agent_id": "uuid"
}
```

#### POST /api/agents/{agent_id}/instruction
Send instruction to agent.

**Request Body:**
```json
{
  "instruction": "Focus on the main features only"
}
```

**Response:**
```json
{
  "status": "sent",
  "agent_id": "uuid"
}
```

#### POST /api/agents/{agent_id}/cancel
Cancel a running agent.

**Response:**
```json
{
  "status": "cancelled",
  "agent_id": "uuid"
}
```

#### DELETE /api/agents/{agent_id}
Delete an agent (cancels if running).

**Response:**
```json
{
  "status": "deleted",
  "agent_id": "uuid"
}
```

## WebSocket Events

### Connection

Connect to: `ws://localhost:8000/ws`

### Event Types

#### connected
Sent when WebSocket connection established.

```json
{
  "type": "connected",
  "data": {
    "message": "Connected to Hrisa Code Web UI"
  }
}
```

#### agent_status
Sent when agent status changes.

```json
{
  "type": "agent_status",
  "data": {
    "agent_id": "uuid",
    "agent": { /* full agent object */ }
  }
}
```

#### agent_message
Sent when agent receives new message.

```json
{
  "type": "agent_message",
  "data": {
    "agent_id": "uuid",
    "message": {
      "timestamp": "...",
      "role": "assistant",
      "content": "..."
    }
  }
}
```

#### agent_stuck
Sent when agent is detected as stuck.

```json
{
  "type": "agent_stuck",
  "data": {
    "agent_id": "uuid",
    "reason": "No activity for 120 seconds"
  }
}
```

### Keep-Alive

Send `ping` to server every 30 seconds to maintain connection.

## Usage Guide

### Creating Your First Agent

1. **Click "Create New Agent"** button
2. **Enter task description**:
   ```
   Analyze the repository and generate a comprehensive CONTRIBUTING.md
   with setup instructions, code style, and testing guidelines
   ```
3. **Optionally configure**:
   - Working directory (defaults to current)
   - Model (defaults to config)
   - Tags (e.g., "documentation", "onboarding")
4. **Click "Create & Start"**
5. **Watch progress** in real-time on the dashboard

### Monitoring Agent Progress

- **Status Badge**: Shows current state (running, stuck, completed)
- **Progress Bar**: Visual completion percentage
- **Statistics**: Steps, tool calls, loop detections
- **Last Activity**: Timestamp of last action
- **Click Agent Card**: Opens detailed view

### Handling Stuck Agents

When an agent shows "stuck" status:

1. **Click the agent** to open details
2. **Review stuck reason** (e.g., "No activity for 120 seconds")
3. **Review messages** to understand what happened
4. **Click "Send Instruction"**
5. **Provide guidance**:
   ```
   The API documentation is in the docs/ folder, not src/docs/.
   Please check docs/API.md for the endpoint descriptions.
   ```
6. **Agent resumes** with your clarification

### Managing Multiple Agents

- **Run up to 5 concurrent agents** (configurable)
- **Use filters** to show only running/stuck agents
- **Tag agents** for organization (e.g., "docs", "refactor", "tests")
- **Monitor stats** at top of dashboard
- **Bulk actions**: Clear all completed agents

### Viewing Results

Once agent completes:

1. **Status changes** to "completed"
2. **Click agent** to open details
3. **Scroll to "Output"** section
4. **View complete results**
5. **Check messages** for full conversation history
6. **Delete or archive** when done

## Development

### Running in Development Mode

```bash
# Enable auto-reload on code changes
hrisa web --reload

# Watch for frontend changes
# (edit files in src/hrisa_code/web/static/)
```

### Testing the API

```bash
# Open interactive API docs
open http://localhost:8000/docs

# Test endpoints with curl
curl http://localhost:8000/api/stats

curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{"task": "Test task"}'
```

### WebSocket Testing

```javascript
// Browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

### Customizing the Frontend

Edit files in `src/hrisa_code/web/static/`:

- **index.html**: Structure and layout
- **styles.css**: Styling and themes
- **app.js**: Logic and interactions

Changes require server restart (unless using `--reload`).

### Extending the Backend

Add new API endpoints in `server.py`:

```python
@app.get("/api/custom")
async def custom_endpoint():
    # Your logic
    return {"result": "data"}
```

Add features to agent manager in `agent_manager.py`:

```python
async def custom_feature(self, agent_id: str):
    # Your feature
    pass
```

## Troubleshooting

### Server Won't Start

**Problem**: "Address already in use"

**Solution**:
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr 8000  # Windows

# Use different port
hrisa web --port 3000
```

### WebSocket Connection Fails

**Problem**: "WebSocket closed" or "disconnected" status

**Solutions**:
1. Check server is running: `curl http://localhost:8000/health`
2. Check browser console for errors (F12)
3. Disable browser extensions that might block WebSockets
4. Check firewall settings

### Agent Stuck Immediately

**Problem**: New agents show "stuck" status right away

**Solutions**:
1. Increase stuck threshold (modify `agent_manager.py`):
   ```python
   manager = WebAgentManager(stuck_threshold_seconds=300)  # 5 minutes
   ```
2. Check Ollama is running: `ollama list`
3. Check model is available: `ollama pull qwen2.5-coder:7b`
4. Review agent task - might be unclear or too complex

### No Agents Showing

**Problem**: Dashboard shows "No agents match the current filters"

**Solutions**:
1. Check status filters (checkboxes in sidebar)
2. Click "Refresh" button
3. Check browser console for API errors
4. Verify server is responding: `curl http://localhost:8000/api/agents`

### Agent Not Making Progress

**Problem**: Agent running but no progress

**Solutions**:
1. Check agent messages in detail panel
2. Look for tool call errors
3. Check Ollama logs
4. Send instruction to clarify task
5. Cancel and recreate with clearer prompt

### Frontend Not Loading

**Problem**: Blank page or "Static files not found"

**Solutions**:
1. Verify static files exist:
   ```bash
   ls src/hrisa_code/web/static/
   # Should show: index.html, styles.css, app.js
   ```
2. Reinstall package:
   ```bash
   pip install -e ".[web]"
   ```
3. Check server logs for errors

### Performance Issues

**Problem**: UI slow or unresponsive

**Solutions**:
1. Limit concurrent agents (reduce `max_concurrent`)
2. Delete old completed agents
3. Reduce message polling frequency (modify `app.js`)
4. Use more powerful machine for Ollama
5. Use smaller models (e.g., 7B instead of 32B)

## Best Practices

### Task Descriptions

✅ **Good**:
```
"Generate a README.md that includes:
- Project overview
- Installation instructions
- Usage examples
- API reference
- Contributing guidelines"
```

❌ **Bad**:
```
"make readme"
```

### Model Selection

- **Small tasks** (< 5 min): `qwen2.5-coder:7b`
- **Medium tasks** (5-15 min): `qwen2.5-coder:14b`
- **Large tasks** (> 15 min): `qwen2.5-coder:32b`

### Monitoring

- Keep WebSocket connected for real-time updates
- Check stuck agents within 2-3 minutes
- Review message history before sending instructions
- Monitor system stats to avoid overloading

### Organization

- Use consistent tags: `documentation`, `refactoring`, `testing`
- Delete completed agents regularly
- Keep working directories organized
- Name tasks clearly for easy identification

## Advanced Usage

### Programmatic API Access

```python
import httpx
import asyncio

async def create_and_monitor_agent():
    async with httpx.AsyncClient() as client:
        # Create agent
        response = await client.post(
            "http://localhost:8000/api/agents",
            json={"task": "Generate API docs"}
        )
        agent = response.json()

        # Start agent
        await client.post(
            f"http://localhost:8000/api/agents/{agent['id']}/start"
        )

        # Monitor until complete
        while True:
            response = await client.get(
                f"http://localhost:8000/api/agents/{agent['id']}"
            )
            agent = response.json()

            if agent['status'] in ['completed', 'failed']:
                break

            await asyncio.sleep(5)

        print(f"Agent {agent['status']}: {agent['output']}")

asyncio.run(create_and_monitor_agent())
```

### Bulk Operations

```javascript
// Browser console - cancel all stuck agents
async function cancelStuckAgents() {
    const response = await fetch('/api/agents?status=stuck');
    const agents = await response.json();

    for (const agent of agents) {
        await fetch(`/api/agents/${agent.id}/cancel`, {
            method: 'POST'
        });
    }

    console.log(`Cancelled ${agents.length} stuck agents`);
}
```

## Security Considerations

⚠️ **Current Implementation**: Designed for local development

**Not Production-Ready**:
- No authentication/authorization
- No rate limiting
- No input sanitization
- Binds to 0.0.0.0 (all interfaces)

**For Production Use**:
1. Add authentication (JWT, OAuth, etc.)
2. Implement authorization (user permissions)
3. Add rate limiting (per user/IP)
4. Sanitize all inputs
5. Use HTTPS/WSS
6. Bind to specific interface
7. Add CORS restrictions
8. Implement audit logging

## Performance Tuning

### Server Settings

```python
# In server.py startup
agent_manager = WebAgentManager(
    max_concurrent=10,              # More concurrent agents
    stuck_threshold_seconds=180,    # Longer before marking stuck
)
```

### Frontend Settings

```javascript
// In app.js
const REFRESH_INTERVAL = 5000;  // Faster updates
const WS_PING_INTERVAL = 15000; // More frequent pings
```

### Ollama Optimization

```bash
# Use GPU if available
CUDA_VISIBLE_DEVICES=0 ollama serve

# Increase context window
ollama run qwen2.5-coder:32b --ctx-size 8192
```

## Future Enhancements

Planned features:
- [ ] Agent templates for common tasks
- [ ] Batch agent creation
- [ ] Agent scheduling/queuing
- [ ] Result comparison between agents
- [ ] Export conversation history
- [ ] Agent performance metrics
- [ ] Custom agent configurations
- [ ] Multi-user support
- [ ] Agent collaboration (agents helping agents)
- [ ] Persistence/database backend

## Support

- **Documentation**: This file
- **Issues**: https://github.com/yourusername/hrisa-code/issues
- **API Docs**: http://localhost:8000/docs (when server running)
- **Source**: `src/hrisa_code/web/`

---

**Version**: 0.2.0
**Last Updated**: 2026-03-03

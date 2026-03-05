"""FastAPI server for Hrisa Code web UI."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from hrisa_code.core.config import Config
from hrisa_code.web.agent_manager import (
    WebAgentManager,
    AgentStatus,
    AgentInfo,
    AgentMessage,
    AgentProgress,
    AgentLog,
    AgentArtifact,
)
from hrisa_code.web.roles import list_roles, AgentRole


# Request/Response Models
class CreateAgentRequest(BaseModel):
    """Request to create a new agent."""

    task: str = Field(..., description="Task description for the agent")
    working_dir: Optional[str] = Field(None, description="Working directory path")
    model: Optional[str] = Field(None, description="Ollama model to use")
    role: Optional[str] = Field("general", description="Agent role/persona (e.g., 'architect', 'coder', 'tester')")
    parent_agent_id: Optional[str] = Field(None, description="Parent agent to inherit artifacts from")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")


class SendInstructionRequest(BaseModel):
    """Request to send instruction to an agent."""

    instruction: str = Field(..., description="User instruction")


class CreateArtifactRequest(BaseModel):
    """Request to create an artifact."""

    name: str = Field(..., description="Artifact name")
    type: str = Field(..., description="Artifact type (code, document, data, etc.)")
    content: str = Field(..., description="Artifact content")
    description: Optional[str] = Field(None, description="Artifact description")
    metadata: Optional[Dict] = Field(None, description="Artifact metadata")
    file_path: Optional[str] = Field(None, description="File path")
    language: Optional[str] = Field(None, description="Programming language for code artifacts")


class AgentResponse(BaseModel):
    """Response containing agent information."""

    id: str
    task: str
    status: str
    created_at: str
    working_dir: str
    model: str
    role: Optional[str]
    progress: Dict
    output: str
    error: Optional[str]
    stuck_reason: Optional[str]
    tags: List[str]
    message_count: int


class AgentMessageResponse(BaseModel):
    """Response containing agent message."""

    timestamp: str
    role: str
    content: str
    tool_calls: Optional[List[Dict]]
    tool_results: Optional[List[Dict]]


class AgentLogResponse(BaseModel):
    """Response containing agent log entry."""

    timestamp: str
    level: str
    message: str
    metadata: Optional[Dict]


class AgentArtifactResponse(BaseModel):
    """Response containing agent artifact."""

    id: str
    name: str
    type: str
    content: str
    created_at: str
    description: Optional[str]
    metadata: Optional[Dict]
    file_path: Optional[str]
    language: Optional[str]


class StatsResponse(BaseModel):
    """Response containing system statistics."""

    total_agents: int
    running_agents: int
    stuck_agents: int
    completed_agents: int
    failed_agents: int
    cancelled_agents: int


# FastAPI app
app = FastAPI(
    title="Hrisa Code Web UI",
    description="Web interface for managing GenAI coding agents",
    version="0.2.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent manager
agent_manager: Optional[WebAgentManager] = None

# WebSocket connections
websocket_connections: Set[WebSocket] = set()

# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _agent_info_to_response(info: AgentInfo) -> AgentResponse:
    """Convert AgentInfo to response model.

    Args:
        info: Agent info

    Returns:
        Agent response model
    """
    return AgentResponse(
        id=info.id,
        task=info.task,
        status=info.status.value,
        created_at=info.created_at.isoformat(),
        working_dir=str(info.working_dir),
        model=info.model,
        role=info.role,
        progress={
            "total_steps": info.progress.total_steps,
            "completed_steps": info.progress.completed_steps,
            "current_step": info.progress.current_step,
            "tool_calls": info.progress.tool_calls,
            "loop_detections": info.progress.loop_detections,
            "errors": info.progress.errors,
            "last_activity": info.progress.last_activity.isoformat(),
        },
        output=info.output,
        error=info.error,
        stuck_reason=info.stuck_reason,
        tags=info.tags,
        message_count=len(info.messages),
    )


def _agent_message_to_response(msg: AgentMessage) -> AgentMessageResponse:
    """Convert AgentMessage to response model.

    Args:
        msg: Agent message

    Returns:
        Message response model
    """
    return AgentMessageResponse(
        timestamp=msg.timestamp.isoformat(),
        role=msg.role,
        content=msg.content,
        tool_calls=msg.tool_calls,
        tool_results=msg.tool_results,
    )


async def broadcast_update(event_type: str, data: Dict) -> None:
    """Broadcast update to all connected WebSocket clients.

    Args:
        event_type: Type of event
        data: Event data
    """
    message = json.dumps({"type": event_type, "data": data})

    # Remove disconnected clients
    disconnected = set()

    for ws in websocket_connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)

    websocket_connections.difference_update(disconnected)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize agent manager on startup."""
    global agent_manager
    import os

    # Load config
    config = Config.load_with_fallback(Path.cwd())

    # Override Ollama host from environment variable if set
    ollama_host = os.getenv("OLLAMA_HOST")
    if ollama_host:
        config.ollama.host = ollama_host
        print(f"Using Ollama host from environment: {ollama_host}")

    # Use available model if default not found (for Docker environment)
    # Default is qwen2.5:72b but we have qwen2.5-coder:7b in Docker
    if config.model.name == "qwen2.5:72b":
        config.model.name = "qwen2.5-coder:7b"
        print(f"Using available model: {config.model.name}")

    # Create agent manager
    agent_manager = WebAgentManager(config=config)

    # Add callbacks for WebSocket broadcasts
    async def on_status_change(agent_id: str, info: AgentInfo):
        await broadcast_update(
            "agent_status",
            {
                "agent_id": agent_id,
                "agent": _agent_info_to_response(info).dict(),
            },
        )

    async def on_message(agent_id: str, message: AgentMessage):
        await broadcast_update(
            "agent_message",
            {
                "agent_id": agent_id,
                "message": _agent_message_to_response(message).dict(),
            },
        )

    async def on_stuck(agent_id: str, reason: str):
        await broadcast_update(
            "agent_stuck",
            {
                "agent_id": agent_id,
                "reason": reason,
            },
        )

    agent_manager.add_status_callback(on_status_change)
    agent_manager.add_message_callback(on_message)
    agent_manager.add_stuck_callback(on_stuck)

    # Start manager
    await agent_manager.start()


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if agent_manager:
        await agent_manager.stop()


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(), status_code=200)
    return HTMLResponse(content="<h1>Hrisa Code Web UI</h1><p>Static files not found</p>", status_code=404)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "name": "Hrisa Code Web UI",
        "version": "0.2.0",
        "status": "running",
    }


@app.get("/api/roles")
async def get_roles():
    """Get available agent roles."""
    roles = list_roles()
    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "color": role.color,
            "icon": role.icon,
        }
        for role in roles
    ]


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agents = agent_manager.list_agents()

    return StatsResponse(
        total_agents=len(agents),
        running_agents=sum(1 for a in agents if a.status == AgentStatus.RUNNING),
        stuck_agents=sum(1 for a in agents if a.status == AgentStatus.STUCK),
        completed_agents=sum(1 for a in agents if a.status == AgentStatus.COMPLETED),
        failed_agents=sum(1 for a in agents if a.status == AgentStatus.FAILED),
        cancelled_agents=sum(1 for a in agents if a.status == AgentStatus.CANCELLED),
    )


@app.get("/api/agents", response_model=List[AgentResponse])
async def list_agents(
    status: Optional[str] = Query(None, description="Filter by status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
):
    """List all agents."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    # Parse filters
    status_filter = AgentStatus(status) if status else None
    tags_filter = tags.split(",") if tags else None

    agents = agent_manager.list_agents(status=status_filter, tags=tags_filter)

    return [_agent_info_to_response(agent) for agent in agents]


@app.get("/api/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent details."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return _agent_info_to_response(agent)


@app.get("/api/agents/{agent_id}/messages", response_model=List[AgentMessageResponse])
async def get_agent_messages(
    agent_id: str,
    offset: int = Query(0, ge=0, description="Message offset"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum messages"),
):
    """Get agent messages."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    messages = agent.messages[offset : offset + limit]

    return [_agent_message_to_response(msg) for msg in messages]


@app.get("/api/agents/{agent_id}/logs", response_model=List[AgentLogResponse])
async def get_agent_logs(
    agent_id: str,
    offset: int = Query(0, ge=0, description="Log offset"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum logs"),
):
    """Get agent logs."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    logs = agent.logs[offset : offset + limit]

    return [
        AgentLogResponse(
            timestamp=log.timestamp.isoformat(),
            level=log.level,
            message=log.message,
            metadata=log.metadata,
        )
        for log in logs
    ]


@app.get("/api/agents/{agent_id}/artifacts", response_model=List[AgentArtifactResponse])
async def get_agent_artifacts(agent_id: str):
    """Get agent artifacts."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    artifacts = agent_manager.get_artifacts(agent_id)

    return [
        AgentArtifactResponse(
            id=artifact.id,
            name=artifact.name,
            type=artifact.type,
            content=artifact.content,
            created_at=artifact.created_at.isoformat(),
            description=artifact.description,
            metadata=artifact.metadata,
            file_path=artifact.file_path,
            language=artifact.language,
        )
        for artifact in artifacts
    ]


@app.post("/api/agents/{agent_id}/artifacts")
async def create_agent_artifact(agent_id: str, request: CreateArtifactRequest):
    """Create an artifact for an agent."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        artifact_id = await agent_manager.add_artifact(
            agent_id=agent_id,
            name=request.name,
            type=request.type,
            content=request.content,
            description=request.description,
            metadata=request.metadata,
            file_path=request.file_path,
            language=request.language,
        )
        return {"artifact_id": artifact_id, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents", response_model=AgentResponse)
async def create_agent(request: CreateAgentRequest):
    """Create a new agent."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        working_dir = Path(request.working_dir) if request.working_dir else None

        agent_id = await agent_manager.create_agent(
            task=request.task,
            working_dir=working_dir,
            model=request.model,
            role=request.role,
            parent_agent_id=request.parent_agent_id,
            tags=request.tags,
        )

        agent = agent_manager.get_agent(agent_id)

        return _agent_info_to_response(agent)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """Start an agent."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        await agent_manager.start_agent(agent_id)
        return {"status": "started", "agent_id": agent_id}
    except ValueError as e:
        print(f"[ERROR] ValueError starting agent {agent_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Exception starting agent {agent_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/{agent_id}/instruction")
async def send_instruction(agent_id: str, request: SendInstructionRequest):
    """Send instruction to an agent."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        await agent_manager.send_instruction(agent_id, request.instruction)
        return {"status": "sent", "agent_id": agent_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/{agent_id}/cancel")
async def cancel_agent(agent_id: str):
    """Cancel an agent."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        await agent_manager.cancel_agent(agent_id)
        return {"status": "cancelled", "agent_id": agent_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent (cancel if running)."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Cancel if running
    if agent.status in [AgentStatus.RUNNING, AgentStatus.STUCK]:
        await agent_manager.cancel_agent(agent_id)

    # Remove from manager
    del agent_manager.agents[agent_id]

    return {"status": "deleted", "agent_id": agent_id}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    websocket_connections.add(websocket)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "Connected to Hrisa Code Web UI"},
        })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()

            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_connections.discard(websocket)


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server.

    Args:
        host: Host to bind to
        port: Port to listen on
        reload: Enable auto-reload for development
    """
    import uvicorn

    uvicorn.run(
        "hrisa_code.web.server:app",
        host=host,
        port=port,
        reload=reload,
    )

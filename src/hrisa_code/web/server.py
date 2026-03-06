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
    AgentState,
    AgentStateTransition,
    AgentMemory,
    InterAgentMessage,
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


class CreateChainedAgentRequest(BaseModel):
    """Request to create a chained agent."""

    task: str = Field(..., description="Task for the chained agent")
    role: Optional[str] = Field(None, description="Agent role (inherits from parent if not specified)")
    model: Optional[str] = Field(None, description="Model to use (inherits from parent if not specified)")
    auto_start: bool = Field(False, description="Auto-start this agent when parent completes")
    tags: Optional[List[str]] = Field(None, description="Tags (inherits from parent if not specified)")


class SaveSessionRequest(BaseModel):
    """Request to save a session."""

    name: str = Field(..., description="Session name")
    description: Optional[str] = Field(None, description="Session description")
    agent_ids: Optional[List[str]] = Field(None, description="Agent IDs to include (all if not specified)")


class SessionResponse(BaseModel):
    """Response containing session information."""

    id: str
    name: str
    description: Optional[str]
    created_at: str
    agent_count: int
    total_artifacts: int


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
    current_state: str
    parent_agent_id: Optional[str]
    child_agent_ids: List[str]
    workflow_step: int


class PaginatedAgentsResponse(BaseModel):
    """Paginated response for agents list."""

    agents: List[AgentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SendAgentMessageRequest(BaseModel):
    """Request to send message between agents."""

    to_agent_id: str = Field(..., description="Recipient agent ID")
    message_type: str = Field(..., description="Message type: request, response, notification, question")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict] = Field(None, description="Optional metadata")
    in_reply_to: Optional[str] = Field(None, description="Message ID this is replying to")


class InterAgentMessageResponse(BaseModel):
    """Response containing inter-agent message."""

    id: str
    timestamp: str
    from_agent_id: str
    to_agent_id: str
    message_type: str
    content: str
    metadata: Optional[Dict]
    in_reply_to: Optional[str]
    read: bool


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


class AgentStateTransitionResponse(BaseModel):
    """Response containing agent state transition."""

    timestamp: str
    from_state: Optional[str]
    to_state: str
    reason: Optional[str]


class AgentStateResponse(BaseModel):
    """Response containing agent state machine information."""

    current_state: str
    transitions: List[AgentStateTransitionResponse]


class AgentMemoryResponse(BaseModel):
    """Response containing agent memory information."""

    decisions: List[Dict]
    context: Dict
    intermediate_outputs: List[Dict]
    state_transitions: List[AgentStateTransitionResponse]
    working_memory: List[str]


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
        current_state=info.current_state.value,
        parent_agent_id=info.parent_agent_id,
        child_agent_ids=info.child_agent_ids,
        workflow_step=info.workflow_step,
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
    # Default is qwen2.5:72b but we have llama3.2:latest in Docker
    if config.model.name == "qwen2.5:72b":
        config.model.name = "llama3.2:latest"
        print(f"Using available model: {config.model.name}")
    elif config.model.name == "qwen2.5-coder:7b":
        config.model.name = "llama3.2:latest"
        print(f"Fallback to available model: {config.model.name}")

    # Create agent manager (limit to 1 concurrent to avoid Ollama overload)
    agent_manager = WebAgentManager(config=config, max_concurrent=1)

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

    async def on_stream(agent_id: str, chunk: str):
        await broadcast_update(
            "agent_stream",
            {
                "agent_id": agent_id,
                "chunk": chunk,
            },
        )

    agent_manager.add_status_callback(on_status_change)
    agent_manager.add_message_callback(on_message)
    agent_manager.add_stuck_callback(on_stuck)
    agent_manager.add_stream_callback(on_stream)

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


@app.get("/api/agents", response_model=PaginatedAgentsResponse)
async def list_agents(
    status: Optional[str] = Query(None, description="Filter by status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
):
    """List all agents with pagination."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    # Parse filters
    status_filter = AgentStatus(status) if status else None
    tags_filter = tags.split(",") if tags else None

    agents = agent_manager.list_agents(status=status_filter, tags=tags_filter)

    # Calculate pagination
    total = len(agents)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Ensure page is within bounds
    if page > total_pages:
        page = total_pages

    # Slice agents for current page
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_agents = agents[start_idx:end_idx]

    return PaginatedAgentsResponse(
        agents=[_agent_info_to_response(agent) for agent in paginated_agents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


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


@app.get("/api/agents/{agent_id}/artifacts/{artifact_id}/download")
async def download_artifact(agent_id: str, artifact_id: str):
    """Download a single artifact."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    artifacts = agent_manager.get_artifacts(agent_id)
    artifact = next((a for a in artifacts if a.id == artifact_id), None)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Determine file extension based on type/language
    language_map = {
        'python': '.py',
        'javascript': '.js',
        'typescript': '.ts',
        'java': '.java',
        'cpp': '.cpp',
        'c': '.c',
        'go': '.go',
        'rust': '.rs',
        'ruby': '.rb',
        'php': '.php',
        'swift': '.swift',
        'kotlin': '.kt',
        'sql': '.sql',
        'bash': '.sh',
        'shell': '.sh',
        'markdown': '.md',
        'json': '.json',
        'yaml': '.yaml',
        'xml': '.xml',
        'html': '.html',
        'css': '.css',
    }

    type_map = {
        'markdown': '.md',
        'json': '.json',
        'document': '.txt',
        'data': '.json',
        'diagram': '.txt',
    }

    # Priority: language > type > default
    if artifact.language and artifact.language.lower() in language_map:
        ext = language_map[artifact.language.lower()]
    elif artifact.type in type_map:
        ext = type_map[artifact.type]
    else:
        ext = '.txt'

    filename = f"{artifact.name}{ext}".replace(' ', '_')

    from fastapi.responses import Response
    return Response(
        content=artifact.content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@app.get("/api/agents/{agent_id}/artifacts/download-all")
async def download_all_artifacts(agent_id: str):
    """Download all artifacts as a zip file."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    artifacts = agent_manager.get_artifacts(agent_id)

    if not artifacts:
        raise HTTPException(status_code=404, detail="No artifacts to download")

    import io
    import zipfile

    # Create zip file in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for artifact in artifacts:
            # Determine file extension
            language_map = {
                'python': '.py',
                'javascript': '.js',
                'typescript': '.ts',
                'java': '.java',
                'cpp': '.cpp',
                'c': '.c',
                'go': '.go',
                'rust': '.rs',
                'ruby': '.rb',
                'php': '.php',
                'swift': '.swift',
                'kotlin': '.kt',
                'sql': '.sql',
                'bash': '.sh',
                'shell': '.sh',
                'markdown': '.md',
                'json': '.json',
                'yaml': '.yaml',
                'xml': '.xml',
                'html': '.html',
                'css': '.css',
            }

            type_map = {
                'markdown': '.md',
                'json': '.json',
                'document': '.txt',
                'data': '.json',
                'diagram': '.txt',
            }

            # Priority: language > type > default
            if artifact.language and artifact.language.lower() in language_map:
                ext = language_map[artifact.language.lower()]
            elif artifact.type in type_map:
                ext = type_map[artifact.type]
            else:
                ext = '.txt'

            filename = f"{artifact.name}{ext}".replace(' ', '_')

            # Add artifact to zip
            zip_file.writestr(filename, artifact.content)

    zip_buffer.seek(0)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="agent_{agent_id[:8]}_artifacts.zip"'
        }
    )


@app.get("/api/agents/{agent_id}/state", response_model=AgentStateResponse)
async def get_agent_state(agent_id: str):
    """Get agent state machine information."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentStateResponse(
        current_state=agent.current_state.value,
        transitions=[
            AgentStateTransitionResponse(
                timestamp=t.timestamp.isoformat(),
                from_state=t.from_state,
                to_state=t.to_state,
                reason=t.reason,
            )
            for t in agent.memory.state_transitions
        ],
    )


@app.get("/api/agents/{agent_id}/memory", response_model=AgentMemoryResponse)
async def get_agent_memory(agent_id: str):
    """Get agent memory information."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentMemoryResponse(
        decisions=agent.memory.decisions,
        context=agent.memory.context,
        intermediate_outputs=agent.memory.intermediate_outputs,
        state_transitions=[
            AgentStateTransitionResponse(
                timestamp=t.timestamp.isoformat(),
                from_state=t.from_state,
                to_state=t.to_state,
                reason=t.reason,
            )
            for t in agent.memory.state_transitions
        ],
        working_memory=agent.memory.working_memory,
    )


@app.get("/api/agents/{agent_id}/memory/decisions")
async def get_agent_decisions(agent_id: str):
    """Get agent decision history."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"decisions": agent.memory.decisions}


@app.get("/api/agents/{agent_id}/memory/outputs")
async def get_agent_outputs(agent_id: str):
    """Get agent intermediate outputs."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"outputs": agent.memory.intermediate_outputs}


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


@app.post("/api/agents/{agent_id}/chain", response_model=AgentResponse)
async def create_chained_agent(agent_id: str, request: CreateChainedAgentRequest):
    """Create a chained agent that inherits from parent."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        child_agent_id = await agent_manager.create_chained_agent(
            parent_agent_id=agent_id,
            task=request.task,
            role=request.role,
            auto_start=request.auto_start,
            model=request.model,
            tags=request.tags,
        )

        child_agent = agent_manager.get_agent(child_agent_id)
        if not child_agent:
            raise HTTPException(status_code=500, detail="Failed to create chained agent")

        return _agent_info_to_response(child_agent)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}/children", response_model=List[AgentResponse])
async def get_agent_children(agent_id: str):
    """Get direct children of an agent."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    children = agent_manager.get_children(agent_id)
    return [_agent_info_to_response(child) for child in children]


@app.get("/api/agents/{agent_id}/workflow", response_model=List[AgentResponse])
async def get_agent_workflow(agent_id: str):
    """Get full workflow chain for an agent."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    workflow = agent_manager.get_workflow_chain(agent_id)
    return [_agent_info_to_response(agent) for agent in workflow]


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


# Session Management Endpoints
@app.post("/api/sessions/save", response_model=SessionResponse)
async def save_session(request: SaveSessionRequest):
    """Save current session (agents, messages, artifacts, state)."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        session_id = agent_manager.save_session(
            name=request.name,
            description=request.description,
            agent_ids=request.agent_ids,
        )
        session_info = agent_manager.get_session(session_id)
        return SessionResponse(**session_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save session: {str(e)}")


@app.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions():
    """List all saved sessions."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    sessions = agent_manager.list_sessions()
    return [SessionResponse(**session) for session in sessions]


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session details."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    session_info = agent_manager.get_session(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(**session_info)


@app.post("/api/sessions/{session_id}/load")
async def load_session(session_id: str):
    """Load a saved session."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        agent_manager.load_session(session_id)
        return {"status": "loaded", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load session: {str(e)}")


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a saved session."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        agent_manager.delete_session(session_id)
        return {"status": "deleted", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")


@app.post("/api/agents/{agent_id}/replay")
async def replay_agent(agent_id: str):
    """Replay an agent's execution (create new agent with same task/context)."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Create new agent with same configuration
    new_agent_id = await agent_manager.create_agent(
        task=f"[REPLAY] {agent.task}",
        working_dir=agent.working_dir,
        model=agent.model,
        role=agent.role,
        tags=agent.tags + ["replay", f"replay-of-{agent_id[:8]}"],
    )

    # Start the new agent
    await agent_manager.start_agent(new_agent_id)

    return {"status": "replaying", "new_agent_id": new_agent_id, "original_agent_id": agent_id}


# Inter-Agent Messaging Endpoints
@app.post("/api/agents/{agent_id}/messages/send")
async def send_agent_message(agent_id: str, request: SendAgentMessageRequest):
    """Send a message from one agent to another."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        message_id = agent_manager.send_agent_message(
            from_agent_id=agent_id,
            to_agent_id=request.to_agent_id,
            message_type=request.message_type,
            content=request.content,
            metadata=request.metadata,
            in_reply_to=request.in_reply_to,
        )
        return {"status": "sent", "message_id": message_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/agents/{agent_id}/messages", response_model=List[InterAgentMessageResponse])
async def get_agent_messages(
    agent_id: str,
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    unread_only: bool = Query(False, description="Only unread messages"),
):
    """Get inter-agent messages for an agent."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    messages = agent_manager.get_agent_messages(
        agent_id=agent_id,
        filter_type=message_type,
        unread_only=unread_only,
    )

    return [
        InterAgentMessageResponse(
            id=msg.id,
            timestamp=msg.timestamp.isoformat(),
            from_agent_id=msg.from_agent_id,
            to_agent_id=msg.to_agent_id,
            message_type=msg.message_type,
            content=msg.content,
            metadata=msg.metadata,
            in_reply_to=msg.in_reply_to,
            read=msg.read,
        )
        for msg in messages
    ]


@app.post("/api/agents/{agent_id}/messages/{message_id}/read")
async def mark_message_read(agent_id: str, message_id: str):
    """Mark a message as read."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent_manager.mark_message_read(agent_id, message_id)
    return {"status": "marked_read", "message_id": message_id}


@app.get("/api/agents/{agent_id}/messages/thread/{other_agent_id}", response_model=List[InterAgentMessageResponse])
async def get_conversation_thread(agent_id: str, other_agent_id: str):
    """Get full conversation thread between two agents."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    messages = agent_manager.get_conversation_thread(agent_id, other_agent_id)

    return [
        InterAgentMessageResponse(
            id=msg.id,
            timestamp=msg.timestamp.isoformat(),
            from_agent_id=msg.from_agent_id,
            to_agent_id=msg.to_agent_id,
            message_type=msg.message_type,
            content=msg.content,
            metadata=msg.metadata,
            in_reply_to=msg.in_reply_to,
            read=msg.read,
        )
        for msg in messages
    ]


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

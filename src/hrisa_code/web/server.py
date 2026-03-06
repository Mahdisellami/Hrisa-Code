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
    AgentTeam,
    ModelPerformanceMetrics,
    ModelFallbackConfig,
    ModelFallbackEvent,
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
    priority: int
    scheduled_start_time: Optional[str]


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


class ShareArtifactRequest(BaseModel):
    """Request to share an artifact with other agents."""

    target_agent_ids: List[str] = Field(..., description="Agent IDs to share with")


class UpdateSharedArtifactRequest(BaseModel):
    """Request to update a shared artifact."""

    content: str = Field(..., description="New artifact content")


class CreateTeamRequest(BaseModel):
    """Request to create a new team."""

    name: str = Field(..., description="Team name")
    description: str = Field(..., description="Team description")
    shared_goal: str = Field(..., description="Team's shared objective")
    lead_agent_id: Optional[str] = Field(None, description="Team lead agent ID")
    member_agent_ids: Optional[List[str]] = Field(default_factory=list, description="Initial member agent IDs")


class AddTeamMemberRequest(BaseModel):
    """Request to add a member to a team."""

    agent_id: str = Field(..., description="Agent ID to add to team")


class TeamResponse(BaseModel):
    """Response containing team information."""

    id: str
    name: str
    description: str
    created_at: str
    lead_agent_id: Optional[str]
    member_agent_ids: List[str]
    shared_goal: str
    status: str


class SetPriorityRequest(BaseModel):
    """Request to set agent priority."""

    priority: int = Field(..., ge=1, le=10, description="Priority level (1=highest, 10=lowest)")


class ScheduleAgentRequest(BaseModel):
    """Request to schedule agent execution."""

    start_time: str = Field(..., description="ISO format datetime for scheduled start")


class BulkSetPriorityRequest(BaseModel):
    """Request to set priority for multiple agents."""

    agent_ids: List[str] = Field(..., description="List of agent IDs")
    priority: int = Field(..., ge=1, le=10, description="Priority level (1=highest, 10=lowest)")


class ModelMetricsResponse(BaseModel):
    """Response containing model performance metrics."""

    model_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_response_time: float
    average_tokens_per_request: float
    total_tokens: int
    last_used: Optional[str]
    error_messages: List[str]


class ModelComparisonResponse(BaseModel):
    """Response containing model comparison data."""

    models: List[str]
    metrics: Dict


class ModelInfoResponse(BaseModel):
    """Response containing model information."""

    name: str
    available: Optional[bool] = None
    capabilities: List[str]
    quality_tier: str
    speed_tier: str
    strengths: str
    weaknesses: Optional[str]
    parameter_count: Optional[str]
    recommended_for: List[str]


class ModelRecommendationResponse(BaseModel):
    """Response containing model recommendation."""

    recommended_model: Optional[str]
    reason: str


class FallbackConfigRequest(BaseModel):
    """Request to update fallback configuration."""

    enabled: Optional[bool] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay: Optional[float] = Field(None, ge=0.1, le=60.0)
    timeout_seconds: Optional[int] = Field(None, ge=10, le=600)
    fallback_models: Optional[List[str]] = None
    auto_switch_on_timeout: Optional[bool] = None
    auto_switch_on_error: Optional[bool] = None


class FallbackConfigResponse(BaseModel):
    """Response containing fallback configuration."""

    enabled: bool
    max_retries: int
    retry_delay: float
    timeout_seconds: int
    fallback_models: List[str]
    auto_switch_on_timeout: bool
    auto_switch_on_error: bool


class FallbackEventResponse(BaseModel):
    """Response containing fallback event."""

    timestamp: str
    agent_id: str
    primary_model: str
    fallback_model: str
    reason: str
    error_message: Optional[str]
    retry_attempt: int


class FallbackStatisticsResponse(BaseModel):
    """Response containing fallback statistics."""

    total_events: int
    by_reason: Dict[str, int]
    by_model: Dict[str, int]
    most_reliable_model: Optional[str]
    most_problematic_model: Optional[str]


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
        priority=info.priority,
        scheduled_start_time=info.scheduled_start_time.isoformat() if info.scheduled_start_time else None,
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


# Shared Artifact Endpoints
@app.post("/api/agents/{agent_id}/artifacts/{artifact_id}/share")
async def share_artifact(agent_id: str, artifact_id: str, request: ShareArtifactRequest):
    """Share an artifact with other agents."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        agent_manager.share_artifact(
            artifact_id=artifact_id,
            owner_agent_id=agent_id,
            target_agent_ids=request.target_agent_ids,
        )
        return {"status": "shared", "artifact_id": artifact_id, "shared_with": request.target_agent_ids}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/agents/{agent_id}/artifacts/shared")
async def get_shared_artifacts(agent_id: str):
    """Get all shared artifacts for an agent."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    artifacts = agent_manager.get_shared_artifacts(agent_id)

    return [
        {
            "id": art.id,
            "name": art.name,
            "type": art.type,
            "language": art.language,
            "description": art.description,
            "content": art.content,
            "created_at": art.created_at.isoformat(),
            "shared": art.shared,
            "owner_agent_id": art.owner_agent_id,
            "shared_with": art.shared_with,
            "locked_by": art.locked_by,
            "version": art.version,
            "last_modified_by": art.last_modified_by,
        }
        for art in artifacts
    ]


@app.post("/api/agents/{agent_id}/artifacts/{artifact_id}/lock")
async def acquire_artifact_lock(agent_id: str, artifact_id: str):
    """Acquire lock on shared artifact for editing."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    success = agent_manager.acquire_artifact_lock(artifact_id, agent_id)

    if not success:
        raise HTTPException(status_code=409, detail="Artifact is locked by another agent")

    return {"status": "locked", "artifact_id": artifact_id, "locked_by": agent_id}


@app.post("/api/agents/{agent_id}/artifacts/{artifact_id}/unlock")
async def release_artifact_lock(agent_id: str, artifact_id: str):
    """Release lock on shared artifact."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent_manager.release_artifact_lock(artifact_id, agent_id)

    return {"status": "unlocked", "artifact_id": artifact_id}


@app.put("/api/agents/{agent_id}/artifacts/{artifact_id}/update")
async def update_shared_artifact(agent_id: str, artifact_id: str, request: UpdateSharedArtifactRequest):
    """Update shared artifact content (requires lock)."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        agent_manager.update_shared_artifact(
            artifact_id=artifact_id,
            agent_id=agent_id,
            new_content=request.content,
        )
        return {"status": "updated", "artifact_id": artifact_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Team Management Endpoints
@app.post("/api/teams")
async def create_team(request: CreateTeamRequest):
    """Create a new team of agents."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    team_id = agent_manager.create_team(
        name=request.name,
        description=request.description,
        shared_goal=request.shared_goal,
        lead_agent_id=request.lead_agent_id,
        member_agent_ids=request.member_agent_ids,
    )

    team = agent_manager.get_team(team_id)
    if not team:
        raise HTTPException(status_code=500, detail="Failed to create team")

    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        created_at=team.created_at.isoformat(),
        lead_agent_id=team.lead_agent_id,
        member_agent_ids=team.member_agent_ids,
        shared_goal=team.shared_goal,
        status=team.status,
    )


@app.get("/api/teams")
async def list_teams(status: Optional[str] = None):
    """List all teams, optionally filtered by status."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    teams = agent_manager.list_teams(status=status)

    return [
        TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            created_at=team.created_at.isoformat(),
            lead_agent_id=team.lead_agent_id,
            member_agent_ids=team.member_agent_ids,
            shared_goal=team.shared_goal,
            status=team.status,
        )
        for team in teams
    ]


@app.get("/api/teams/{team_id}")
async def get_team(team_id: str):
    """Get team details."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    team = agent_manager.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        created_at=team.created_at.isoformat(),
        lead_agent_id=team.lead_agent_id,
        member_agent_ids=team.member_agent_ids,
        shared_goal=team.shared_goal,
        status=team.status,
    )


@app.get("/api/teams/{team_id}/members")
async def get_team_members(team_id: str):
    """Get all agents in a team."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    team = agent_manager.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    agents = agent_manager.get_team_members(team_id)

    return {
        "team_id": team_id,
        "lead": _agent_info_to_response(agents[0]) if agents and team.lead_agent_id else None,
        "members": [_agent_info_to_response(agent) for agent in agents[1:]] if len(agents) > 1 else [],
        "total_members": len(agents),
    }


@app.post("/api/teams/{team_id}/members")
async def add_team_member(team_id: str, request: AddTeamMemberRequest):
    """Add a member to a team."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        agent_manager.add_agent_to_team(team_id, request.agent_id)
        return {"status": "added", "team_id": team_id, "agent_id": request.agent_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/teams/{team_id}/members/{agent_id}")
async def remove_team_member(team_id: str, agent_id: str):
    """Remove a member from a team."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        agent_manager.remove_agent_from_team(team_id, agent_id)
        return {"status": "removed", "team_id": team_id, "agent_id": agent_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/teams/{team_id}/disband")
async def disband_team(team_id: str):
    """Disband a team."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        agent_manager.disband_team(team_id)
        return {"status": "disbanded", "team_id": team_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Priority and Scheduling Endpoints
@app.post("/api/agents/{agent_id}/priority")
async def set_agent_priority(agent_id: str, request: SetPriorityRequest):
    """Set priority for an agent (1=highest, 10=lowest)."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        agent_manager.set_agent_priority(agent_id, request.priority)
        return {"status": "updated", "agent_id": agent_id, "priority": request.priority}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/agents/{agent_id}/schedule")
async def schedule_agent(agent_id: str, request: ScheduleAgentRequest):
    """Schedule an agent to start at a specific time."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        from datetime import datetime

        start_time = datetime.fromisoformat(request.start_time)
        agent_manager.schedule_agent(agent_id, start_time)
        return {"status": "scheduled", "agent_id": agent_id, "start_time": request.start_time}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/agents/priority-queue")
async def get_priority_queue():
    """Get list of agents sorted by priority."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agents = agent_manager.get_priority_queue()

    return [
        {
            "id": agent.id,
            "task": agent.task,
            "status": agent.status.value,
            "priority": agent.priority,
            "scheduled_start_time": agent.scheduled_start_time.isoformat() if agent.scheduled_start_time else None,
            "created_at": agent.created_at.isoformat(),
            "role": agent.role,
        }
        for agent in agents
    ]


@app.post("/api/agents/bulk-priority")
async def bulk_set_priority(request: BulkSetPriorityRequest):
    """Set priority for multiple agents at once."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    try:
        updated_count = agent_manager.bulk_set_priority(request.agent_ids, request.priority)
        return {
            "status": "updated",
            "updated_count": updated_count,
            "requested_count": len(request.agent_ids),
            "priority": request.priority,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Model Performance Tracking Endpoints
@app.get("/api/models/metrics")
async def get_all_model_metrics():
    """Get performance metrics for all tracked models."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    metrics = agent_manager.get_all_model_metrics()

    return [
        ModelMetricsResponse(
            model_name=m.model_name,
            total_requests=m.total_requests,
            successful_requests=m.successful_requests,
            failed_requests=m.failed_requests,
            success_rate=m.success_rate,
            average_response_time=m.average_response_time,
            average_tokens_per_request=m.average_tokens_per_request,
            total_tokens=m.total_tokens,
            last_used=m.last_used.isoformat() if m.last_used else None,
            error_messages=m.error_messages,
        )
        for m in metrics
    ]


@app.get("/api/models/{model_name}/metrics")
async def get_model_metrics(model_name: str):
    """Get performance metrics for a specific model."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    metrics = agent_manager.get_model_metrics(model_name)

    if not metrics:
        raise HTTPException(status_code=404, detail="Model metrics not found")

    return ModelMetricsResponse(
        model_name=metrics.model_name,
        total_requests=metrics.total_requests,
        successful_requests=metrics.successful_requests,
        failed_requests=metrics.failed_requests,
        success_rate=metrics.success_rate,
        average_response_time=metrics.average_response_time,
        average_tokens_per_request=metrics.average_tokens_per_request,
        total_tokens=metrics.total_tokens,
        last_used=metrics.last_used.isoformat() if metrics.last_used else None,
        error_messages=metrics.error_messages,
    )


@app.get("/api/models/leaderboard")
async def get_model_leaderboard(
    sort_by: str = Query("success_rate", regex="^(success_rate|avg_response_time|total_requests|avg_tokens)$"),
    limit: int = Query(10, ge=1, le=50),
):
    """Get model leaderboard sorted by a metric."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    metrics = agent_manager.get_model_leaderboard(sort_by=sort_by, limit=limit)

    return [
        ModelMetricsResponse(
            model_name=m.model_name,
            total_requests=m.total_requests,
            successful_requests=m.successful_requests,
            failed_requests=m.failed_requests,
            success_rate=m.success_rate,
            average_response_time=m.average_response_time,
            average_tokens_per_request=m.average_tokens_per_request,
            total_tokens=m.total_tokens,
            last_used=m.last_used.isoformat() if m.last_used else None,
            error_messages=m.error_messages,
        )
        for m in metrics
    ]


@app.post("/api/models/compare")
async def compare_models(model_names: List[str]):
    """Compare performance metrics across multiple models."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    comparison = agent_manager.get_model_comparison(model_names)

    return ModelComparisonResponse(
        models=comparison["models"],
        metrics=comparison["metrics"],
    )


@app.post("/api/models/{model_name}/metrics/reset")
async def reset_model_metrics(model_name: str):
    """Reset performance metrics for a specific model."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent_manager.reset_model_metrics(model_name)

    return {"status": "reset", "model_name": model_name}


@app.post("/api/models/metrics/reset-all")
async def reset_all_model_metrics():
    """Reset performance metrics for all models."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent_manager.reset_model_metrics()

    return {"status": "reset", "message": "All model metrics reset"}


# Model Selection and Discovery Endpoints
@app.get("/api/models/available")
async def get_available_models(force_refresh: bool = Query(False)):
    """Get list of available models from Ollama."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    models = await agent_manager.get_available_models(force_refresh=force_refresh)

    return {"models": models, "count": len(models)}


@app.get("/api/models/catalog")
async def get_model_catalog():
    """Get all models from the catalog with their information."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    catalog_models = agent_manager.get_all_catalog_models()

    return [
        ModelInfoResponse(
            name=m["name"],
            capabilities=m["capabilities"],
            quality_tier=m["quality_tier"],
            speed_tier=m["speed_tier"],
            strengths=m["strengths"],
            weaknesses=m["weaknesses"],
            parameter_count=m["parameter_count"],
            recommended_for=m["recommended_for"],
        )
        for m in catalog_models
    ]


@app.get("/api/models/available-with-info")
async def get_available_models_with_info():
    """Get available models with their catalog information."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    models_with_info = await agent_manager.get_available_models_with_info()

    return [
        ModelInfoResponse(
            name=m["name"],
            available=m["available"],
            capabilities=m["capabilities"],
            quality_tier=m["quality_tier"],
            speed_tier=m["speed_tier"],
            strengths=m["strengths"],
            weaknesses=m["weaknesses"],
            parameter_count=m["parameter_count"],
            recommended_for=m["recommended_for"],
        )
        for m in models_with_info
    ]


@app.get("/api/models/{model_name}/info")
async def get_model_info(model_name: str):
    """Get information about a specific model."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    model_info = agent_manager.get_model_info(model_name)

    if not model_info:
        raise HTTPException(status_code=404, detail="Model not found in catalog")

    return ModelInfoResponse(
        name=model_info["name"],
        capabilities=model_info["capabilities"],
        quality_tier=model_info["quality_tier"],
        speed_tier=model_info["speed_tier"],
        strengths=model_info["strengths"],
        weaknesses=model_info["weaknesses"],
        parameter_count=model_info["parameter_count"],
        recommended_for=model_info["recommended_for"],
    )


@app.post("/api/models/recommend")
async def recommend_model_for_task(task_description: str):
    """Get recommended model for a task."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    recommended = agent_manager.get_recommended_model_for_task(task_description)

    if not recommended:
        return ModelRecommendationResponse(
            recommended_model=None,
            reason="No specific recommendation, use default model",
        )

    model_info = agent_manager.get_model_info(recommended)
    reason = f"Recommended for this task type"
    if model_info:
        reason = f"{model_info['strengths']}"

    return ModelRecommendationResponse(
        recommended_model=recommended,
        reason=reason,
    )


# Model Fallback and Retry Endpoints
@app.get("/api/models/fallback/config")
async def get_fallback_config():
    """Get current fallback configuration."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    config = agent_manager.get_fallback_config()

    return FallbackConfigResponse(
        enabled=config["enabled"],
        max_retries=config["max_retries"],
        retry_delay=config["retry_delay"],
        timeout_seconds=config["timeout_seconds"],
        fallback_models=config["fallback_models"],
        auto_switch_on_timeout=config["auto_switch_on_timeout"],
        auto_switch_on_error=config["auto_switch_on_error"],
    )


@app.put("/api/models/fallback/config")
async def update_fallback_config(request: FallbackConfigRequest):
    """Update fallback configuration."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    # Build config dict from non-None values
    config_updates = {}
    if request.enabled is not None:
        config_updates["enabled"] = request.enabled
    if request.max_retries is not None:
        config_updates["max_retries"] = request.max_retries
    if request.retry_delay is not None:
        config_updates["retry_delay"] = request.retry_delay
    if request.timeout_seconds is not None:
        config_updates["timeout_seconds"] = request.timeout_seconds
    if request.fallback_models is not None:
        config_updates["fallback_models"] = request.fallback_models
    if request.auto_switch_on_timeout is not None:
        config_updates["auto_switch_on_timeout"] = request.auto_switch_on_timeout
    if request.auto_switch_on_error is not None:
        config_updates["auto_switch_on_error"] = request.auto_switch_on_error

    agent_manager.update_fallback_config(config_updates)

    return {"status": "updated", "config": agent_manager.get_fallback_config()}


@app.get("/api/models/fallback/events")
async def get_fallback_events(
    agent_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """Get fallback event history."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    events = agent_manager.get_fallback_events(agent_id=agent_id, limit=limit)

    return [
        FallbackEventResponse(
            timestamp=event.timestamp.isoformat(),
            agent_id=event.agent_id,
            primary_model=event.primary_model,
            fallback_model=event.fallback_model,
            reason=event.reason,
            error_message=event.error_message,
            retry_attempt=event.retry_attempt,
        )
        for event in events
    ]


@app.get("/api/models/fallback/statistics")
async def get_fallback_statistics():
    """Get statistics about fallback events."""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    stats = agent_manager.get_fallback_statistics()

    return FallbackStatisticsResponse(
        total_events=stats["total_events"],
        by_reason=stats["by_reason"],
        by_model=stats["by_model"],
        most_reliable_model=stats["most_reliable_model"],
        most_problematic_model=stats["most_problematic_model"],
    )


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

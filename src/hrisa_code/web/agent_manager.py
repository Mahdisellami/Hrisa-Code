"""Web-based agent manager for orchestrating multiple GenAI agents."""

import asyncio
import uuid
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from collections import deque

from hrisa_code.core.config import Config
from hrisa_code.core.planning.agent import AgentLoop
from hrisa_code.core.conversation import ConversationManager, OllamaClient
from hrisa_code.core.conversation.ollama_client import OllamaConfig
from hrisa_code.web.roles import get_role_system_prompt


class AgentStatus(Enum):
    """Status of a web-managed agent."""

    PENDING = "pending"
    RUNNING = "running"
    STUCK = "stuck"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentState(Enum):
    """Detailed state within agent execution (state machine)."""

    INITIALIZING = "initializing"
    PLANNING = "planning"
    EXECUTING = "executing"
    THINKING = "thinking"
    TOOL_USE = "tool_use"
    REFLECTING = "reflecting"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    FINALIZING = "finalizing"


@dataclass
class AgentMessage:
    """A message in the agent's conversation."""

    timestamp: datetime
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None


@dataclass
class AgentLog:
    """A log entry from agent execution."""

    timestamp: datetime
    level: str  # 'info', 'error', 'debug', 'tool', 'iteration'
    message: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentArtifact:
    """An artifact produced by an agent."""

    id: str
    name: str
    type: str  # 'code', 'document', 'data', 'diagram', 'file', 'json', 'markdown'
    content: str
    created_at: datetime
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None  # For file artifacts
    language: Optional[str] = None  # For code artifacts (python, javascript, etc.)
    # Shared artifact fields
    shared: bool = False  # Whether this artifact is shared with other agents
    shared_with: List[str] = field(default_factory=list)  # Agent IDs this is shared with
    owner_agent_id: Optional[str] = None  # Original creator agent
    locked_by: Optional[str] = None  # Agent ID that has lock for editing
    version: int = 1  # Version number for tracking changes
    last_modified_by: Optional[str] = None  # Last agent to modify


@dataclass
class InterAgentMessage:
    """A message sent from one agent to another."""

    id: str
    timestamp: datetime
    from_agent_id: str
    to_agent_id: str
    message_type: str  # 'request', 'response', 'notification', 'question'
    content: str
    metadata: Optional[Dict[str, Any]] = None
    in_reply_to: Optional[str] = None  # ID of message this is replying to
    read: bool = False


@dataclass
class AgentStateTransition:
    """A state transition in the agent's execution."""

    timestamp: datetime
    from_state: Optional[str]
    to_state: str
    reason: Optional[str] = None


@dataclass
class AgentMemory:
    """Memory system for agent context and decisions."""

    decisions: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    intermediate_outputs: List[Dict[str, Any]] = field(default_factory=list)
    state_transitions: List[AgentStateTransition] = field(default_factory=list)
    working_memory: List[str] = field(default_factory=list)  # Short-term memory


@dataclass
class AgentProgress:
    """Progress information for an agent."""

    total_steps: int = 0
    completed_steps: int = 0
    current_step: Optional[str] = None
    tool_calls: int = 0
    loop_detections: int = 0
    errors: int = 0
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class AgentInfo:
    """Complete information about a web-managed agent."""

    id: str
    task: str
    status: AgentStatus
    created_at: datetime
    working_dir: Path
    model: str
    progress: AgentProgress
    messages: List[AgentMessage]
    logs: List[AgentLog] = field(default_factory=list)
    artifacts: List[AgentArtifact] = field(default_factory=list)
    role: Optional[str] = None
    output: str = ""
    error: Optional[str] = None
    stuck_reason: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parent_agent_id: Optional[str] = None  # For tracking artifact inheritance
    child_agent_ids: List[str] = field(default_factory=list)  # Children in workflow
    workflow_step: int = 0  # Position in workflow (0=root, 1=first child, etc.)
    auto_start_next: Optional[str] = None  # Next agent ID to auto-start on completion
    current_state: AgentState = AgentState.INITIALIZING  # State machine
    memory: AgentMemory = field(default_factory=AgentMemory)  # Agent memory
    inter_agent_messages: List[InterAgentMessage] = field(default_factory=list)  # Messages to/from other agents


class WebAgentManager:
    """Manages multiple GenAI agents with web UI integration.

    This manager orchestrates multiple concurrent agents, tracks their progress,
    detects when they get stuck, and provides interfaces for user intervention.
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        max_concurrent: int = 5,
        stuck_threshold_seconds: int = 120,
    ):
        """Initialize the web agent manager.

        Args:
            config: Configuration for agents (uses default if None)
            max_concurrent: Maximum number of concurrent agents
            stuck_threshold_seconds: Seconds without activity before marking as stuck
        """
        self.config = config or Config.get_default()
        self.max_concurrent = max_concurrent
        self.stuck_threshold = stuck_threshold_seconds

        self.agents: Dict[str, AgentInfo] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        self.agent_instances: Dict[str, AgentLoop] = {}

        # Callbacks for web UI updates
        self.status_callbacks: List[Callable[[str, AgentInfo], None]] = []
        self.message_callbacks: List[Callable[[str, AgentMessage], None]] = []
        self.stuck_callbacks: List[Callable[[str, str], None]] = []
        self.stream_callbacks: List[Callable[[str, str], None]] = []  # New: for streaming responses

        # Background task for monitoring
        self.monitor_task: Optional[asyncio.Task] = None
        self.running = False

        # Session management
        self.sessions_dir = Path.home() / ".hrisa" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Start the agent manager and monitoring."""
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_agents())

    async def stop(self) -> None:
        """Stop the agent manager and cancel all agents."""
        self.running = False

        # Cancel all running agents
        for agent_id in list(self.agent_tasks.keys()):
            await self.cancel_agent(agent_id)

        # Cancel monitor task
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

    def add_status_callback(self, callback: Callable[[str, AgentInfo], None]) -> None:
        """Add a callback for status updates.

        Args:
            callback: Function called with (agent_id, agent_info) on status change
        """
        self.status_callbacks.append(callback)

    def add_message_callback(self, callback: Callable[[str, AgentMessage], None]) -> None:
        """Add a callback for new messages.

        Args:
            callback: Function called with (agent_id, message) on new message
        """
        self.message_callbacks.append(callback)

    def add_stuck_callback(self, callback: Callable[[str, str], None]) -> None:
        """Add a callback for stuck detection.

        Args:
            callback: Function called with (agent_id, reason) when stuck
        """
        self.stuck_callbacks.append(callback)

    def add_stream_callback(self, callback: Callable[[str, str], None]) -> None:
        """Add a callback for streaming response chunks.

        Args:
            callback: Function called with (agent_id, chunk) for each response chunk
        """
        self.stream_callbacks.append(callback)

    async def create_agent(
        self,
        task: str,
        working_dir: Optional[Path] = None,
        model: Optional[str] = None,
        tags: Optional[List[str]] = None,
        role: Optional[str] = None,
        parent_agent_id: Optional[str] = None,
    ) -> str:
        """Create a new agent for a task.

        Args:
            task: The task description for the agent
            working_dir: Working directory (uses cwd if None)
            model: Ollama model to use (uses config default if None)
            tags: Optional tags for categorization
            role: Agent role/persona (e.g., 'architect', 'coder', 'tester')
            parent_agent_id: Parent agent to inherit artifacts from

        Returns:
            Agent ID

        Raises:
            RuntimeError: If max concurrent agents reached
        """
        # Check concurrent limit
        running_count = sum(
            1 for info in self.agents.values() if info.status == AgentStatus.RUNNING
        )
        if running_count >= self.max_concurrent:
            raise RuntimeError(
                f"Maximum concurrent agents ({self.max_concurrent}) reached"
            )

        # Generate agent ID
        agent_id = str(uuid.uuid4())

        # Create agent info
        agent_info = AgentInfo(
            id=agent_id,
            task=task,
            status=AgentStatus.PENDING,
            created_at=datetime.now(),
            working_dir=working_dir or Path.cwd(),
            model=model or self.config.model.name,
            progress=AgentProgress(),
            messages=[],
            role=role or "general",
            tags=tags or [],
            parent_agent_id=parent_agent_id,
        )

        # Inherit artifacts from parent agent if specified
        if parent_agent_id and parent_agent_id in self.agents:
            parent_agent = self.agents[parent_agent_id]
            agent_info.artifacts = [
                AgentArtifact(
                    id=artifact.id,
                    name=artifact.name,
                    type=artifact.type,
                    content=artifact.content,
                    created_at=artifact.created_at,
                    description=f"Inherited from parent agent {parent_agent_id[:8]}",
                    metadata=artifact.metadata,
                    file_path=artifact.file_path,
                    language=artifact.language,
                )
                for artifact in parent_agent.artifacts
            ]

        self.agents[agent_id] = agent_info

        # Notify callbacks
        await self._notify_status_change(agent_id, agent_info)

        return agent_id

    async def start_agent(self, agent_id: str) -> None:
        """Start an agent's execution.

        Args:
            agent_id: The agent ID

        Raises:
            ValueError: If agent not found or already running
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent_info = self.agents[agent_id]

        if agent_info.status == AgentStatus.RUNNING:
            raise ValueError(f"Agent {agent_id} is already running")

        # Update status
        agent_info.status = AgentStatus.RUNNING
        agent_info.progress.last_activity = datetime.now()
        await self._notify_status_change(agent_id, agent_info)

        # Create agent instance with custom callbacks
        # Create OllamaConfig and ConversationManager with agent-specific model and role
        ollama_config = OllamaConfig(
            model=agent_info.model or self.config.model.name,
            host=self.config.ollama.host,
            temperature=self.config.model.temperature,
            top_p=self.config.model.top_p,
            top_k=self.config.model.top_k,
        )

        # Get role-specific system prompt
        role_system_prompt = get_role_system_prompt(agent_info.role or "general")

        conversation_manager = ConversationManager(
            ollama_config=ollama_config,
            working_directory=agent_info.working_dir,
            system_prompt=role_system_prompt,
        )
        agent = AgentLoop(
            conversation_manager=conversation_manager,
            max_iterations=15,
            enable_reflection=True,
            enable_planning=True,
        )

        # Monkey-patch agent to capture messages and progress
        original_process_message = agent._process_message if hasattr(agent, '_process_message') else None

        async def intercepted_process_message(*args, **kwargs):
            # Update activity timestamp
            agent_info.progress.last_activity = datetime.now()
            agent_info.progress.total_steps += 1

            # Call original if exists
            if original_process_message:
                result = await original_process_message(*args, **kwargs)

                # Capture message
                if result:
                    message = AgentMessage(
                        timestamp=datetime.now(),
                        role="assistant",
                        content=str(result.get("content", "")),
                        tool_calls=result.get("tool_calls"),
                    )
                    agent_info.messages.append(message)
                    await self._notify_message(agent_id, message)

                return result

        if original_process_message:
            agent._process_message = intercepted_process_message

        self.agent_instances[agent_id] = agent

        # Start agent task
        task = asyncio.create_task(self._run_agent(agent_id, agent))
        self.agent_tasks[agent_id] = task

    async def _add_log(self, agent_id: str, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a log entry for an agent.

        Args:
            agent_id: The agent ID
            level: Log level
            message: Log message
            metadata: Optional metadata
        """
        agent_info = self.agents.get(agent_id)
        if not agent_info:
            return

        log = AgentLog(
            timestamp=datetime.now(),
            level=level,
            message=message,
            metadata=metadata,
        )
        agent_info.logs.append(log)

    async def _transition_state(
        self,
        agent_id: str,
        new_state: AgentState,
        reason: Optional[str] = None,
    ) -> None:
        """Transition agent to a new state and record it.

        Args:
            agent_id: The agent ID
            new_state: The new state to transition to
            reason: Optional reason for the transition
        """
        agent_info = self.agents.get(agent_id)
        if not agent_info:
            return

        # Record transition
        transition = AgentStateTransition(
            timestamp=datetime.now(),
            from_state=agent_info.current_state.value if agent_info.current_state else None,
            to_state=new_state.value,
            reason=reason,
        )
        agent_info.memory.state_transitions.append(transition)
        agent_info.current_state = new_state

        # Log state change
        await self._add_log(
            agent_id,
            "info",
            f"State transition: {transition.from_state} → {new_state.value}" + (f" ({reason})" if reason else ""),
            {"transition": {"from": transition.from_state, "to": new_state.value}},
        )

    async def _add_decision(
        self,
        agent_id: str,
        decision_type: str,
        description: str,
        rationale: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a decision made by the agent.

        Args:
            agent_id: The agent ID
            decision_type: Type of decision (e.g., 'tool_selection', 'approach', 'verification')
            description: Description of the decision
            rationale: Optional rationale for the decision
            context: Optional context data
        """
        agent_info = self.agents.get(agent_id)
        if not agent_info:
            return

        decision = {
            "timestamp": datetime.now().isoformat(),
            "type": decision_type,
            "description": description,
            "rationale": rationale,
            "context": context or {},
        }
        agent_info.memory.decisions.append(decision)

    async def _add_intermediate_output(
        self,
        agent_id: str,
        output_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an intermediate output from the agent.

        Args:
            agent_id: The agent ID
            output_type: Type of output (e.g., 'analysis', 'plan', 'code_snippet')
            content: The output content
            metadata: Optional metadata
        """
        agent_info = self.agents.get(agent_id)
        if not agent_info:
            return

        output = {
            "timestamp": datetime.now().isoformat(),
            "type": output_type,
            "content": content,
            "metadata": metadata or {},
        }
        agent_info.memory.intermediate_outputs.append(output)

    async def _update_working_memory(
        self,
        agent_id: str,
        item: str,
        max_items: int = 10,
    ) -> None:
        """Update the agent's working memory (short-term memory).

        Args:
            agent_id: The agent ID
            item: Memory item to add
            max_items: Maximum number of items to keep (FIFO)
        """
        agent_info = self.agents.get(agent_id)
        if not agent_info:
            return

        agent_info.memory.working_memory.append(item)

        # Keep only the last max_items
        if len(agent_info.memory.working_memory) > max_items:
            agent_info.memory.working_memory = agent_info.memory.working_memory[-max_items:]

    async def add_artifact(
        self,
        agent_id: str,
        name: str,
        type: str,
        content: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str:
        """Add an artifact for an agent.

        Args:
            agent_id: The agent ID
            name: Artifact name
            type: Artifact type (code, document, data, etc.)
            content: Artifact content
            description: Optional description
            metadata: Optional metadata
            file_path: Optional file path
            language: Optional language for code artifacts

        Returns:
            Artifact ID
        """
        agent_info = self.agents.get(agent_id)
        if not agent_info:
            raise ValueError(f"Agent {agent_id} not found")

        artifact_id = str(uuid.uuid4())
        artifact = AgentArtifact(
            id=artifact_id,
            name=name,
            type=type,
            content=content,
            created_at=datetime.now(),
            description=description,
            metadata=metadata,
            file_path=file_path,
            language=language,
        )
        agent_info.artifacts.append(artifact)

        await self._add_log(
            agent_id,
            "info",
            f"Created artifact: {name} ({type})",
            {"artifact_id": artifact_id},
        )

        return artifact_id

    def get_artifacts(self, agent_id: str) -> List[AgentArtifact]:
        """Get all artifacts for an agent.

        Args:
            agent_id: The agent ID

        Returns:
            List of artifacts
        """
        agent_info = self.agents.get(agent_id)
        if not agent_info:
            return []
        return agent_info.artifacts

    async def _run_agent(self, agent_id: str, agent: AgentLoop) -> None:
        """Run an agent until completion or error.

        Args:
            agent_id: The agent ID
            agent: The agent instance
        """
        agent_info = self.agents[agent_id]

        try:
            # Transition to PLANNING state
            await self._transition_state(agent_id, AgentState.PLANNING, "Analyzing task requirements")

            # Log agent start
            await self._add_log(agent_id, "info", f"Agent started with role: {agent_info.role or 'general'}")
            await self._add_log(agent_id, "info", f"Using model: {agent_info.model}")
            await self._add_log(agent_id, "info", f"Working directory: {agent_info.working_dir}")

            # Store initial context in memory
            agent_info.memory.context["task"] = agent_info.task
            agent_info.memory.context["role"] = agent_info.role or "general"
            agent_info.memory.context["model"] = agent_info.model
            agent_info.memory.context["working_dir"] = str(agent_info.working_dir)
            agent_info.memory.context["started_at"] = datetime.now().isoformat()

            # Add initial user message
            initial_message = AgentMessage(
                timestamp=datetime.now(),
                role="user",
                content=agent_info.task,
            )
            agent_info.messages.append(initial_message)
            await self._notify_message(agent_id, initial_message)

            await self._add_log(agent_id, "info", "Executing task...")

            # Transition to EXECUTING state
            await self._transition_state(agent_id, AgentState.EXECUTING, "Beginning task execution")
            await self._update_working_memory(agent_id, f"Started executing: {agent_info.task[:100]}")

            # Run agent
            result = await agent.execute_task(agent_info.task)

            # Transition to FINALIZING state
            await self._transition_state(agent_id, AgentState.FINALIZING, "Completing task and generating output")

            # Store final output in intermediate outputs
            await self._add_intermediate_output(
                agent_id,
                "final_output",
                result,
                {"status": "success", "completed_steps": agent_info.progress.total_steps},
            )

            # Store output
            agent_info.output = result
            agent_info.status = AgentStatus.COMPLETED
            agent_info.progress.completed_steps = agent_info.progress.total_steps

            # Update memory context
            agent_info.memory.context["completed_at"] = datetime.now().isoformat()
            agent_info.memory.context["final_status"] = "completed"

            await self._add_log(agent_id, "info", "Task completed successfully")

            # Auto-start next agent in workflow if configured
            if agent_info.auto_start_next:
                next_agent_id = agent_info.auto_start_next
                await self._add_log(agent_id, "info", f"Auto-starting next agent in workflow: {next_agent_id[:8]}")
                try:
                    await self.start_agent(next_agent_id)
                except Exception as chain_error:
                    await self._add_log(agent_id, "error", f"Failed to start next agent: {str(chain_error)}")

        except Exception as e:
            agent_info.status = AgentStatus.FAILED
            agent_info.error = str(e)

            # Update memory with error context
            agent_info.memory.context["failed_at"] = datetime.now().isoformat()
            agent_info.memory.context["final_status"] = "failed"
            agent_info.memory.context["error"] = str(e)

            await self._add_log(agent_id, "error", f"Agent failed: {str(e)}")

        finally:
            # Cleanup
            if agent_id in self.agent_tasks:
                del self.agent_tasks[agent_id]
            if agent_id in self.agent_instances:
                del self.agent_instances[agent_id]

            # Notify
            await self._notify_status_change(agent_id, agent_info)

    async def send_instruction(self, agent_id: str, instruction: str) -> None:
        """Send an instruction to a running or stuck agent.

        Args:
            agent_id: The agent ID
            instruction: The user instruction

        Raises:
            ValueError: If agent not found or not in correct state
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent_info = self.agents[agent_id]

        if agent_info.status not in [
            AgentStatus.RUNNING,
            AgentStatus.STUCK,
            AgentStatus.WAITING_INPUT,
        ]:
            raise ValueError(
                f"Agent {agent_id} is {agent_info.status.value}, cannot send instruction"
            )

        # Add user message
        message = AgentMessage(
            timestamp=datetime.now(),
            role="user",
            content=instruction,
        )
        agent_info.messages.append(message)
        await self._notify_message(agent_id, message)

        # If stuck, resume agent
        if agent_info.status == AgentStatus.STUCK:
            agent_info.status = AgentStatus.RUNNING
            agent_info.stuck_reason = None
            agent_info.progress.last_activity = datetime.now()
            await self._notify_status_change(agent_id, agent_info)

        # Send instruction to agent instance
        if agent_id in self.agent_instances:
            agent = self.agent_instances[agent_id]
            # Add message to agent's conversation
            if hasattr(agent, 'conversation_manager'):
                agent.conversation_manager.messages.append({
                    "role": "user",
                    "content": instruction,
                })

    async def cancel_agent(self, agent_id: str) -> None:
        """Cancel a running agent.

        Args:
            agent_id: The agent ID

        Raises:
            ValueError: If agent not found
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent_info = self.agents[agent_id]

        # Cancel task if running
        if agent_id in self.agent_tasks:
            task = self.agent_tasks[agent_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Update status
        agent_info.status = AgentStatus.CANCELLED
        await self._notify_status_change(agent_id, agent_info)

    async def create_chained_agent(
        self,
        parent_agent_id: str,
        task: str,
        role: Optional[str] = None,
        auto_start: bool = False,
        model: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Create a chained agent that inherits from a parent.

        Args:
            parent_agent_id: ID of parent agent to chain from
            task: Task for the new agent
            role: Agent role (defaults to parent's role if not specified)
            auto_start: Whether to auto-start this agent when parent completes
            model: Model to use (defaults to parent's model)
            tags: Tags for the agent

        Returns:
            New agent ID

        Raises:
            ValueError: If parent agent not found
        """
        parent_agent = self.get_agent(parent_agent_id)
        if not parent_agent:
            raise ValueError(f"Parent agent {parent_agent_id} not found")

        # Inherit settings from parent if not specified
        if not role:
            role = parent_agent.role
        if not model:
            model = parent_agent.model
        if not tags:
            tags = parent_agent.tags.copy()

        # Create the chained agent
        child_agent_id = await self.create_agent(
            task=task,
            working_dir=parent_agent.working_dir,
            model=model,
            tags=tags,
            role=role,
            parent_agent_id=parent_agent_id,
        )

        # Update parent's child list
        parent_agent.child_agent_ids.append(child_agent_id)

        # Update child's workflow step
        child_agent = self.agents[child_agent_id]
        child_agent.workflow_step = parent_agent.workflow_step + 1

        # Set up auto-start if requested
        if auto_start:
            parent_agent.auto_start_next = child_agent_id
            await self._add_log(
                parent_agent_id,
                "info",
                f"Configured to auto-start child agent {child_agent_id[:8]} on completion",
            )

        await self._add_log(
            parent_agent_id,
            "info",
            f"Created chained agent {child_agent_id[:8]} with role: {role}",
        )

        await self._add_log(
            child_agent_id,
            "info",
            f"Chained from parent agent {parent_agent_id[:8]} (workflow step {child_agent.workflow_step})",
        )

        return child_agent_id

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent information.

        Args:
            agent_id: The agent ID

        Returns:
            Agent info or None if not found
        """
        return self.agents.get(agent_id)

    def list_agents(
        self,
        status: Optional[AgentStatus] = None,
        tags: Optional[List[str]] = None,
    ) -> List[AgentInfo]:
        """List all agents, optionally filtered.

        Args:
            status: Filter by status
            tags: Filter by tags (agents must have all tags)

        Returns:
            List of agent info
        """
        agents = list(self.agents.values())

        if status:
            agents = [a for a in agents if a.status == status]

        if tags:
            agents = [
                a for a in agents if all(tag in a.tags for tag in tags)
            ]

        # Sort by creation time (newest first)
        agents.sort(key=lambda a: a.created_at, reverse=True)

        return agents

    def get_workflow_chain(self, agent_id: str) -> List[AgentInfo]:
        """Get the full workflow chain for an agent (root to leaves).

        Args:
            agent_id: Agent ID to get workflow for

        Returns:
            List of agents in workflow order (parent first, then children)
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return []

        # Find root agent (no parent)
        root = agent
        while root.parent_agent_id:
            parent = self.get_agent(root.parent_agent_id)
            if parent:
                root = parent
            else:
                break

        # Build chain from root using BFS
        chain = []
        queue = [root]

        while queue:
            current = queue.pop(0)
            chain.append(current)

            # Add children in order
            for child_id in current.child_agent_ids:
                child = self.get_agent(child_id)
                if child:
                    queue.append(child)

        return chain

    def get_children(self, agent_id: str) -> List[AgentInfo]:
        """Get direct children of an agent.

        Args:
            agent_id: Parent agent ID

        Returns:
            List of child agents
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return []

        children = []
        for child_id in agent.child_agent_ids:
            child = self.get_agent(child_id)
            if child:
                children.append(child)

        return children

    async def _monitor_agents(self) -> None:
        """Background task to monitor agents for stuck conditions."""
        while self.running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                now = datetime.now()

                for agent_id, agent_info in self.agents.items():
                    if agent_info.status != AgentStatus.RUNNING:
                        continue

                    # Check if stuck (no activity for threshold)
                    time_since_activity = (
                        now - agent_info.progress.last_activity
                    ).total_seconds()

                    if time_since_activity > self.stuck_threshold:
                        agent_info.status = AgentStatus.STUCK
                        agent_info.stuck_reason = (
                            f"No activity for {int(time_since_activity)} seconds"
                        )

                        # Notify callbacks
                        await self._notify_status_change(agent_id, agent_info)
                        await self._notify_stuck(agent_id, agent_info.stuck_reason)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue monitoring
                print(f"Error in agent monitoring: {e}")

    async def _notify_status_change(self, agent_id: str, agent_info: AgentInfo) -> None:
        """Notify status callbacks.

        Args:
            agent_id: The agent ID
            agent_info: The agent info
        """
        for callback in self.status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent_id, agent_info)
                else:
                    callback(agent_id, agent_info)
            except Exception as e:
                print(f"Error in status callback: {e}")

    async def _notify_message(self, agent_id: str, message: AgentMessage) -> None:
        """Notify message callbacks.

        Args:
            agent_id: The agent ID
            message: The message
        """
        for callback in self.message_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent_id, message)
                else:
                    callback(agent_id, message)
            except Exception as e:
                print(f"Error in message callback: {e}")

    async def _notify_stuck(self, agent_id: str, reason: str) -> None:
        """Notify stuck callbacks.

        Args:
            agent_id: The agent ID
            reason: The stuck reason
        """
        for callback in self.stuck_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent_id, reason)
                else:
                    callback(agent_id, reason)
            except Exception as e:
                print(f"Error in stuck callback: {e}")

    async def _notify_stream(self, agent_id: str, chunk: str) -> None:
        """Notify stream callbacks with response chunk.

        Args:
            agent_id: The agent ID
            chunk: Response chunk
        """
        for callback in self.stream_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent_id, chunk)
                else:
                    callback(agent_id, chunk)
            except Exception as e:
                print(f"Error in stream callback: {e}")

    # Session Management Methods
    def save_session(
        self,
        name: str,
        description: Optional[str] = None,
        agent_ids: Optional[List[str]] = None,
    ) -> str:
        """Save current session to disk.

        Args:
            name: Session name
            description: Optional description
            agent_ids: List of agent IDs to save (all if None)

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())[:8]

        # Determine which agents to save
        agents_to_save = agent_ids or list(self.agents.keys())

        # Serialize agents
        session_data = {
            "id": session_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "agents": {}
        }

        for agent_id in agents_to_save:
            agent_info = self.agents.get(agent_id)
            if not agent_info:
                continue

            # Convert to dict (handling dataclasses and enums)
            agent_dict = {
                "id": agent_info.id,
                "task": agent_info.task,
                "status": agent_info.status.value,
                "created_at": agent_info.created_at.isoformat(),
                "working_dir": agent_info.working_dir,
                "model": agent_info.model,
                "role": agent_info.role,
                "tags": agent_info.tags,
                "parent_agent_id": agent_info.parent_agent_id,
                "child_agent_ids": agent_info.child_agent_ids,
                "workflow_step": agent_info.workflow_step,
                "auto_start_next": agent_info.auto_start_next,
                "current_state": agent_info.current_state.value if agent_info.current_state else None,
                "messages": [
                    {
                        "timestamp": msg.timestamp.isoformat(),
                        "role": msg.role,
                        "content": msg.content,
                        "tool_calls": msg.tool_calls,
                        "tool_results": msg.tool_results,
                    }
                    for msg in agent_info.messages
                ],
                "logs": [
                    {
                        "timestamp": log.timestamp.isoformat(),
                        "level": log.level,
                        "message": log.message,
                        "metadata": log.metadata,
                    }
                    for log in agent_info.logs
                ],
                "artifacts": [
                    {
                        "id": art.id,
                        "name": art.name,
                        "type": art.type,
                        "content": art.content,
                        "created_at": art.created_at.isoformat(),
                        "description": art.description,
                        "metadata": art.metadata,
                        "file_path": art.file_path,
                        "language": art.language,
                    }
                    for art in agent_info.artifacts
                ],
                "memory": {
                    "decisions": agent_info.memory.decisions,
                    "context": agent_info.memory.context,
                    "intermediate_outputs": agent_info.memory.intermediate_outputs,
                    "working_memory": agent_info.memory.working_memory,
                    "state_transitions": [
                        {
                            "timestamp": st.timestamp.isoformat(),
                            "from_state": st.from_state,
                            "to_state": st.to_state,
                            "reason": st.reason,
                        }
                        for st in agent_info.memory.state_transitions
                    ],
                },
            }

            session_data["agents"][agent_id] = agent_dict

        # Save to file
        session_file = self.sessions_dir / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        return session_id

    def load_session(self, session_id: str) -> None:
        """Load a saved session from disk.

        Args:
            session_id: Session ID to load
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        with open(session_file, 'r') as f:
            session_data = json.load(f)

        # Clear current agents
        self.agents.clear()

        # Restore agents
        for agent_id, agent_dict in session_data["agents"].items():
            # Reconstruct agent info
            agent_info = AgentInfo(
                id=agent_dict["id"],
                task=agent_dict["task"],
                status=AgentStatus(agent_dict["status"]),
                created_at=datetime.fromisoformat(agent_dict["created_at"]),
                working_dir=agent_dict["working_dir"],
                model=agent_dict["model"],
                role=agent_dict.get("role"),
                tags=agent_dict.get("tags", []),
                parent_agent_id=agent_dict.get("parent_agent_id"),
                child_agent_ids=agent_dict.get("child_agent_ids", []),
                workflow_step=agent_dict.get("workflow_step", 0),
                auto_start_next=agent_dict.get("auto_start_next"),
                current_state=AgentState(agent_dict["current_state"]) if agent_dict.get("current_state") else AgentState.INITIALIZING,
                messages=[
                    AgentMessage(
                        timestamp=datetime.fromisoformat(msg["timestamp"]),
                        role=msg["role"],
                        content=msg["content"],
                        tool_calls=msg.get("tool_calls"),
                        tool_results=msg.get("tool_results"),
                    )
                    for msg in agent_dict.get("messages", [])
                ],
                logs=[
                    AgentLog(
                        timestamp=datetime.fromisoformat(log["timestamp"]),
                        level=log["level"],
                        message=log["message"],
                        metadata=log.get("metadata"),
                    )
                    for log in agent_dict.get("logs", [])
                ],
                artifacts=[
                    AgentArtifact(
                        id=art["id"],
                        name=art["name"],
                        type=art["type"],
                        content=art["content"],
                        created_at=datetime.fromisoformat(art["created_at"]),
                        description=art.get("description"),
                        metadata=art.get("metadata"),
                        file_path=art.get("file_path"),
                        language=art.get("language"),
                    )
                    for art in agent_dict.get("artifacts", [])
                ],
                memory=AgentMemory(
                    decisions=agent_dict.get("memory", {}).get("decisions", []),
                    context=agent_dict.get("memory", {}).get("context", {}),
                    intermediate_outputs=agent_dict.get("memory", {}).get("intermediate_outputs", []),
                    working_memory=agent_dict.get("memory", {}).get("working_memory", []),
                    state_transitions=[
                        AgentStateTransition(
                            timestamp=datetime.fromisoformat(st["timestamp"]),
                            from_state=st.get("from_state"),
                            to_state=st["to_state"],
                            reason=st.get("reason"),
                        )
                        for st in agent_dict.get("memory", {}).get("state_transitions", [])
                    ],
                ),
            )

            self.agents[agent_id] = agent_info

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions.

        Returns:
            List of session info dicts
        """
        sessions = []
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    sessions.append({
                        "id": session_data["id"],
                        "name": session_data["name"],
                        "description": session_data.get("description"),
                        "created_at": session_data["created_at"],
                        "agent_count": len(session_data["agents"]),
                        "total_artifacts": sum(
                            len(agent.get("artifacts", []))
                            for agent in session_data["agents"].values()
                        ),
                    })
            except Exception as e:
                print(f"Error loading session {session_file}: {e}")

        return sorted(sessions, key=lambda s: s["created_at"], reverse=True)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session info.

        Args:
            session_id: Session ID

        Returns:
            Session info dict or None
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return None

        with open(session_file, 'r') as f:
            session_data = json.load(f)
            return {
                "id": session_data["id"],
                "name": session_data["name"],
                "description": session_data.get("description"),
                "created_at": session_data["created_at"],
                "agent_count": len(session_data["agents"]),
                "total_artifacts": sum(
                    len(agent.get("artifacts", []))
                    for agent in session_data["agents"].values()
                ),
            }

    def delete_session(self, session_id: str) -> None:
        """Delete a saved session.

        Args:
            session_id: Session ID to delete
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        session_file.unlink()

    # Inter-Agent Messaging Methods
    def send_agent_message(
        self,
        from_agent_id: str,
        to_agent_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        in_reply_to: Optional[str] = None,
    ) -> str:
        """Send a message from one agent to another.

        Args:
            from_agent_id: Sender agent ID
            to_agent_id: Recipient agent ID
            message_type: Type of message (request, response, notification, question)
            content: Message content
            metadata: Optional metadata
            in_reply_to: Optional message ID this is replying to

        Returns:
            Message ID
        """
        from_agent = self.get_agent(from_agent_id)
        to_agent = self.get_agent(to_agent_id)

        if not from_agent:
            raise ValueError(f"Sender agent {from_agent_id} not found")
        if not to_agent:
            raise ValueError(f"Recipient agent {to_agent_id} not found")

        message_id = str(uuid.uuid4())[:8]
        message = InterAgentMessage(
            id=message_id,
            timestamp=datetime.now(),
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=message_type,
            content=content,
            metadata=metadata,
            in_reply_to=in_reply_to,
            read=False,
        )

        # Add to both agents' message lists
        from_agent.inter_agent_messages.append(message)
        to_agent.inter_agent_messages.append(message)

        return message_id

    def get_agent_messages(
        self,
        agent_id: str,
        filter_type: Optional[str] = None,
        unread_only: bool = False,
    ) -> List[InterAgentMessage]:
        """Get inter-agent messages for an agent.

        Args:
            agent_id: Agent ID
            filter_type: Optional message type filter
            unread_only: Only return unread messages

        Returns:
            List of messages
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return []

        messages = agent.inter_agent_messages

        # Filter by type
        if filter_type:
            messages = [m for m in messages if m.message_type == filter_type]

        # Filter by read status
        if unread_only:
            messages = [m for m in messages if not m.read and m.to_agent_id == agent_id]

        return messages

    def mark_message_read(self, agent_id: str, message_id: str) -> None:
        """Mark a message as read.

        Args:
            agent_id: Agent ID
            message_id: Message ID
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return

        for message in agent.inter_agent_messages:
            if message.id == message_id and message.to_agent_id == agent_id:
                message.read = True
                break

    def get_conversation_thread(
        self,
        agent_id: str,
        other_agent_id: str,
    ) -> List[InterAgentMessage]:
        """Get full conversation thread between two agents.

        Args:
            agent_id: First agent ID
            other_agent_id: Second agent ID

        Returns:
            List of messages sorted by timestamp
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return []

        # Get messages between these two agents
        messages = [
            m for m in agent.inter_agent_messages
            if (m.from_agent_id == agent_id and m.to_agent_id == other_agent_id)
            or (m.from_agent_id == other_agent_id and m.to_agent_id == agent_id)
        ]

        # Sort by timestamp
        messages.sort(key=lambda m: m.timestamp)

        return messages

    # Shared Artifact Methods
    def share_artifact(
        self,
        artifact_id: str,
        owner_agent_id: str,
        target_agent_ids: List[str],
    ) -> None:
        """Share an artifact with other agents.

        Args:
            artifact_id: Artifact ID to share
            owner_agent_id: Owner agent ID
            target_agent_ids: List of agent IDs to share with
        """
        owner = self.get_agent(owner_agent_id)
        if not owner:
            raise ValueError(f"Owner agent {owner_agent_id} not found")

        # Find artifact
        artifact = next((a for a in owner.artifacts if a.id == artifact_id), None)
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")

        # Mark as shared
        artifact.shared = True
        artifact.owner_agent_id = owner_agent_id
        artifact.shared_with = list(set(artifact.shared_with + target_agent_ids))

        # Add to target agents' artifacts
        for target_id in target_agent_ids:
            target = self.get_agent(target_id)
            if target and target_id != owner_agent_id:
                # Check if already has this artifact
                if not any(a.id == artifact_id for a in target.artifacts):
                    target.artifacts.append(artifact)

    def get_shared_artifacts(
        self,
        agent_id: str,
    ) -> List[AgentArtifact]:
        """Get all artifacts shared with or by an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of shared artifacts
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return []

        return [a for a in agent.artifacts if a.shared]

    def acquire_artifact_lock(
        self,
        artifact_id: str,
        agent_id: str,
    ) -> bool:
        """Acquire lock on shared artifact for editing.

        Args:
            artifact_id: Artifact ID
            agent_id: Agent ID requesting lock

        Returns:
            True if lock acquired, False if already locked
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        artifact = next((a for a in agent.artifacts if a.id == artifact_id), None)
        if not artifact or not artifact.shared:
            return False

        # Check if already locked
        if artifact.locked_by and artifact.locked_by != agent_id:
            return False

        artifact.locked_by = agent_id
        return True

    def release_artifact_lock(
        self,
        artifact_id: str,
        agent_id: str,
    ) -> None:
        """Release lock on shared artifact.

        Args:
            artifact_id: Artifact ID
            agent_id: Agent ID releasing lock
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return

        artifact = next((a for a in agent.artifacts if a.id == artifact_id), None)
        if artifact and artifact.locked_by == agent_id:
            artifact.locked_by = None

    def update_shared_artifact(
        self,
        artifact_id: str,
        agent_id: str,
        new_content: str,
    ) -> None:
        """Update shared artifact content (requires lock).

        Args:
            artifact_id: Artifact ID
            agent_id: Agent ID making update
            new_content: New artifact content
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        artifact = next((a for a in agent.artifacts if a.id == artifact_id), None)
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")

        if not artifact.shared:
            raise ValueError(f"Artifact {artifact_id} is not shared")

        if artifact.locked_by != agent_id:
            raise ValueError(f"Artifact is locked by {artifact.locked_by}")

        # Update content and metadata
        artifact.content = new_content
        artifact.version += 1
        artifact.last_modified_by = agent_id

        # Propagate changes to all agents sharing this artifact
        for other_agent in self.agents.values():
            if other_agent.id != agent_id:
                other_artifact = next((a for a in other_agent.artifacts if a.id == artifact_id), None)
                if other_artifact:
                    other_artifact.content = new_content
                    other_artifact.version = artifact.version
                    other_artifact.last_modified_by = agent_id

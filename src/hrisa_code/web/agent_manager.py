"""Web-based agent manager for orchestrating multiple GenAI agents."""

import asyncio
import uuid
from dataclasses import dataclass, field
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

        # Background task for monitoring
        self.monitor_task: Optional[asyncio.Task] = None
        self.running = False

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
            # Log agent start
            await self._add_log(agent_id, "info", f"Agent started with role: {agent_info.role or 'general'}")
            await self._add_log(agent_id, "info", f"Using model: {agent_info.model}")
            await self._add_log(agent_id, "info", f"Working directory: {agent_info.working_dir}")

            # Add initial user message
            initial_message = AgentMessage(
                timestamp=datetime.now(),
                role="user",
                content=agent_info.task,
            )
            agent_info.messages.append(initial_message)
            await self._notify_message(agent_id, initial_message)

            await self._add_log(agent_id, "info", "Executing task...")

            # Run agent
            result = await agent.execute_task(agent_info.task)

            # Store output
            agent_info.output = result
            agent_info.status = AgentStatus.COMPLETED
            agent_info.progress.completed_steps = agent_info.progress.total_steps

            await self._add_log(agent_id, "info", "Task completed successfully")

        except Exception as e:
            agent_info.status = AgentStatus.FAILED
            agent_info.error = str(e)
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

# Future Enhancements for Hrisa Code

This document outlines planned future enhancements and architectural improvements for Hrisa Code.

## Development Philosophy

**Current Phase: Functionality First** 🔧
- Focus on implementing core features
- Get things working end-to-end
- Verify accuracy and correctness
- Build foundational capabilities

**Future Phase: Optimization & Polish** ⚡
- Performance optimization
- Minimize redundant operations
- Adaptive workflows
- Enhanced UX/DX

---

## 1. Meta-Orchestration System

### Vision
Transform the current task-specific orchestration (HRISA.md generation) into a **general-purpose meta-orchestrator** that can handle ANY complex workflow autonomously.

### Current State
We have a hard-coded orchestrator for HRISA.md generation:
```python
# Specific workflow with fixed steps
steps = ["architecture", "components", "features", "workflows", "synthesis"]
```

### Proposed Architecture

#### 1.1 Complexity Detection Module
Automatically determines if a task requires orchestration:

```python
class ComplexityDetector:
    """Analyzes tasks to determine if orchestration is needed."""

    async def analyze(self, task: str, context: str) -> TaskComplexity:
        """
        Analyze task complexity and determine orchestration needs.

        Returns:
            - Simple: Single-turn execution (e.g., "list files")
            - Moderate: Multi-step but sequential (e.g., "add logging")
            - Complex: Multi-step with exploration (e.g., "refactor auth")
        """
        pass
```

**Detection Criteria:**
- Multi-file changes required?
- Requires exploration before action?
- Multiple interdependent steps?
- Uncertain scope/requirements?

**Examples:**
```
✅ Simple → "List all Python files"
→ Single tool call, no orchestration

⚠️ Moderate → "Add error handling to API endpoints"
→ Multi-step: explore → plan → implement

🔴 Complex → "Implement comprehensive authentication system"
→ Multi-phase: research → design → implement → test
```

#### 1.2 Dynamic Planning Module
Generates task-specific execution plans:

```python
class TaskPlanner:
    """Generates dynamic execution plans for complex tasks."""

    async def create_plan(
        self,
        task: str,
        complexity: TaskComplexity,
        codebase_context: str
    ) -> ExecutionPlan:
        """
        Use LLM to generate a step-by-step execution plan.

        Returns:
            ExecutionPlan with:
            - Ordered list of steps
            - Tool requirements per step
            - Success criteria
            - Estimated scope
        """
        pass
```

**Plan Structure:**
```python
@dataclass
class ExecutionStep:
    name: str                          # Step identifier
    description: str                   # What this step does
    required_tools: List[str]          # Tools needed
    dependencies: List[str]            # Previous steps required
    success_criteria: str              # How to know it's done

@dataclass
class ExecutionPlan:
    task: str                          # Original task
    steps: List[ExecutionStep]         # Ordered steps
    estimated_complexity: str          # Low/Medium/High
    can_parallelize: List[Set[str]]    # Steps that can run in parallel
```

**Example Generated Plan:**

User Task: "Add comprehensive logging to the application"

```python
plan = ExecutionPlan(
    task="Add comprehensive logging to the application",
    steps=[
        ExecutionStep(
            name="discover_existing_logging",
            description="Search for existing logging implementations",
            required_tools=["search_files", "grep"],
            dependencies=[],
            success_criteria="Found all files using logging"
        ),
        ExecutionStep(
            name="identify_key_modules",
            description="Identify modules that need logging",
            required_tools=["list_directory", "read_file"],
            dependencies=["discover_existing_logging"],
            success_criteria="Listed all critical modules"
        ),
        ExecutionStep(
            name="design_logging_strategy",
            description="Design consistent logging approach",
            required_tools=["read_file"],
            dependencies=["identify_key_modules"],
            success_criteria="Created logging design"
        ),
        ExecutionStep(
            name="implement_logging",
            description="Add logging to identified modules",
            required_tools=["write_file", "read_file"],
            dependencies=["design_logging_strategy"],
            success_criteria="Logging added to all modules"
        ),
        ExecutionStep(
            name="add_configuration",
            description="Add logging configuration",
            required_tools=["write_file"],
            dependencies=["implement_logging"],
            success_criteria="Logging config file created"
        ),
        ExecutionStep(
            name="verify_implementation",
            description="Test logging implementation",
            required_tools=["execute_command"],
            dependencies=["add_configuration"],
            success_criteria="All tests pass"
        ),
    ],
    estimated_complexity="High",
    can_parallelize=[{"discover_existing_logging", "identify_key_modules"}]
)
```

#### 1.3 Adaptive Execution Engine
Executes plans with intelligence and adaptation:

```python
class AdaptiveExecutor:
    """Executes plans with adaptive behavior."""

    async def execute(self, plan: ExecutionPlan) -> ExecutionResult:
        """
        Execute plan with adaptation:
        - Monitor results of each step
        - Adjust subsequent steps based on findings
        - Handle errors gracefully
        - Decide when to continue vs. abort
        - Provide progress feedback
        """

        for step in plan.steps:
            # Execute step
            result = await self.execute_step(step)

            # Analyze result
            analysis = await self.analyze_result(result, step)

            # Adapt plan if needed
            if analysis.requires_adjustment:
                plan = await self.adjust_plan(plan, analysis)

            # Decide if we should continue
            if analysis.should_abort:
                return ExecutionResult.aborted(reason=analysis.reason)

            # Provide progress update
            self.report_progress(step, result)

        return ExecutionResult.success()
```

**Adaptive Behaviors:**
- **Pivot on Discovery**: If step reveals unexpected structure, adjust plan
- **Skip Unnecessary Steps**: If prerequisites already met, skip steps
- **Add Missing Steps**: If gaps discovered, insert new steps
- **Error Recovery**: If step fails, try alternative approach
- **Scope Adjustment**: If task too large, break into subtasks

**Example Adaptation:**

```python
# Original plan step 3: "Design logging strategy"
# Execution discovers: Logging framework already exists!

# Adaptation:
plan.steps[3].description = "Extend existing logging strategy"
plan.steps[4].description = "Enhance existing logging calls"
# Skip step 5 (configuration already exists)
```

### Benefits

1. **Generalization**: Works for ANY complex task, not just HRISA.md
2. **Intelligence**: LLM generates task-specific plans
3. **Adaptability**: Adjusts based on discoveries
4. **Reusability**: Single system handles diverse workflows
5. **Scalability**: Easily extend to new task types

### Workflow Templates

Before building the full meta-orchestrator, we'll create templates for common tasks:

#### 1. HRISA.md Generation (✅ Implemented)
- **Audience**: AI assistants
- **Steps**: Architecture → Components → Features → Workflows → Synthesis
- **Focus**: Technical internals, comprehensive

#### 2. README Generation (Planned)
- **Audience**: Human developers/users
- **Steps**: Project Discovery → Feature Highlights → Installation → Usage Examples → Synthesis
- **Focus**: User-friendly, getting started
- **Output**: README.md with:
  - Clear value proposition
  - Feature highlights with benefits
  - Installation instructions
  - Usage examples
  - Troubleshooting
  - Contributing guidelines

#### 3. API Documentation (Planned)
- **Audience**: API consumers
- **Steps**: Endpoint Discovery → Schema Analysis → Example Generation → Synthesis
- **Focus**: API reference, authentication, endpoints

#### 4. CONTRIBUTING.md (Planned)
- **Audience**: Contributors
- **Steps**: Workflow Discovery → Setup Analysis → Standards Review → Synthesis
- **Focus**: How to contribute, dev setup, guidelines

### Implementation Phases

**Phase 1: Abstraction** (Near-term)
- Extract common orchestration logic from HRISA orchestrator
- Make steps configurable
- Create orchestration templates for common tasks
- **Implement README workflow template**

**Phase 2: Dynamic Planning** (Mid-term)
- Implement complexity detector
- Build LLM-based plan generator
- Create plan validation and optimization

**Phase 3: Adaptive Execution** (Long-term)
- Implement result analysis
- Build plan adjustment logic
- Add sophisticated error recovery
- Support parallel step execution

**Phase 4: Optimization** (Future)
- Minimize redundant tool calls
- Optimize execution time
- Cache intermediate results
- Smart step skipping

---

## 2. Enhanced Tool System

### 2.1 Write Operations with User Approval ⚠️ **HIGH PRIORITY**
**Philosophy**: Read operations are safe and automatic. Write operations need user confirmation.

**Required Git Write Tools** (with approval):
- **git_commit**: Create commits with message
  - Requires: User approval for commit message and file list
  - Shows: Diff preview before commit
- **git_push**: Push commits to remote
  - Requires: Explicit user confirmation (critical operation)
  - Shows: What will be pushed (branch, commits)
- **git_pull**: Pull changes from remote
  - Requires: User confirmation if local changes exist
  - Shows: What will be fetched
- **git_stash**: Stash working changes
  - Requires: User approval for stash message
  - Shows: What will be stashed

**File Write Tools Enhancement** (add approval layer):
- **write_file**: Needs approval if file exists
  - Shows: Diff of changes (if file exists)
  - Allows: Approve, Reject, Edit
- **delete_file**: Always needs approval
  - Shows: File contents before deletion
  - Requires: Explicit confirmation
- **move_file/rename_file**: Needs approval
  - Shows: Source and destination
  - Checks: Destination doesn't exist

**Implementation Pattern**:
```python
class ApprovalManager:
    """Manages user approval for write operations."""

    async def request_approval(
        self,
        operation: WriteOperation,
        preview: str,
        risk_level: RiskLevel
    ) -> ApprovalResult:
        """
        Request user approval with rich preview.

        Args:
            operation: What will be done
            preview: Diff/content preview
            risk_level: LOW, MEDIUM, HIGH, CRITICAL

        Returns:
            APPROVED, REJECTED, MODIFIED (user edited)
        """
        # Show rich preview with syntax highlighting
        console.print(f"[bold yellow]Approval Required: {operation}[/]")
        console.print(Panel(preview, title="Preview"))

        # Different prompts based on risk
        if risk_level == RiskLevel.CRITICAL:
            response = Confirm.ask(
                "⚠️  CRITICAL: This cannot be undone. Type 'yes' to confirm",
                default=False
            )
        else:
            response = Confirm.ask("Approve this operation?", default=True)

        return ApprovalResult.from_response(response)
```

**Configuration**:
```yaml
# .hrisa/config.yaml
tools:
  approval_mode: interactive  # interactive, auto_approve, auto_reject
  risk_levels:
    git_push: critical
    git_commit: medium
    delete_file: high
    write_file: low  # if file exists: medium
```

### 2.2 Tool Call Optimization
- Detect redundant tool calls
- Cache tool results within a session
- Batch similar operations
- Smart tool selection

### 2.3 Tool Streaming
- Stream large file reads
- Progressive command output
- Real-time feedback

### 2.4 Tool Composition
- Combine multiple tools into workflows
- Create custom tool chains
- Reusable tool patterns

---

## 3. Context Management

### 3.1 Smart Context Windows
- Prioritize relevant context
- Summarize old conversations
- Keep critical information in context

### 3.2 Project Memory
- Remember project structure across sessions
- Cache architectural insights
- Maintain code relationship graph

---

## 4. Multi-Model Support ✅ **IMPLEMENTED**

### 4.1 Specialized Models ✅
- ✅ Use different models for different tasks
- ✅ Route tasks to best-suited model
- ✅ Fallback strategies

### 4.2 Model Orchestration ✅
- ✅ Use specialized models for orchestration steps
- ✅ Model catalog with capability metadata
- ✅ Intelligent model routing and selection
- ✅ Graceful fallback to available models

**Implementation Details:**
- **Model Catalog** (`model_catalog.py`): Defines model profiles with capabilities, quality tiers, and speed tiers
- **Model Router** (`model_router.py`): Selects best model for each task based on requirements and availability
- **Conversation Manager**: Supports dynamic model switching while preserving conversation history
- **HRISA Orchestrator**: Uses different models for each step (architecture, components, features, workflows, synthesis)

**Usage:**
```bash
# Use multi-model orchestration (requires large models like qwen2.5:72b, deepseek-coder-v2:236b, llama3.1:70b)
hrisa init --comprehensive --multi-model

# Example step assignments:
# - Architecture: qwen2.5:72b (strong reasoning, architecture analysis)
# - Components: deepseek-coder-v2:236b (best code understanding)
# - Features: qwen2.5:72b (pattern generation)
# - Workflows: deepseek-r1:70b (workflow tracing with reasoning)
# - Synthesis: llama3.1:70b (excellent documentation writing)
```

**Benefits:**
- Better quality output by using specialized models for specific tasks
- Optimal model selection based on task requirements
- Automatic fallback if preferred models unavailable
- Future-ready for additional model types and capabilities

---

## 5. Agentic Robustness & Guardrails

### 5.1 Loop Detection & Prevention ⚠️ **HIGH PRIORITY**
**Problem Identified**: During testing, qwen2.5-coder:32b called `git_status` 9 times in a row with identical parameters, reaching the 20-round limit without completing the task.

**Required Improvements:**
- **Detect identical tool calls**: Track tool call history within a conversation turn
- **Pattern recognition**: Identify when same tool is called 3+ times with same/similar parameters
- **Automatic intervention**: After 3 identical calls, inject system message: "You've called this tool multiple times with the same result. Try a different approach or provide a final answer."
- **Loop breaking**: Suggest alternative tools or prompt for completion
- **Configurable thresholds**: Allow users to set max repeated calls per tool

**Implementation:**
```python
class LoopDetector:
    def __init__(self, max_identical_calls: int = 3):
        self.tool_history = []
        self.max_identical = max_identical_calls

    def check_loop(self, tool_call: dict) -> LoopStatus:
        """Detect if we're in an unproductive loop."""
        recent_calls = self.tool_history[-5:]  # Last 5 calls
        identical_count = sum(1 for call in recent_calls
                             if call['name'] == tool_call['name']
                             and call['arguments'] == tool_call['arguments'])

        if identical_count >= self.max_identical:
            return LoopStatus.DETECTED
        return LoopStatus.OK
```

### 5.2 Result Verification & Goal Detection ⚠️ **HIGH PRIORITY**
**Problem**: Models don't verify if tool results actually answer the user's question, leading to repeated calls.

**Required Improvements:**
- **Result analysis**: After each tool call, LLM evaluates: "Does this result answer the user's question?"
- **Goal state tracking**: Maintain what information is still needed
- **Completion detection**: Recognize when task is complete
- **Progress validation**: Verify each step moves closer to goal

**Implementation:**
```python
class GoalTracker:
    async def check_progress(
        self,
        user_question: str,
        tool_results: List[ToolResult],
        current_answer: str
    ) -> GoalStatus:
        """
        Evaluate if we have enough information to answer.
        Returns: COMPLETE, IN_PROGRESS, or STUCK
        """
        prompt = f"""
        User asked: {user_question}
        Tool results obtained: {tool_results}
        Current answer: {current_answer}

        Do we have enough information to fully answer the question?
        If yes, return COMPLETE. If making progress, return IN_PROGRESS.
        If stuck (repeated attempts, no new info), return STUCK.
        """
        # Use lightweight model for this check
```

### 5.3 Intelligent Tool Selection
**Current Issue**: Models sometimes try to use `execute_command` with tool-specific parameters (like passing `cached` or `directory` to git commands via execute_command instead of using dedicated git tools)

**Required Improvements:**
- **Tool capability awareness**: LLM understands which parameters each tool accepts
- **Tool suggestion**: System suggests appropriate tools based on task
- **Parameter validation**: Validate parameters before execution
- **Fallback strategies**: If preferred tool unavailable, suggest alternatives

### 5.4 Reflective Learning
- Learn from successful patterns
- Avoid failed approaches
- Build pattern library
- Remember what worked in previous sessions

---

## 6. Collaboration Features

### 6.1 Multi-Agent Systems
- Specialized agents for different tasks
- Agent communication protocols
- Coordinated execution

### 6.2 Human-in-the-Loop ✅ **PARTIALLY IMPLEMENTED**
**Status**: Core approval manager implemented. Additional features planned.

**Implemented Features:**
- ✅ **Write Operation Approval**: User confirms file overwrites and destructive commands
- ✅ **Destructive Operation Detection**: Automatic detection of dangerous commands (rm, del, etc.)
- ✅ **Diff Preview**: Shows file changes before applying overwrites
- ✅ **Session Memory**: "Always/Never" approval for operation types during session
- ✅ **Auto-approve Mode**: Testing-friendly mode to bypass prompts
- ✅ **Rich UI**: Formatted panels with colored options and clear descriptions
- ✅ **Git Operation Approval**: Approval for commits, pushes, pulls, stash operations
- ✅ **File Delete Approval**: Explicit approval for file deletion with warnings

**Remaining Implementation Areas:**
- ⏳ **Clarification Requests**: LLM asks when uncertain about intent
- ⏳ **Manual Intervention**: Allow user to pause, modify, or abort at any step
- ⏳ **Undo Support**: Track operations for potential rollback

**Current Workflow Example:**
```
User: "Update config.yaml"
Assistant: *tries to write file*
System: [Displays approval panel]
  📝 File Write Operation
  Overwrite existing file: config.yaml
  File: /path/to/config.yaml
  Action: Overwrite
  [Shows unified diff preview]

  Options:
    y - Approve this operation
    n - Deny this operation
    a - Always approve this type (for this session)
    v - Never approve this type (for this session)

User: "y"
Assistant: *executes write*
```

---

## Timeline

### Q1 2025: Foundation ✅ (Complete)
- ✅ Basic tool calling
- ✅ Multi-turn workflows
- ✅ HRISA.md orchestration
- ✅ Text-based tool parsing
- ✅ Git read operations (status, diff, log, branch)

### Q2 2025: Robustness & Safety ✅ (COMPLETE!)
**Critical Issues Identified in Testing:**
- ✅ **Loop Detection & Prevention**: Implemented - prevents models from getting stuck (max 3 identical calls)
- ✅ **Goal Detection**: Implemented - detects when task is complete
- ✅ **Write Operations with Approval**: Implemented - user confirmation for write operations
- ✅ **Abstract Orchestration Patterns**: Implemented - ProgressiveBaseOrchestrator + TemplateOrchestrator
- ✅ **Result Verification System**: Implemented - validates tool output relevance after each execution
- ✅ **Intelligent Tool Selection Guidance**: Implemented - parameter validation and tool capability hints

**Implementation Summary:**
1. ✅ Loop detector (max 3 identical calls) - COMPLETE
2. ✅ Goal tracker (completion detection) - COMPLETE
3. ✅ Approval manager (write operation confirmation) - COMPLETE
4. ✅ Git write tools (commit, push, pull, stash) with approval - COMPLETE
5. ✅ File delete tool with approval - COMPLETE
6. ✅ Abstract orchestration patterns - COMPLETE (607 lines eliminated)
7. ✅ Result verification system - COMPLETE (immediate relevance checking)
8. ✅ Tool selection guidance - COMPLETE (validation + capability hints)

### Q3 2025: Intelligence & Generalization ✅ COMPLETE
- ✅ Multi-model orchestration
- ✅ Complexity detection (heuristic + LLM-based analysis with visual feedback)
- ✅ Dynamic planning (LLM-based plan generation with heuristic fallback)
- ✅ AgentLoop integration (complexity + planning components)
- ✅ Adaptive execution (plan-driven step-by-step execution with progress tracking)
- ✅ Plan refinement (adapts plans based on discoveries during execution)
- ✅ Error recovery (handles step failures, stops after max errors)
- ✅ ConversationManager integration (plan mode accessible via /agent command cycling)
- ✅ Full end-to-end workflow (normal → agent → plan mode cycling with visual feedback)

### Q4 2025: Optimization & Scale
- ⏳ Performance tuning
- ⏳ Tool optimization (caching, deduplication)
- ⏳ Context management
- ⏳ Parallel step execution
- ⏳ **Adaptive Mode Switching** (NEW)

---

## 2. Adaptive Mode Switching

### Vision
The system should intelligently detect when the current execution mode (normal/agent/plan) is not optimal for the task complexity and suggest switching modes with user confirmation.

### Problem
Currently, users manually choose execution modes:
- **Normal mode** - for simple queries
- **Agent mode** - for multi-step autonomous tasks
- **Plan mode** - for complex tasks requiring structured execution

However, users might:
- Choose normal mode for a complex task (inefficient, requires many back-and-forth interactions)
- Choose plan mode for a simple task (overhead of plan generation)
- Start in one mode and realize mid-execution that another mode would work better

### Proposed Solution

#### 2.1 Mid-Execution Detection
Monitor task complexity during execution and detect mismatches:

```python
class AdaptiveModeManager:
    """Detects when current mode is suboptimal and suggests alternatives."""

    async def evaluate_mode_fit(
        self,
        current_mode: str,
        task: str,
        execution_history: List[str]
    ) -> ModeSuggestion:
        """
        Evaluate if current mode matches task complexity.

        Returns:
            - ModeSuggestion with:
              - should_switch: bool
              - suggested_mode: str
              - reason: str
              - confidence: float
        """
        pass
```

#### 2.2 Detection Triggers

**Switch to Plan Mode** (from normal/agent):
- User's task requires 5+ tool calls
- Multiple failed attempts at same subtask
- Task involves multiple file modifications
- Clear multi-phase structure detected
- Example: In normal mode, user asks to "refactor the entire auth system"

**Switch to Agent Mode** (from normal):
- Task requires 2-3 autonomous steps
- User asks follow-up questions indicating multi-step intent
- Example: In normal mode, user asks to "add error logging and test it"

**Switch to Normal Mode** (from agent/plan):
- Task is actually simple (1-2 tool calls would suffice)
- User asks a simple informational question
- Example: In plan mode, user asks "what's in this file?"

#### 2.3 User Confirmation Flow

```
[During execution, system detects mismatch]

╭─────────────────────────────────────────────────────╮
│ 💡 Mode Suggestion                                  │
│                                                     │
│ This task appears more COMPLEX than expected.       │
│                                                     │
│ Current mode: Normal                                │
│ Suggested mode: Plan Mode                           │
│                                                     │
│ Reason: Task requires multiple file modifications   │
│ across 8 files with dependencies.                   │
│                                                     │
│ Plan mode would:                                    │
│   • Generate structured execution plan              │
│   • Track progress across steps                    │
│   • Handle dependencies automatically               │
│                                                     │
│ Switch to Plan Mode? [Y/n/never]:                   │
╰─────────────────────────────────────────────────────╯
```

**User Options:**
- **Y** (default) - Switch to suggested mode and continue
- **n** - Stay in current mode
- **never** - Disable adaptive suggestions for this session

#### 2.4 Implementation Details

**Detection Points:**
1. **After initial task analysis** (before first action)
2. **After 3rd tool call** (pattern emerging)
3. **After tool errors** (current approach not working)
4. **On explicit complexity markers** ("comprehensive", "entire", "all")

**Thresholds:**
```python
SIMPLE_TASK_INDICATORS = {
    "tool_calls": 1,
    "files_accessed": 1,
    "execution_time": "< 30s"
}

MODERATE_TASK_INDICATORS = {
    "tool_calls": "2-5",
    "files_accessed": "2-5",
    "execution_time": "30s - 2min"
}

COMPLEX_TASK_INDICATORS = {
    "tool_calls": "5+",
    "files_accessed": "5+",
    "execution_time": "> 2min",
    "has_dependencies": True
}
```

**Confidence Scoring:**
- High confidence (>0.8): Auto-suggest immediately
- Medium confidence (0.5-0.8): Suggest after confirmation threshold
- Low confidence (<0.5): Don't suggest

#### 2.5 Example Scenarios

**Scenario 1: Underestimated Complexity**
```
User: [Normal Mode] "Add error handling to all API endpoints"

[System starts execution]
[After 3 tool calls exploring files]

💡 Mode Suggestion: This task is more COMPLEX than expected.
   Suggested: Plan Mode
   Reason: Found 12 API endpoint files requiring changes

Switch to Plan Mode? [Y/n]: Y

[Switches to plan mode, generates 5-step plan]
```

**Scenario 2: Overestimated Complexity**
```
User: [Plan Mode] "Show me what's in config.py"

💡 Mode Suggestion: This task is SIMPLER than expected.
   Suggested: Normal Mode
   Reason: Single file read operation

Switch to Normal Mode? [Y/n]: Y

[Reads file immediately, no plan needed]
```

**Scenario 3: Mid-Execution Pivot**
```
User: [Agent Mode] "Fix the authentication bug"

[Agent tries 3 different approaches, all fail]

💡 Mode Suggestion: Consider switching to Plan Mode
   Suggested: Plan Mode
   Reason: Multiple failed attempts suggest need for
           structured exploration and planning

Switch to Plan Mode? [Y/n]: Y

[Generates plan: Explore → Diagnose → Design Fix → Implement → Test]
```

#### 2.6 Configuration

Users can control adaptive suggestions:

```yaml
# .hrisa/config.yaml
adaptive_mode:
  enabled: true
  auto_suggest_threshold: 0.8  # confidence threshold
  prompt_for_confirmation: true
  remember_user_preferences: true  # remember "never" choices

  # Disable specific transitions
  disable_suggestions:
    - "normal_to_plan"  # Never suggest plan mode from normal
```

#### 2.7 Benefits

**For Users:**
- ✅ Don't need to predict task complexity upfront
- ✅ System guides them to optimal mode
- ✅ Learn which modes work best for which tasks
- ✅ Can override suggestions (user stays in control)

**For System:**
- ✅ Better mode utilization
- ✅ Fewer wasted iterations
- ✅ Faster task completion
- ✅ User feedback on mode effectiveness

#### 2.8 Future Extensions

- **Learning from history**: Track which mode switches users accept/reject
- **Proactive suggestions**: "Based on similar tasks, Plan Mode works better"
- **Cost optimization**: "Plan Mode will use fewer LLM calls for this task"
- **Time estimates**: "Plan Mode estimated: 3 min vs Agent Mode: 8 min"

---

## Contributing

This is a living document. As we implement features and learn from usage, we'll update priorities and approaches.

**Want to contribute?** Pick an enhancement and:
1. Discuss the approach in an issue
2. Prototype the solution
3. Test with real use cases
4. Submit PR with documentation

---

## References

- [Claude Code](https://claude.com/claude-code) - Inspiration for autonomous coding
- [LangGraph](https://github.com/langchain-ai/langgraph) - Graph-based agent orchestration
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) - Autonomous agents
- [Aider](https://github.com/paul-gauthier/aider) - Local coding assistant patterns

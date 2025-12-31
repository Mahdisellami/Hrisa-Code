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

### Q3 2025: Real Project Implementation 🏗️
- ⏳ Use Hrisa to build a complete project from scratch
- ⏳ Validate all improvements in real-world scenario
- ⏳ Measure success metrics (code written by Hrisa, tests passing, etc.)
- ⏳ Identify gaps and improvement opportunities
- ⏳ Document lessons learned

**Candidate Projects:**
- CLI Task Manager (CRUD, persistence, search)
- API Client Library (auth, retries, rate limiting)
- Code Analysis Tool (AST parsing, metrics, refactoring suggestions)

**Success Criteria:**
- Minimum: 50% code by Hrisa, 70% tests passing
- Good: 70% code by Hrisa, 85% tests passing
- Excellent: 85%+ code by Hrisa, 95%+ tests passing

See detailed plan in section 2 below.

### Q4 2025: Optimization & Scale
- ⏳ Performance tuning
- ⏳ Tool optimization (caching, deduplication)
- ⏳ Context management
- ⏳ Parallel step execution
- ⏳ **Adaptive Mode Switching** (NEW)

---

## 2. Real Project Implementation Test (Q3 2025)

### Goal
Use Hrisa to implement a complete real-world project from scratch to validate all improvements and identify remaining gaps.

### Project Selection Criteria
Choose a project that:
- **Moderate complexity** - Multiple modules, testing, documentation needed
- **Clear requirements** - Well-defined scope to measure success
- **Real utility** - Actually useful, not just a demo
- **Good test case** - Exercises all patterns (implement, refactor, test, document, optimize)

### Candidate Projects

**Option 1: CLI Task Manager**
```
Scope:
- Add/edit/delete tasks with priorities
- Task categories and tags
- Due dates and reminders
- Search and filtering
- Export to various formats (JSON, CSV, Markdown)

Why Good Test:
✓ Implements CRUD operations
✓ Needs data persistence (file or SQLite)
✓ Requires comprehensive testing
✓ Needs user documentation
✓ Can be optimized (search performance)
✓ Can be refactored (add features incrementally)
✓ Exercises: implement, test, document, refactor, optimize patterns
```

**Option 2: API Client Library**
```
Scope:
- REST API wrapper with authentication (Bearer, OAuth)
- Request/response handling with serialization
- Error handling and automatic retries
- Rate limiting and backoff
- Comprehensive documentation and examples

Why Good Test:
✓ Requires design phase (API surface)
✓ Needs extensive testing (unit + integration + mocking)
✓ Documentation is critical (public API)
✓ Error handling complexity
✓ Can be optimized (caching, connection pooling)
✓ Exercises: design, implement, test, document, optimize patterns
```

**Option 3: Code Analysis Tool**
```
Scope:
- Parse Python code using AST
- Detect code smells (long functions, deep nesting, etc.)
- Generate complexity metrics (cyclomatic, cognitive)
- Suggest refactorings
- Output reports in multiple formats

Why Good Test:
✓ Complex implementation (AST traversal)
✓ Needs multiple modules (parser, analyzer, reporter)
✓ Testing is critical (many edge cases)
✓ Documentation needed (usage, extending)
✓ Performance matters (large codebases)
✓ Self-referential (can analyze itself!)
✓ Exercises: ALL patterns (explore, analyze, design, implement, test, document, optimize)
```

### Testing Methodology

**Phase 1: Planning (Day 1)**
```bash
hrisa chat
/agent  # Cycle to plan mode
> Implement a [PROJECT] with the following features: [SPEC]
```
**Measure:**
- Plan quality (number of steps, specificity of each step)
- Complexity detection accuracy
- Time to generate plan

**Expected:**
- Multi-step plan (8-15 steps)
- Proper phases (exploration → design → implement → test → document)
- Realistic dependencies between steps

---

**Phase 2: Implementation (Days 2-5)**
```bash
> Implement the [MODULE_NAME] according to the design in step 3
> Write comprehensive tests for [MODULE_NAME] covering happy path and edge cases
> Add documentation for [MODULE_NAME] including usage examples
```

**Measure per module:**
- Code quality (passes linting: black, ruff, mypy)
- Tool calls efficiency (how many calls per step)
- Self-correction rate (validation errors, retries)
- Manual fixes needed (% of code that needs human intervention)

**Expected:**
- Working code with <30% manual fixes needed
- Tests that pass on first run (with minor fixes)
- Clear documentation generated

---

**Phase 3: Refinement (Days 6-7)**
```bash
> Refactor [MODULE] to improve maintainability by extracting helper functions
> Optimize [FUNCTION] for better performance with large inputs
> Add comprehensive API documentation with docstrings and examples
```

**Measure:**
- Refactoring quality (maintains tests, improves structure)
- Pattern usage (refactor, optimize, document patterns triggered)
- Integration across modules (does refactoring break other modules?)

**Expected:**
- Improved code structure without breaking tests
- Performance improvements measurable
- Complete documentation coverage

---

**Phase 4: Analysis & Metrics (Day 8)**

**Success Metrics:**
- **Code Written:** % of LOC written by Hrisa vs manual
- **Tests Passing:** % of tests passing without manual fixes
- **Iterations:** Average # of iterations per feature
- **Time Saved:** Estimated time saved vs manual coding
- **Tool Efficiency:** Tool calls per completed feature

**Quality Metrics:**
- Code passes linting (black, ruff, mypy) ✓/✗
- Tests have >80% coverage ✓/✗
- Documentation complete and clear ✓/✗
- No major bugs in functionality ✓/✗
- Code follows project conventions ✓/✗

---

### What We'll Learn

**Strengths to Validate:**
- ✓ Step context passing reduces redundancy
- ✓ Heuristic patterns work for real tasks
- ✓ Plan mode handles multi-module projects
- ✓ Goal tracking prevents premature completion
- ✓ Parameter checklists reduce errors

**Gaps to Discover:**
- ❓ Module interdependencies (does it maintain consistency?)
- ❓ Long-running tasks (context management over days)
- ❓ Error recovery in multi-step implementations
- ❓ Design consistency across modules
- ❓ Integration testing coordination
- ❓ Refactoring impact analysis
- ❓ Documentation quality and completeness

**Improvements to Identify:**
- What patterns are missing?
- What tool calls are redundant?
- What prompts need clarification?
- What error recovery is needed?

---

### Success Criteria

**Minimum Success (⭐):**
- 50% of code written by Hrisa (other 50% manual fixes)
- 70% of tests passing without fixes
- Project is functional and usable
- Manual intervention <5 times per module

**Good Success (⭐⭐):**
- 70% of code written by Hrisa
- 85% of tests passing
- Minimal manual intervention (<3 times per module)
- Documentation mostly complete

**Excellent Success (⭐⭐⭐):**
- 85%+ code written by Hrisa
- 95%+ tests passing
- Production-quality output
- Documentation complete and clear
- Minimal manual intervention (<2 times per module)

---

### Expected Timeline

- **When:** Q3 2025 (after step context and quality improvements settle)
- **Duration:** 1-2 weeks for full project implementation
- **Effort:** Daily sessions (1-2 hours) to maintain context
- **Commitment:** Consistent testing to gather meaningful data

---

### Deliverables

1. **Working Project**
   - Complete implementation
   - All tests passing
   - Documentation included
   - Ready for real use

2. **Implementation Log**
   - Detailed record of all Hrisa interactions
   - Copy of all prompts and responses
   - Notes on manual interventions

3. **Metrics Report**
   - Quantified success metrics (tables, charts)
   - Comparison: expected vs actual
   - Time savings analysis

4. **Lessons Learned Document**
   - What worked well
   - What didn't work
   - Surprising findings
   - User experience feedback

5. **Improvement Roadmap**
   - Next features needed based on real usage
   - Prioritized list of fixes
   - New pattern ideas discovered

---

## 3. Adaptive Mode Switching

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

#### 2.1 Leverage Existing Infrastructure

**Important:** We already have these components - reuse them!
- ✅ `ComplexityDetector` - analyzes task complexity (SIMPLE/MODERATE/COMPLEX)
- ✅ `DynamicPlanner` - generates execution plans
- ✅ `GoalTracker` - monitors task progress and completion
- ✅ `LoopDetector` - detects when agent is stuck

**Adaptive mode switching should USE these, not duplicate them!**

```python
class AdaptiveModeManager:
    """Suggests mode switches based on existing detection systems."""

    def __init__(
        self,
        complexity_detector: ComplexityDetector,  # REUSE existing
        goal_tracker: GoalTracker,                # REUSE existing
        loop_detector: LoopDetector               # REUSE existing
    ):
        self.complexity_detector = complexity_detector
        self.goal_tracker = goal_tracker
        self.loop_detector = loop_detector

    async def evaluate_mode_fit(
        self,
        current_mode: str,
        task: str,
        execution_context: ExecutionContext
    ) -> ModeSuggestion:
        """
        Evaluate if current mode matches task complexity.

        Uses EXISTING detection systems:
        - ComplexityDetector for task analysis
        - GoalTracker for progress monitoring
        - LoopDetector for stuck detection
        """
        # Use existing complexity detector
        complexity = self.complexity_detector.analyze(task)

        # Check if mode matches complexity
        mode_complexity_map = {
            "normal": TaskComplexity.SIMPLE,
            "agent": TaskComplexity.MODERATE,
            "plan": TaskComplexity.COMPLEX
        }

        expected_mode = self._map_complexity_to_mode(complexity)

        if current_mode != expected_mode:
            return ModeSuggestion(
                should_switch=True,
                suggested_mode=expected_mode,
                reason=self._get_reason(complexity, current_mode),
                confidence=complexity.confidence
            )

        return ModeSuggestion(should_switch=False)
```

#### 2.2 Detection Triggers (Using Existing Systems)

**Important:** Triggers leverage existing detection capabilities:

**Switch to Plan Mode** (from normal/agent):
- **ComplexityDetector** returns `COMPLEX` (5+ indicators, dependencies detected)
- **LoopDetector** fires (multiple failed attempts at same subtask)
- **GoalTracker** shows no progress after 5+ tool rounds
- Example: In normal mode, user asks to "refactor the entire auth system"
  - ComplexityDetector finds: 12 files, dependencies, architectural changes

**Switch to Agent Mode** (from normal):
- **ComplexityDetector** returns `MODERATE` (2-4 indicators, no dependencies)
- Task requires 2-3 autonomous steps
- Example: In normal mode, user asks to "add error logging and test it"
  - ComplexityDetector finds: 2 steps, no dependencies

**Switch to Normal Mode** (from agent/plan):
- **ComplexityDetector** returns `SIMPLE` (1 indicator, single action)
- **GoalTracker** shows task achievable in 1-2 tool calls
- Example: In plan mode, user asks "what's in this file?"
  - ComplexityDetector finds: 1 file read, no complexity indicators

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

#### 2.4 Implementation Details (Thin Orchestration Layer)

**Important:** AdaptiveModeManager is a thin orchestration layer that USES existing systems, not a reimplementation.

**Detection Points:**
1. **After initial task analysis** (uses `ComplexityDetector.analyze()`)
2. **After 3rd tool call** (checks `LoopDetector` status)
3. **After tool errors** (checks `GoalTracker.check_progress()`)
4. **On explicit complexity markers** (already in `ComplexityDetector.COMPLEXITY_INDICATORS`)

**Thresholds (from ComplexityDetector):**
```python
# REUSE existing thresholds from ComplexityDetector
# These are already defined in src/hrisa_code/core/planning/complexity_detector.py

COMPLEXITY_INDICATORS = {
    "file_system_ops": ["multiple files", "directory", "recursive", "all files", "entire codebase"],
    "architectural": ["refactor", "restructure", "migrate", "architecture"],
    "multi_phase": ["implement", "test", "deploy", "first", "then", "after"],
    "dependencies": ["depends on", "requires", "after", "before"],
    "iterations": ["all", "each", "every", "throughout"]
}

# Map ComplexityDetector results to modes:
# SIMPLE (0-1 indicators) → normal mode
# MODERATE (2-4 indicators, no dependencies) → agent mode
# COMPLEX (5+ indicators or dependencies) → plan mode
```

**Confidence Scoring (from ComplexityDetector):**
- High confidence (>0.8): Auto-suggest immediately
- Medium confidence (0.5-0.8): Suggest after confirmation threshold
- Low confidence (<0.5): Don't suggest

**Integration Point:**
```python
# AdaptiveModeManager fits between ConversationManager and AgentLoop
# It does NOT duplicate detection - it consults existing detectors

class ConversationManager:
    def __init__(self, ...):
        # Existing detectors
        self.complexity_detector = ComplexityDetector()
        self.goal_tracker = GoalTracker()
        self.loop_detector = LoopDetector()

        # NEW: Thin orchestration layer
        self.adaptive_mode_manager = AdaptiveModeManager(
            complexity_detector=self.complexity_detector,  # Pass existing
            goal_tracker=self.goal_tracker,                # Pass existing
            loop_detector=self.loop_detector               # Pass existing
        )
```

#### 2.5 Example Scenarios

**Scenario 1: Underestimated Complexity (ComplexityDetector detects mismatch)**
```
User: [Normal Mode] "Add error handling to all API endpoints"

[System starts execution]
[After 3 tool calls exploring files]

[AdaptiveModeManager calls ComplexityDetector.analyze()]
ComplexityDetector returns:
  - Complexity: COMPLEX
  - Indicators: 5 (file_system_ops: "all", iterations: "each", architectural: implied)
  - Files affected: 12
  - Confidence: 0.9

💡 Mode Suggestion: This task is more COMPLEX than expected.
   Suggested: Plan Mode
   Reason: ComplexityDetector found 5+ complexity indicators
           (12 API endpoint files requiring coordinated changes)

Switch to Plan Mode? [Y/n]: Y

[Switches to plan mode, generates 5-step plan using DynamicPlanner]
```

**Scenario 2: Overestimated Complexity (ComplexityDetector shows SIMPLE)**
```
User: [Plan Mode] "Show me what's in config.py"

[AdaptiveModeManager calls ComplexityDetector.analyze()]
ComplexityDetector returns:
  - Complexity: SIMPLE
  - Indicators: 0
  - Files affected: 1
  - Confidence: 0.95

💡 Mode Suggestion: This task is SIMPLER than expected.
   Suggested: Normal Mode
   Reason: ComplexityDetector found no complexity indicators
           (single file read operation)

Switch to Normal Mode? [Y/n]: Y

[Reads file immediately, no plan needed]
```

**Scenario 3: Mid-Execution Pivot (LoopDetector + GoalTracker signal stuck)**
```
User: [Agent Mode] "Fix the authentication bug"

[Agent tries 3 different approaches, all fail]

[AdaptiveModeManager checks LoopDetector and GoalTracker]
LoopDetector: "Repetitive attempts detected"
GoalTracker: "No progress after 5 tool rounds"

💡 Mode Suggestion: Consider switching to Plan Mode
   Suggested: Plan Mode
   Reason: LoopDetector shows repetitive attempts without progress
           (structured exploration and planning may help)

Switch to Plan Mode? [Y/n]: Y

[Switches to plan mode]
[DynamicPlanner generates: Explore → Diagnose → Design Fix → Implement → Test]
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
- ✅ System guides them to optimal mode using proven detection systems
- ✅ Learn which modes work best for which tasks
- ✅ Can override suggestions (user stays in control)

**For System:**
- ✅ Better mode utilization
- ✅ Fewer wasted iterations
- ✅ Faster task completion
- ✅ User feedback on mode effectiveness
- ✅ **No code duplication** - reuses ComplexityDetector, GoalTracker, LoopDetector
- ✅ **Thin orchestration layer** - minimal new code, maximum reuse

#### 2.8 Architecture Overview

**Key Design Principle: Composition over Duplication**

```
┌─────────────────────────────────────────────────────────────┐
│ ConversationManager (existing)                              │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ComplexityDetector│  │ GoalTracker     │                  │
│  │   (existing)     │  │   (existing)    │                  │
│  └────────┬─────────┘  └────────┬────────┘                  │
│           │                     │                           │
│           │  ┌──────────────────┴────┐                      │
│           │  │   LoopDetector        │                      │
│           │  │   (existing)          │                      │
│           │  └──────────┬────────────┘                      │
│           │             │                                   │
│           └─────────────┴──────────────┐                    │
│                                        │                    │
│  ┌─────────────────────────────────────▼──────────────┐    │
│  │ AdaptiveModeManager (NEW - thin layer)             │    │
│  │                                                     │    │
│  │ - REUSES ComplexityDetector for analysis           │    │
│  │ - REUSES GoalTracker for progress checks           │    │
│  │ - REUSES LoopDetector for stuck detection          │    │
│  │ - NO duplicate thresholds or detection logic       │    │
│  │ - ONLY orchestrates mode switch suggestions        │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │ User Confirmation     │                      │
│              │ (ApprovalManager)     │                      │
│              └───────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

**What AdaptiveModeManager Does:**
- ✅ Consults existing detectors for signals
- ✅ Maps complexity/progress/loops to mode recommendations
- ✅ Prompts user for confirmation
- ✅ Executes mode switch if approved

**What AdaptiveModeManager Does NOT Do:**
- ❌ Reimplement complexity detection
- ❌ Reimplement goal tracking
- ❌ Reimplement loop detection
- ❌ Define new thresholds or indicators
- ❌ Duplicate any existing logic

**Estimated Implementation Size:**
- ~150 lines of orchestration code
- ~50 lines for user confirmation flow
- ~100 lines for configuration and testing
- **Total: ~300 lines** (vs 1000+ if reimplemented)

#### 2.9 Future Extensions

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

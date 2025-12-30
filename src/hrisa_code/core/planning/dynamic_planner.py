"""Dynamic task planning with LLM-based plan generation.

This module provides intelligent task planning that generates custom execution
strategies based on task complexity and requirements. Unlike hard-coded workflows,
the planner adapts to each unique task.

Key Features:
- LLM-based plan generation
- Step-by-step execution strategies
- Plan refinement based on discoveries
- Validation and feasibility checking
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import re


class PlanStepType(Enum):
    """Types of execution steps in a plan."""

    EXPLORATION = "exploration"  # Discover existing code/patterns
    ANALYSIS = "analysis"  # Analyze findings
    DESIGN = "design"  # Design solution approach
    IMPLEMENTATION = "implementation"  # Write/modify code
    TESTING = "testing"  # Verify functionality
    DOCUMENTATION = "documentation"  # Update docs
    VALIDATION = "validation"  # Final verification


class PlanStatus(Enum):
    """Status of an execution plan."""

    DRAFT = "draft"  # Plan generated but not started
    IN_PROGRESS = "in_progress"  # Executing steps
    COMPLETED = "completed"  # All steps finished
    FAILED = "failed"  # Plan execution failed
    REFINED = "refined"  # Plan was refined during execution


@dataclass
class PlanStep:
    """A single step in an execution plan."""

    step_number: int
    type: PlanStepType
    description: str
    rationale: str
    expected_tools: List[str] = field(default_factory=list)
    success_criteria: str = ""
    dependencies: List[int] = field(default_factory=list)  # Step numbers this depends on
    estimated_duration: str = "quick"  # quick, medium, long
    completed: bool = False
    result: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "step_number": self.step_number,
            "type": self.type.value,
            "description": self.description,
            "rationale": self.rationale,
            "expected_tools": self.expected_tools,
            "success_criteria": self.success_criteria,
            "dependencies": self.dependencies,
            "estimated_duration": self.estimated_duration,
            "completed": self.completed,
            "result": self.result,
        }


@dataclass
class ExecutionPlan:
    """A complete execution plan for a task."""

    task: str
    complexity: str  # SIMPLE, MODERATE, COMPLEX
    total_steps: int
    steps: List[PlanStep]
    rationale: str
    risks: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    confidence: float = 0.8

    def get_next_step(self) -> Optional[PlanStep]:
        """Get the next incomplete step."""
        for step in self.steps:
            if not step.completed:
                # Check if dependencies are met
                if all(self.steps[dep - 1].completed for dep in step.dependencies):
                    return step
        return None

    def mark_step_complete(self, step_number: int, result: str) -> None:
        """Mark a step as completed with its result."""
        if 0 < step_number <= len(self.steps):
            self.steps[step_number - 1].completed = True
            self.steps[step_number - 1].result = result

    def get_progress(self) -> float:
        """Get completion progress as percentage."""
        if not self.steps:
            return 0.0
        completed = sum(1 for step in self.steps if step.completed)
        return (completed / len(self.steps)) * 100

    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return all(step.completed for step in self.steps)

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary."""
        return {
            "task": self.task,
            "complexity": self.complexity,
            "total_steps": self.total_steps,
            "steps": [step.to_dict() for step in self.steps],
            "rationale": self.rationale,
            "risks": self.risks,
            "prerequisites": self.prerequisites,
            "status": self.status.value,
            "confidence": self.confidence,
            "progress": self.get_progress(),
        }


class DynamicPlanner:
    """Generates and manages dynamic execution plans using LLM reasoning."""

    def __init__(self, ollama_client=None, planning_model: str = "qwen2.5-coder:7b"):
        """Initialize the dynamic planner.

        Args:
            ollama_client: Optional Ollama client for LLM-based planning
            planning_model: Model to use for plan generation
        """
        self.ollama_client = ollama_client
        self.planning_model = planning_model

    async def generate_plan(
        self,
        task: str,
        complexity: str,
        context: Optional[str] = None
    ) -> ExecutionPlan:
        """Generate an execution plan for a task.

        Args:
            task: The task description
            complexity: Task complexity (SIMPLE, MODERATE, COMPLEX)
            context: Optional context about the codebase/environment

        Returns:
            ExecutionPlan with steps tailored to the task
        """
        # If no LLM client, use heuristic planning
        if not self.ollama_client:
            return self._generate_heuristic_plan(task, complexity, context)

        try:
            # Generate plan using LLM
            return await self._generate_llm_plan(task, complexity, context)
        except Exception:
            # Fallback to heuristic
            return self._generate_heuristic_plan(task, complexity, context)

    def _generate_heuristic_plan(
        self,
        task: str,
        complexity: str,
        context: Optional[str] = None
    ) -> ExecutionPlan:
        """Generate a plan using heuristic rules.

        This is a fallback when LLM is unavailable or fails.

        Args:
            task: Task description
            complexity: Task complexity level
            context: Optional context

        Returns:
            ExecutionPlan with basic structure
        """
        task_lower = task.lower()
        steps: List[PlanStep] = []

        # Determine plan structure based on keywords and complexity
        # Check analysis tasks first (more specific)
        if any(word in task_lower for word in ["analyze", "review", "understand", "explain"]):
            # Analysis task
            steps.append(PlanStep(
                step_number=1,
                type=PlanStepType.EXPLORATION,
                description="Gather relevant code and documentation",
                rationale="Collect information for analysis",
                expected_tools=["read_file", "search_files"],
                success_criteria="All relevant files identified"
            ))

            steps.append(PlanStep(
                step_number=2,
                type=PlanStepType.ANALYSIS,
                description="Analyze the findings",
                rationale="Deep dive into the code/patterns",
                dependencies=[1],
                success_criteria="Comprehensive analysis complete"
            ))

        elif any(word in task_lower for word in ["implement", "create", "build", "add"]):
            # Implementation task
            steps.append(PlanStep(
                step_number=1,
                type=PlanStepType.EXPLORATION,
                description=f"Explore existing code related to: {task}",
                rationale="Understand current implementation before making changes",
                expected_tools=["read_file", "search_files"],
                success_criteria="Found relevant files and patterns"
            ))

            if complexity in ["MODERATE", "COMPLEX"]:
                steps.append(PlanStep(
                    step_number=2,
                    type=PlanStepType.DESIGN,
                    description="Design the solution approach",
                    rationale="Plan implementation strategy before coding",
                    dependencies=[1],
                    success_criteria="Clear design documented"
                ))

            impl_step = len(steps) + 1
            steps.append(PlanStep(
                step_number=impl_step,
                type=PlanStepType.IMPLEMENTATION,
                description="Implement the solution",
                rationale="Execute the planned changes",
                expected_tools=["write_file", "edit_file"],
                dependencies=[impl_step - 1] if len(steps) > 1 else [],
                success_criteria="Code written and functional"
            ))

            if complexity == "COMPLEX":
                steps.append(PlanStep(
                    step_number=len(steps) + 1,
                    type=PlanStepType.TESTING,
                    description="Write and run tests",
                    rationale="Verify implementation correctness",
                    expected_tools=["write_file", "execute_command"],
                    dependencies=[impl_step],
                    success_criteria="Tests pass"
                ))

        elif any(word in task_lower for word in ["fix", "debug", "resolve"]):
            # Bug fix task
            steps.append(PlanStep(
                step_number=1,
                type=PlanStepType.EXPLORATION,
                description="Locate the bug and understand the issue",
                rationale="Identify root cause before fixing",
                expected_tools=["read_file", "search_files", "git_log"],
                success_criteria="Bug root cause identified"
            ))

            steps.append(PlanStep(
                step_number=2,
                type=PlanStepType.IMPLEMENTATION,
                description="Fix the bug",
                rationale="Apply the fix",
                expected_tools=["write_file", "edit_file"],
                dependencies=[1],
                success_criteria="Bug fixed"
            ))

            steps.append(PlanStep(
                step_number=3,
                type=PlanStepType.VALIDATION,
                description="Verify the fix works",
                rationale="Ensure bug is resolved",
                expected_tools=["execute_command"],
                dependencies=[2],
                success_criteria="Fix verified"
            ))

        else:
            # Generic task
            steps.append(PlanStep(
                step_number=1,
                type=PlanStepType.EXPLORATION,
                description=f"Investigate: {task}",
                rationale="Gather information about the task",
                expected_tools=["read_file", "search_files"],
                success_criteria="Relevant information gathered"
            ))

            steps.append(PlanStep(
                step_number=2,
                type=PlanStepType.IMPLEMENTATION,
                description="Execute the task",
                rationale="Complete the requested work",
                dependencies=[1],
                success_criteria="Task completed"
            ))

        return ExecutionPlan(
            task=task,
            complexity=complexity,
            total_steps=len(steps),
            steps=steps,
            rationale=f"Heuristic plan for {complexity.lower()} task",
            confidence=0.7,  # Lower confidence for heuristic plans
        )

    async def _generate_llm_plan(
        self,
        task: str,
        complexity: str,
        context: Optional[str] = None
    ) -> ExecutionPlan:
        """Generate a plan using LLM reasoning.

        Args:
            task: Task description
            complexity: Task complexity level
            context: Optional context

        Returns:
            ExecutionPlan generated by LLM
        """
        # Build prompt for plan generation
        prompt = self._build_planning_prompt(task, complexity, context)

        # Switch to planning model if needed
        original_model = None
        if hasattr(self.ollama_client, 'get_current_model'):
            original_model = self.ollama_client.get_current_model()
            if original_model != self.planning_model:
                self.ollama_client.switch_model(self.planning_model, verbose=False)

        try:
            # Get plan from LLM
            response = await self.ollama_client.chat_simple(prompt)

            # Parse the response
            plan = self._parse_llm_plan(response, task, complexity)

            return plan

        finally:
            # Restore original model
            if original_model and original_model != self.planning_model:
                self.ollama_client.switch_model(original_model, verbose=False)

    def _build_planning_prompt(
        self,
        task: str,
        complexity: str,
        context: Optional[str] = None
    ) -> str:
        """Build prompt for LLM plan generation.

        Args:
            task: Task description
            complexity: Task complexity
            context: Optional context

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert software engineer creating an execution plan for a task.

TASK: {task}
COMPLEXITY: {complexity}
CONTEXT: {context if context else "None provided"}

Generate a detailed execution plan with the following format:

RATIONALE: [Why this approach is best for this task]

STEP 1:
TYPE: [exploration/analysis/design/implementation/testing/documentation/validation]
DESCRIPTION: [What to do in this step]
RATIONALE: [Why this step is needed]
TOOLS: [Expected tools: read_file, write_file, search_files, execute_command, git_*, etc.]
SUCCESS_CRITERIA: [How to know this step succeeded]
DEPENDENCIES: [Step numbers this depends on, or "none"]
DURATION: [quick/medium/long]

STEP 2:
...

RISKS: [Potential risks or challenges]
PREREQUISITES: [Any prerequisites needed]
CONFIDENCE: [0.0-1.0 confidence in this plan]

Guidelines:
- For SIMPLE tasks: 1-2 steps
- For MODERATE tasks: 2-4 steps
- For COMPLEX tasks: 5-8 steps
- Start with exploration/analysis when needed
- Include design steps for complex changes
- End with testing/validation for implementations
- Be specific and actionable
"""
        return prompt

    def _parse_llm_plan(
        self,
        response: str,
        task: str,
        complexity: str
    ) -> ExecutionPlan:
        """Parse LLM response into ExecutionPlan.

        Args:
            response: LLM response text
            task: Original task
            complexity: Task complexity

        Returns:
            Parsed ExecutionPlan
        """
        lines = response.strip().split('\n')

        # Extract rationale
        rationale = ""
        rationale_match = re.search(r'RATIONALE:\s*(.+?)(?=\n\nSTEP|\nSTEP|$)', response, re.DOTALL)
        if rationale_match:
            rationale = rationale_match.group(1).strip()

        # Extract risks
        risks = []
        risks_match = re.search(r'RISKS?:\s*(.+?)(?=\n\n|PREREQUISITES|CONFIDENCE|$)', response, re.DOTALL)
        if risks_match:
            risks_text = risks_match.group(1).strip()
            # Split on newlines or commas
            if '\n' in risks_text:
                risks = [r.strip('- ').strip() for r in risks_text.split('\n') if r.strip()]
            else:
                risks = [r.strip() for r in risks_text.split(',') if r.strip()]

        # Extract prerequisites
        prerequisites = []
        prereq_match = re.search(r'PREREQUISITES?:\s*(.+?)(?=\n\n|CONFIDENCE|$)', response, re.DOTALL)
        if prereq_match:
            prereq_text = prereq_match.group(1).strip()
            # Split on newlines or commas
            if '\n' in prereq_text:
                prerequisites = [p.strip('- ').strip() for p in prereq_text.split('\n') if p.strip()]
            else:
                prerequisites = [p.strip() for p in prereq_text.split(',') if p.strip()]

        # Extract confidence
        confidence = 0.8
        conf_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', response)
        if conf_match:
            confidence = float(conf_match.group(1))

        # Extract steps
        steps = []
        step_pattern = r'STEP (\d+):\s*\n(.*?)(?=\nSTEP \d+:|\nRISKS?:|\nPREREQUISITES?:|\nCONFIDENCE:|$)'
        step_matches = re.finditer(step_pattern, response, re.DOTALL)

        for match in step_matches:
            step_num = int(match.group(1))
            step_text = match.group(2).strip()

            # Parse step fields
            type_match = re.search(r'TYPE:\s*(\w+)', step_text, re.IGNORECASE)
            desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?=\nRATIONALE|\nTOOLS|\nSUCCESS|\nDEPENDENCIES|\nDURATION|$)', step_text, re.DOTALL | re.IGNORECASE)
            rat_match = re.search(r'RATIONALE:\s*(.+?)(?=\nTOOLS|\nSUCCESS|\nDEPENDENCIES|\nDURATION|$)', step_text, re.DOTALL | re.IGNORECASE)
            tools_match = re.search(r'TOOLS:\s*(.+?)(?=\nSUCCESS|\nDEPENDENCIES|\nDURATION|$)', step_text, re.DOTALL | re.IGNORECASE)
            success_match = re.search(r'SUCCESS_CRITERIA:\s*(.+?)(?=\nDEPENDENCIES|\nDURATION|$)', step_text, re.DOTALL | re.IGNORECASE)
            dep_match = re.search(r'DEPENDENCIES:\s*(.+?)(?=\nDURATION|$)', step_text, re.DOTALL | re.IGNORECASE)
            dur_match = re.search(r'DURATION:\s*(\w+)', step_text, re.IGNORECASE)

            # Parse step type
            step_type = PlanStepType.IMPLEMENTATION
            if type_match:
                type_str = type_match.group(1).lower()
                for pst in PlanStepType:
                    if pst.value == type_str:
                        step_type = pst
                        break

            # Parse dependencies
            dependencies = []
            if dep_match:
                dep_text = dep_match.group(1).strip().lower()
                if dep_text != "none":
                    # Extract numbers from dependency text
                    dep_nums = re.findall(r'\d+', dep_text)
                    dependencies = [int(d) for d in dep_nums]

            # Parse tools
            tools = []
            if tools_match:
                tools_text = tools_match.group(1).strip()
                tools = [t.strip('[], ') for t in re.split(r'[,\s]+', tools_text) if t.strip()]

            step = PlanStep(
                step_number=step_num,
                type=step_type,
                description=desc_match.group(1).strip() if desc_match else f"Step {step_num}",
                rationale=rat_match.group(1).strip() if rat_match else "",
                expected_tools=tools,
                success_criteria=success_match.group(1).strip() if success_match else "",
                dependencies=dependencies,
                estimated_duration=dur_match.group(1).strip() if dur_match else "quick",
            )
            steps.append(step)

        # If no steps parsed, create a basic plan
        if not steps:
            steps = [
                PlanStep(
                    step_number=1,
                    type=PlanStepType.IMPLEMENTATION,
                    description=task,
                    rationale="Execute the task",
                    success_criteria="Task completed"
                )
            ]

        return ExecutionPlan(
            task=task,
            complexity=complexity,
            total_steps=len(steps),
            steps=steps,
            rationale=rationale or f"Plan for {complexity.lower()} task",
            risks=risks,
            prerequisites=prerequisites,
            confidence=confidence,
        )

    async def refine_plan(
        self,
        plan: ExecutionPlan,
        new_information: str
    ) -> ExecutionPlan:
        """Refine a plan based on new discoveries.

        Args:
            plan: Current execution plan
            new_information: New information discovered during execution

        Returns:
            Refined ExecutionPlan
        """
        if not self.ollama_client:
            # Can't refine without LLM
            return plan

        prompt = f"""You are refining an execution plan based on new discoveries.

ORIGINAL TASK: {plan.task}
ORIGINAL PLAN: {len(plan.steps)} steps
PROGRESS: {plan.get_progress():.0f}% complete

NEW INFORMATION:
{new_information}

Should the plan be modified? If yes, provide:
1. What should change (add steps, remove steps, reorder, etc.)
2. Why the change is needed
3. Updated step list

If no changes needed, respond with: NO_CHANGES_NEEDED
"""

        try:
            response = await self.ollama_client.chat_simple(prompt)

            if "NO_CHANGES_NEEDED" in response.upper():
                return plan

            # Parse refinement and apply changes
            # For now, return the original plan with status updated
            plan.status = PlanStatus.REFINED
            return plan

        except Exception:
            return plan

    def validate_plan(self, plan: ExecutionPlan) -> bool:
        """Validate a plan for feasibility.

        Args:
            plan: ExecutionPlan to validate

        Returns:
            True if plan is valid and feasible
        """
        # Check basic validity
        if not plan.steps:
            return False

        # Check step numbers are sequential
        for i, step in enumerate(plan.steps, 1):
            if step.step_number != i:
                return False

        # Check dependencies are valid
        for step in plan.steps:
            for dep in step.dependencies:
                if dep < 1 or dep >= step.step_number:
                    return False

        # Check total_steps matches actual steps
        if plan.total_steps != len(plan.steps):
            return False

        return True

"""Tests for DynamicPlanner and execution plan generation."""

import pytest
from unittest.mock import Mock, AsyncMock
from hrisa_code.core.planning import (
    DynamicPlanner,
    ExecutionPlan,
    PlanStep,
    PlanStepType,
    PlanStatus,
)


class TestPlanStep:
    """Tests for PlanStep data model."""

    def test_plan_step_creation(self):
        """Test creating a PlanStep."""
        step = PlanStep(
            step_number=1,
            type=PlanStepType.EXPLORATION,
            description="Explore the codebase",
            rationale="Understand existing patterns",
        )

        assert step.step_number == 1
        assert step.type == PlanStepType.EXPLORATION
        assert step.description == "Explore the codebase"
        assert step.rationale == "Understand existing patterns"
        assert not step.completed
        assert step.result is None

    def test_plan_step_with_dependencies(self):
        """Test PlanStep with dependencies."""
        step = PlanStep(
            step_number=3,
            type=PlanStepType.IMPLEMENTATION,
            description="Implement feature",
            rationale="Build the solution",
            dependencies=[1, 2],
        )

        assert step.dependencies == [1, 2]

    def test_plan_step_to_dict(self):
        """Test converting PlanStep to dictionary."""
        step = PlanStep(
            step_number=1,
            type=PlanStepType.DESIGN,
            description="Design solution",
            rationale="Plan approach",
            expected_tools=["read_file", "write_file"],
            success_criteria="Design documented",
        )

        result = step.to_dict()

        assert result["step_number"] == 1
        assert result["type"] == "design"
        assert result["description"] == "Design solution"
        assert result["expected_tools"] == ["read_file", "write_file"]
        assert result["success_criteria"] == "Design documented"


class TestExecutionPlan:
    """Tests for ExecutionPlan data model."""

    def test_execution_plan_creation(self):
        """Test creating an ExecutionPlan."""
        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Explore", "Understand"),
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Implement", "Build"),
        ]

        plan = ExecutionPlan(
            task="Add logging",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Multi-step implementation",
        )

        assert plan.task == "Add logging"
        assert plan.complexity == "MODERATE"
        assert plan.total_steps == 2
        assert len(plan.steps) == 2
        assert plan.status == PlanStatus.DRAFT

    def test_get_next_step_no_dependencies(self):
        """Test getting next step when no dependencies."""
        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First"),
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Step 2", "Second"),
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="SIMPLE",
            total_steps=2,
            steps=steps,
            rationale="Test",
        )

        next_step = plan.get_next_step()
        assert next_step is not None
        assert next_step.step_number == 1

    def test_get_next_step_with_dependencies(self):
        """Test getting next step respects dependencies."""
        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First"),
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Step 2", "Second", dependencies=[1]),
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test",
        )

        # First step should be next
        next_step = plan.get_next_step()
        assert next_step.step_number == 1

        # Mark first complete, second should be next
        plan.mark_step_complete(1, "Done")
        next_step = plan.get_next_step()
        assert next_step.step_number == 2

    def test_get_next_step_blocked_by_dependency(self):
        """Test that step with unmet dependency is not returned."""
        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First"),
            PlanStep(2, PlanStepType.DESIGN, "Step 2", "Second", dependencies=[1]),
            PlanStep(3, PlanStepType.IMPLEMENTATION, "Step 3", "Third", dependencies=[2]),
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="COMPLEX",
            total_steps=3,
            steps=steps,
            rationale="Test",
        )

        # Only step 1 should be available
        next_step = plan.get_next_step()
        assert next_step.step_number == 1

        # Complete step 1, step 2 should be available
        plan.mark_step_complete(1, "Done")
        next_step = plan.get_next_step()
        assert next_step.step_number == 2

        # Step 3 still blocked
        next_step = plan.get_next_step()
        assert next_step.step_number == 2  # Still step 2

        # Complete step 2, step 3 available
        plan.mark_step_complete(2, "Done")
        next_step = plan.get_next_step()
        assert next_step.step_number == 3

    def test_mark_step_complete(self):
        """Test marking a step as completed."""
        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First"),
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="SIMPLE",
            total_steps=1,
            steps=steps,
            rationale="Test",
        )

        plan.mark_step_complete(1, "Step completed successfully")

        assert plan.steps[0].completed
        assert plan.steps[0].result == "Step completed successfully"

    def test_get_progress(self):
        """Test calculating progress percentage."""
        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First"),
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Step 2", "Second"),
            PlanStep(3, PlanStepType.TESTING, "Step 3", "Third"),
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=3,
            steps=steps,
            rationale="Test",
        )

        assert plan.get_progress() == 0.0

        plan.mark_step_complete(1, "Done")
        assert plan.get_progress() == pytest.approx(33.33, rel=0.1)

        plan.mark_step_complete(2, "Done")
        assert plan.get_progress() == pytest.approx(66.67, rel=0.1)

        plan.mark_step_complete(3, "Done")
        assert plan.get_progress() == 100.0

    def test_is_complete(self):
        """Test checking if plan is complete."""
        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First"),
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Step 2", "Second"),
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test",
        )

        assert not plan.is_complete()

        plan.mark_step_complete(1, "Done")
        assert not plan.is_complete()

        plan.mark_step_complete(2, "Done")
        assert plan.is_complete()

    def test_to_dict(self):
        """Test converting ExecutionPlan to dictionary."""
        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Explore", "Understand"),
        ]

        plan = ExecutionPlan(
            task="Add feature",
            complexity="MODERATE",
            total_steps=1,
            steps=steps,
            rationale="Implementation plan",
            risks=["Risk 1"],
            prerequisites=["Prereq 1"],
            confidence=0.85,
        )

        result = plan.to_dict()

        assert result["task"] == "Add feature"
        assert result["complexity"] == "MODERATE"
        assert result["total_steps"] == 1
        assert len(result["steps"]) == 1
        assert result["rationale"] == "Implementation plan"
        assert result["risks"] == ["Risk 1"]
        assert result["prerequisites"] == ["Prereq 1"]
        assert result["confidence"] == 0.85
        assert result["progress"] == 0.0


class TestDynamicPlannerInitialization:
    """Tests for DynamicPlanner initialization."""

    def test_initialization_without_client(self):
        """Test initializing planner without Ollama client."""
        planner = DynamicPlanner()

        assert planner.ollama_client is None
        assert planner.planning_model == "qwen2.5-coder:7b"

    def test_initialization_with_client(self):
        """Test initializing planner with Ollama client."""
        mock_client = Mock()
        planner = DynamicPlanner(ollama_client=mock_client, planning_model="custom:model")

        assert planner.ollama_client is mock_client
        assert planner.planning_model == "custom:model"


class TestHeuristicPlanning:
    """Tests for heuristic-based plan generation."""

    def test_heuristic_implementation_plan(self):
        """Test generating heuristic plan for implementation task."""
        planner = DynamicPlanner()

        plan = planner._generate_heuristic_plan(
            task="Implement user authentication",
            complexity="COMPLEX",
            context=None
        )

        assert plan.task == "Implement user authentication"
        assert plan.complexity == "COMPLEX"
        assert len(plan.steps) > 0
        assert any(step.type == PlanStepType.EXPLORATION for step in plan.steps)
        assert any(step.type == PlanStepType.IMPLEMENTATION for step in plan.steps)
        assert plan.confidence == 0.7  # Heuristic plans have lower confidence

    def test_heuristic_analysis_plan(self):
        """Test generating heuristic plan for analysis task."""
        planner = DynamicPlanner()

        plan = planner._generate_heuristic_plan(
            task="Analyze the complexity detector implementation",
            complexity="MODERATE",
            context=None
        )

        assert "analyze" in plan.task.lower()
        assert len(plan.steps) >= 2
        assert plan.steps[0].type == PlanStepType.EXPLORATION
        assert plan.steps[1].type == PlanStepType.ANALYSIS

    def test_heuristic_bug_fix_plan(self):
        """Test generating heuristic plan for bug fix task."""
        planner = DynamicPlanner()

        plan = planner._generate_heuristic_plan(
            task="Fix the parsing bug in complexity detector",
            complexity="MODERATE",
            context=None
        )

        assert len(plan.steps) == 3
        assert plan.steps[0].type == PlanStepType.EXPLORATION
        assert plan.steps[1].type == PlanStepType.IMPLEMENTATION
        assert plan.steps[2].type == PlanStepType.VALIDATION

    def test_heuristic_simple_task_plan(self):
        """Test heuristic plan for simple task."""
        planner = DynamicPlanner()

        plan = planner._generate_heuristic_plan(
            task="List all Python files",
            complexity="SIMPLE",
            context=None
        )

        assert plan.complexity == "SIMPLE"
        assert len(plan.steps) >= 1

    def test_heuristic_moderate_adds_design(self):
        """Test that MODERATE implementation tasks include design step."""
        planner = DynamicPlanner()

        plan = planner._generate_heuristic_plan(
            task="Add logging to API endpoints",
            complexity="MODERATE",
            context=None
        )

        assert any(step.type == PlanStepType.DESIGN for step in plan.steps)

    def test_heuristic_complex_adds_testing(self):
        """Test that COMPLEX implementation tasks include testing step."""
        planner = DynamicPlanner()

        plan = planner._generate_heuristic_plan(
            task="Implement caching system",
            complexity="COMPLEX",
            context=None
        )

        assert any(step.type == PlanStepType.TESTING for step in plan.steps)


class TestLLMPlanning:
    """Tests for LLM-based plan generation."""

    @pytest.mark.asyncio
    async def test_generate_plan_without_client_uses_heuristic(self):
        """Test that plan generation falls back to heuristic without client."""
        planner = DynamicPlanner(ollama_client=None)

        plan = await planner.generate_plan(
            task="Implement feature",
            complexity="MODERATE",
            context=None
        )

        assert isinstance(plan, ExecutionPlan)
        assert plan.confidence == 0.7  # Heuristic confidence

    @pytest.mark.asyncio
    async def test_generate_plan_with_llm(self):
        """Test LLM-based plan generation."""
        mock_client = Mock()
        mock_client.get_current_model = Mock(return_value="qwen2.5-coder:32b")
        mock_client.switch_model = Mock()
        mock_client.chat_simple = AsyncMock(return_value="""
RATIONALE: This implementation requires careful exploration and design

STEP 1:
TYPE: exploration
DESCRIPTION: Explore existing authentication patterns
RATIONALE: Understand current setup
TOOLS: read_file, search_files
SUCCESS_CRITERIA: Found auth-related code
DEPENDENCIES: none
DURATION: medium

STEP 2:
TYPE: design
DESCRIPTION: Design authentication flow
RATIONALE: Plan the implementation
TOOLS: none
SUCCESS_CRITERIA: Design documented
DEPENDENCIES: 1
DURATION: medium

STEP 3:
TYPE: implementation
DESCRIPTION: Implement authentication
RATIONALE: Build the feature
TOOLS: write_file, edit_file
SUCCESS_CRITERIA: Auth working
DEPENDENCIES: 2
DURATION: long

RISKS: Integration complexity, security considerations
PREREQUISITES: None
CONFIDENCE: 0.85
""")

        planner = DynamicPlanner(
            ollama_client=mock_client,
            planning_model="qwen2.5-coder:7b"
        )

        plan = await planner.generate_plan(
            task="Implement authentication",
            complexity="COMPLEX",
            context="Existing app has user management"
        )

        assert plan.task == "Implement authentication"
        assert plan.complexity == "COMPLEX"
        assert len(plan.steps) == 3
        assert plan.steps[0].type == PlanStepType.EXPLORATION
        assert plan.steps[1].type == PlanStepType.DESIGN
        assert plan.steps[2].type == PlanStepType.IMPLEMENTATION
        assert plan.confidence == 0.85
        assert len(plan.risks) > 0

    @pytest.mark.asyncio
    async def test_generate_plan_llm_fallback_on_error(self):
        """Test that LLM planning falls back to heuristic on error."""
        mock_client = Mock()
        mock_client.get_current_model = Mock(side_effect=Exception("API Error"))

        planner = DynamicPlanner(ollama_client=mock_client)

        plan = await planner.generate_plan(
            task="Add feature",
            complexity="MODERATE",
            context=None
        )

        # Should get heuristic plan
        assert isinstance(plan, ExecutionPlan)
        assert plan.confidence == 0.7

    @pytest.mark.asyncio
    async def test_generate_plan_model_switching(self):
        """Test that planner switches to planning model and back."""
        mock_client = Mock()
        mock_client.get_current_model = Mock(return_value="main-model")
        mock_client.switch_model = Mock()
        mock_client.chat_simple = AsyncMock(return_value="STEP 1:\nTYPE: implementation\nDESCRIPTION: Do task\nRATIONALE: Complete it\nDEPENDENCIES: none\nDURATION: quick")

        planner = DynamicPlanner(
            ollama_client=mock_client,
            planning_model="planning-model"
        )

        await planner.generate_plan("test task", "SIMPLE", None)

        # Verify model was switched
        assert mock_client.switch_model.call_count == 2
        mock_client.switch_model.assert_any_call("planning-model", verbose=False)
        mock_client.switch_model.assert_any_call("main-model", verbose=False)


class TestPlanParsing:
    """Tests for parsing LLM responses into plans."""

    def test_parse_llm_plan_basic(self):
        """Test parsing a basic LLM response."""
        planner = DynamicPlanner()

        response = """
RATIONALE: Simple task execution

STEP 1:
TYPE: implementation
DESCRIPTION: Execute the task
RATIONALE: Complete the work
TOOLS: write_file
SUCCESS_CRITERIA: Task done
DEPENDENCIES: none
DURATION: quick

CONFIDENCE: 0.9
"""

        plan = planner._parse_llm_plan(response, "Test task", "SIMPLE")

        assert plan.task == "Test task"
        assert plan.complexity == "SIMPLE"
        assert len(plan.steps) == 1
        assert plan.steps[0].type == PlanStepType.IMPLEMENTATION
        assert plan.confidence == 0.9

    def test_parse_llm_plan_with_risks(self):
        """Test parsing plan with risks."""
        planner = DynamicPlanner()

        response = """
RATIONALE: Complex implementation

STEP 1:
TYPE: exploration
DESCRIPTION: Explore
RATIONALE: Understand
DEPENDENCIES: none
DURATION: quick

RISKS: Integration issues, performance concerns
CONFIDENCE: 0.75
"""

        plan = planner._parse_llm_plan(response, "Task", "COMPLEX")

        assert len(plan.risks) == 2
        assert "Integration issues" in plan.risks
        assert "performance concerns" in plan.risks

    def test_parse_llm_plan_with_prerequisites(self):
        """Test parsing plan with prerequisites."""
        planner = DynamicPlanner()

        response = """
STEP 1:
TYPE: implementation
DESCRIPTION: Do work
RATIONALE: Complete task
DEPENDENCIES: none
DURATION: quick

PREREQUISITES: Database setup, API keys configured
"""

        plan = planner._parse_llm_plan(response, "Task", "MODERATE")

        assert len(plan.prerequisites) == 2
        assert "Database setup" in plan.prerequisites

    def test_parse_llm_plan_malformed_fallback(self):
        """Test parsing malformed response creates basic plan."""
        planner = DynamicPlanner()

        response = "This is a malformed response with no structure"

        plan = planner._parse_llm_plan(response, "Test task", "SIMPLE")

        # Should create a basic fallback plan
        assert len(plan.steps) == 1
        assert plan.steps[0].description == "Test task"


class TestPlanValidation:
    """Tests for plan validation."""

    def test_validate_valid_plan(self):
        """Test validating a valid plan."""
        planner = DynamicPlanner()

        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First"),
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Step 2", "Second", dependencies=[1]),
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test",
        )

        assert planner.validate_plan(plan)

    def test_validate_empty_plan(self):
        """Test that plan with no steps is invalid."""
        planner = DynamicPlanner()

        plan = ExecutionPlan(
            task="Test",
            complexity="SIMPLE",
            total_steps=0,
            steps=[],
            rationale="Test",
        )

        assert not planner.validate_plan(plan)

    def test_validate_invalid_step_numbers(self):
        """Test that non-sequential step numbers are invalid."""
        planner = DynamicPlanner()

        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First"),
            PlanStep(3, PlanStepType.IMPLEMENTATION, "Step 3", "Third"),  # Missing 2
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test",
        )

        assert not planner.validate_plan(plan)

    def test_validate_invalid_dependencies(self):
        """Test that invalid dependencies are caught."""
        planner = DynamicPlanner()

        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First", dependencies=[2]),  # Forward ref
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Step 2", "Second"),
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test",
        )

        assert not planner.validate_plan(plan)

    def test_validate_mismatched_total_steps(self):
        """Test that mismatched total_steps is invalid."""
        planner = DynamicPlanner()

        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First"),
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="SIMPLE",
            total_steps=5,  # Says 5 but only 1 step
            steps=steps,
            rationale="Test",
        )

        assert not planner.validate_plan(plan)


class TestPlanRefinement:
    """Tests for plan refinement based on discoveries."""

    @pytest.mark.asyncio
    async def test_refine_plan_without_client(self):
        """Test that refinement without client returns original plan."""
        planner = DynamicPlanner(ollama_client=None)

        steps = [PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First")]
        plan = ExecutionPlan(
            task="Test",
            complexity="SIMPLE",
            total_steps=1,
            steps=steps,
            rationale="Test",
        )

        refined = await planner.refine_plan(plan, "New information discovered")

        # Should return same plan
        assert refined.task == plan.task
        assert len(refined.steps) == len(plan.steps)

    @pytest.mark.asyncio
    async def test_refine_plan_no_changes_needed(self):
        """Test refinement when no changes needed."""
        mock_client = Mock()
        mock_client.chat_simple = AsyncMock(return_value="NO_CHANGES_NEEDED")

        planner = DynamicPlanner(ollama_client=mock_client)

        steps = [PlanStep(1, PlanStepType.EXPLORATION, "Step 1", "First")]
        plan = ExecutionPlan(
            task="Test",
            complexity="SIMPLE",
            total_steps=1,
            steps=steps,
            rationale="Test",
        )

        refined = await planner.refine_plan(plan, "Minor discovery")

        assert refined.task == plan.task

    @pytest.mark.asyncio
    async def test_refine_plan_updates_status(self):
        """Test that refinement updates plan status."""
        mock_client = Mock()
        mock_client.chat_simple = AsyncMock(return_value="Add step for error handling")

        planner = DynamicPlanner(ollama_client=mock_client)

        steps = [PlanStep(1, PlanStepType.IMPLEMENTATION, "Step 1", "First")]
        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=1,
            steps=steps,
            rationale="Test",
            status=PlanStatus.IN_PROGRESS,
        )

        refined = await planner.refine_plan(plan, "Found error handling needed")

        assert refined.status == PlanStatus.REFINED

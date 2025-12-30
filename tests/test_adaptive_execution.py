"""Tests for adaptive execution in AgentLoop."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from hrisa_code.core.planning import (
    AgentLoop,
    ExecutionPlan,
    PlanStep,
    PlanStepType,
    PlanStatus,
)


class TestExecuteWithPlan:
    """Tests for execute_with_plan method."""

    @pytest.mark.asyncio
    async def test_execute_with_plan_provided(self):
        """Test executing with a pre-generated plan."""
        # Setup
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test prompt"
        mock_conv.process_message = AsyncMock(return_value="Step completed")

        agent = AgentLoop(mock_conv)

        # Create a simple plan
        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Explore code", "Understand codebase"),
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Implement feature", "Build solution", dependencies=[1]),
        ]

        plan = ExecutionPlan(
            task="Add logging",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test plan",
        )

        # Execute
        result = await agent.execute_with_plan("Add logging", plan)

        # Verify
        assert result == "Step completed"
        assert plan.is_complete()
        assert mock_conv.process_message.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_plan_generates_plan(self):
        """Test that plan is generated if not provided."""
        # Setup
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test prompt"
        mock_conv.process_message = AsyncMock(return_value="Done")

        agent = AgentLoop(mock_conv)

        # Mock complexity detector
        with patch.object(agent.complexity_detector, 'analyze') as mock_analyze:
            mock_analysis = Mock()
            mock_analysis.complexity.value = "moderate"
            mock_analyze.return_value = mock_analysis

            # Mock plan generation
            with patch.object(agent.dynamic_planner, 'generate_plan') as mock_generate:
                steps = [PlanStep(1, PlanStepType.IMPLEMENTATION, "Do task", "Complete it")]
                mock_plan = ExecutionPlan(
                    task="Test task",
                    complexity="MODERATE",
                    total_steps=1,
                    steps=steps,
                    rationale="Test",
                )
                mock_generate.return_value = mock_plan

                # Execute
                result = await agent.execute_with_plan("Test task")

                # Verify plan was generated
                mock_analyze.assert_called_once_with("Test task")
                mock_generate.assert_called_once()
                assert result == "Done"

    @pytest.mark.asyncio
    async def test_execute_with_plan_respects_dependencies(self):
        """Test that step dependencies are respected."""
        # Setup
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test prompt"

        call_order = []

        async def track_calls(prompt):
            if "Step 1" in prompt:
                call_order.append(1)
            elif "Step 2" in prompt:
                call_order.append(2)
            return "Done"

        mock_conv.process_message = AsyncMock(side_effect=track_calls)

        agent = AgentLoop(mock_conv)

        # Create plan with dependencies
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

        # Execute
        await agent.execute_with_plan("Test", plan)

        # Verify order
        assert call_order == [1, 2]

    @pytest.mark.asyncio
    async def test_execute_with_plan_tracks_progress(self):
        """Test that progress is tracked correctly."""
        # Setup
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test prompt"
        mock_conv.process_message = AsyncMock(return_value="Done")

        agent = AgentLoop(mock_conv)

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

        # Track progress at each step
        progress_values = []

        original_display = agent._display_step_complete

        def track_progress(step, plan):
            progress_values.append(plan.get_progress())
            original_display(step, plan)

        agent._display_step_complete = track_progress

        # Execute
        await agent.execute_with_plan("Test", plan)

        # Verify progress tracked
        assert len(progress_values) == 2
        assert progress_values[0] == pytest.approx(50.0)
        assert progress_values[1] == pytest.approx(100.0)

    @pytest.mark.asyncio
    async def test_execute_with_plan_handles_errors(self):
        """Test error handling during step execution."""
        # Setup
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test prompt"

        # First step fails, second succeeds
        mock_conv.process_message = AsyncMock(side_effect=[
            Exception("Step failed"),
            "Step 2 done"
        ])

        agent = AgentLoop(mock_conv)

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

        # Execute
        result = await agent.execute_with_plan("Test", plan)

        # Verify error was handled
        assert steps[0].result.startswith("FAILED:")
        assert steps[1].completed
        assert agent.error_count > 0

    @pytest.mark.asyncio
    async def test_execute_with_plan_stops_after_max_errors(self):
        """Test that execution stops after too many errors."""
        # Setup
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test prompt"

        # All steps fail
        mock_conv.process_message = AsyncMock(side_effect=Exception("Failed"))

        agent = AgentLoop(mock_conv)

        steps = [
            PlanStep(i, PlanStepType.IMPLEMENTATION, f"Step {i}", f"Step {i}")
            for i in range(1, 6)
        ]

        plan = ExecutionPlan(
            task="Test",
            complexity="COMPLEX",
            total_steps=5,
            steps=steps,
            rationale="Test",
        )

        # Execute
        await agent.execute_with_plan("Test", plan)

        # Verify stopped after error limit
        assert agent.error_count > 3
        # Not all steps should be attempted
        completed_count = sum(1 for s in steps if s.completed)
        assert completed_count <= 4  # Should stop around 4 due to error limit


class TestStepExecution:
    """Tests for individual step execution."""

    @pytest.mark.asyncio
    async def test_execute_step(self):
        """Test executing a single step."""
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test prompt"
        mock_conv.process_message = AsyncMock(return_value="Step result")

        agent = AgentLoop(mock_conv)

        step = PlanStep(
            1,
            PlanStepType.EXPLORATION,
            "Explore codebase",
            "Understand structure",
            expected_tools=["read_file", "search_files"],
            success_criteria="Files found"
        )

        result = await agent._execute_step(step, "Original task")

        assert result == "Step result"
        mock_conv.process_message.assert_called_once()

        # Check prompt includes step details
        call_args = mock_conv.process_message.call_args[0][0]
        assert "Explore codebase" in call_args
        assert "Understand structure" in call_args
        assert "read_file" in call_args

    def test_build_step_prompt(self):
        """Test building prompt for a step."""
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test"

        agent = AgentLoop(mock_conv)

        step = PlanStep(
            2,
            PlanStepType.DESIGN,
            "Design solution",
            "Plan approach",
            expected_tools=["write_file"],
            success_criteria="Design documented"
        )

        prompt = agent._build_step_prompt(step, "Add authentication")

        assert "Add authentication" in prompt
        assert "Design solution" in prompt
        assert "Plan approach" in prompt
        assert "write_file" in prompt
        assert "Design documented" in prompt


class TestPlanDisplay:
    """Tests for plan display methods."""

    def test_display_plan(self):
        """Test displaying a plan."""
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test"

        agent = AgentLoop(mock_conv)

        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Explore", "Understand"),
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Implement", "Build", dependencies=[1]),
        ]

        plan = ExecutionPlan(
            task="Test task",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test plan",
            risks=["Risk 1"],
        )

        # Should not raise
        agent._display_plan(plan)

    def test_display_step_start(self):
        """Test displaying step start."""
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test"

        agent = AgentLoop(mock_conv)

        step = PlanStep(1, PlanStepType.EXPLORATION, "Explore", "Understand")
        steps = [step, PlanStep(2, PlanStepType.IMPLEMENTATION, "Implement", "Build")]

        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test",
        )

        # Should not raise
        agent._display_step_start(step, plan)

    def test_display_step_complete(self):
        """Test displaying step completion."""
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test"

        agent = AgentLoop(mock_conv)

        step = PlanStep(1, PlanStepType.EXPLORATION, "Explore", "Understand")
        step.completed = True

        steps = [step, PlanStep(2, PlanStepType.IMPLEMENTATION, "Implement", "Build")]

        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test",
        )

        # Should not raise
        agent._display_step_complete(step, plan)

    def test_display_plan_completion_success(self):
        """Test displaying successful plan completion."""
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test"

        agent = AgentLoop(mock_conv)

        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Explore", "Understand"),
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Implement", "Build"),
        ]

        # Mark all complete
        for step in steps:
            step.completed = True

        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test",
        )

        # Should not raise
        agent._display_plan_completion(plan)

    def test_display_plan_completion_incomplete(self):
        """Test displaying incomplete plan."""
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test"

        agent = AgentLoop(mock_conv)

        steps = [
            PlanStep(1, PlanStepType.EXPLORATION, "Explore", "Understand"),
            PlanStep(2, PlanStepType.IMPLEMENTATION, "Implement", "Build"),
        ]

        # Only first complete
        steps[0].completed = True

        plan = ExecutionPlan(
            task="Test",
            complexity="MODERATE",
            total_steps=2,
            steps=steps,
            rationale="Test",
        )

        # Should not raise
        agent._display_plan_completion(plan)


class TestPlanAdaptation:
    """Tests for plan adaptation during execution."""

    @pytest.mark.asyncio
    async def test_plan_refinement_on_discovery(self):
        """Test that plan is refined when unexpected findings occur."""
        # Setup
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test prompt"

        # Step returns unexpected result
        mock_conv.process_message = AsyncMock(return_value="Unexpected: found existing implementation")

        agent = AgentLoop(mock_conv, enable_planning=True)

        # Mock refinement
        with patch.object(agent.dynamic_planner, 'refine_plan') as mock_refine:
            steps = [PlanStep(1, PlanStepType.EXPLORATION, "Explore", "Understand")]
            plan = ExecutionPlan(
                task="Test",
                complexity="SIMPLE",
                total_steps=1,
                steps=steps,
                rationale="Test",
            )

            refined_plan = ExecutionPlan(
                task="Test",
                complexity="SIMPLE",
                total_steps=1,
                steps=steps,
                rationale="Refined",
                status=PlanStatus.REFINED,
            )

            mock_refine.return_value = refined_plan

            # Execute
            await agent.execute_with_plan("Test", plan)

            # Verify refinement was attempted
            mock_refine.assert_called_once()

    @pytest.mark.asyncio
    async def test_plan_not_refined_without_trigger(self):
        """Test that plan is not refined unnecessarily."""
        # Setup
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test prompt"

        # Normal result
        mock_conv.process_message = AsyncMock(return_value="Step completed normally")

        agent = AgentLoop(mock_conv, enable_planning=True)

        # Mock refinement
        with patch.object(agent.dynamic_planner, 'refine_plan') as mock_refine:
            steps = [PlanStep(1, PlanStepType.EXPLORATION, "Explore", "Understand")]
            plan = ExecutionPlan(
                task="Test",
                complexity="SIMPLE",
                total_steps=1,
                steps=steps,
                rationale="Test",
            )

            # Execute
            await agent.execute_with_plan("Test", plan)

            # Verify refinement was NOT called (no "unexpected" in result)
            mock_refine.assert_not_called()


class TestFallbackBehavior:
    """Tests for fallback to regular execution."""

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_plan(self):
        """Test that invalid plans fall back to regular execution."""
        # Setup
        mock_conv = Mock()
        mock_conv.ollama_client = Mock()
        mock_conv.ollama_config = Mock(model="test-model")
        mock_conv.system_prompt = "Test prompt"
        mock_conv.process_message = AsyncMock(return_value="Done")

        agent = AgentLoop(mock_conv)

        # Mock complexity analysis and plan generation
        with patch.object(agent.complexity_detector, 'analyze') as mock_analyze:
            mock_analysis = Mock()
            mock_analysis.complexity.value = "simple"
            mock_analyze.return_value = mock_analysis

            with patch.object(agent.dynamic_planner, 'generate_plan') as mock_generate:
                # Generate invalid plan (mismatched total_steps)
                steps = [PlanStep(1, PlanStepType.IMPLEMENTATION, "Do it", "Complete")]
                invalid_plan = ExecutionPlan(
                    task="Test",
                    complexity="SIMPLE",
                    total_steps=5,  # Wrong!
                    steps=steps,
                    rationale="Test",
                )

                mock_generate.return_value = invalid_plan

                # Mock regular execute_task
                with patch.object(agent, 'execute_task') as mock_execute:
                    mock_execute.return_value = "Fallback result"

                    # Execute
                    result = await agent.execute_with_plan("Test")

                    # Verify fallback was used
                    mock_execute.assert_called_once_with("Test")
                    assert result == "Fallback result"

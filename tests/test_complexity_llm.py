"""Tests for LLM-based complexity analysis."""

import pytest
from unittest.mock import Mock, AsyncMock
from hrisa_code.core.planning.complexity_detector import (
    ComplexityDetector,
    TaskComplexity,
)


class TestLLMBasedAnalysis:
    """Tests for LLM-based complexity analysis."""

    @pytest.mark.asyncio
    async def test_analyze_with_llm_no_client(self):
        """Test that analyze_with_llm falls back to heuristic when no client."""
        detector = ComplexityDetector(ollama_client=None)
        result = await detector.analyze_with_llm("list files")

        # Should fall back to heuristic analysis
        assert result.complexity == TaskComplexity.SIMPLE
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_analyze_with_llm_simple_task(self):
        """Test LLM analysis for simple task."""
        mock_client = Mock()
        mock_client.get_current_model = Mock(return_value="qwen2.5-coder:7b")
        mock_client.switch_model = Mock()
        mock_client.chat_simple = AsyncMock(return_value="""
COMPLEXITY: SIMPLE
CONFIDENCE: 0.95
REASONING: This is a simple file listing operation
INDICATORS: Single operation
ESTIMATED_STEPS: 1
""")

        detector = ComplexityDetector(
            ollama_client=mock_client,
            evaluation_model="qwen2.5-coder:7b"
        )

        result = await detector.analyze_with_llm("list all Python files")

        assert result.complexity == TaskComplexity.SIMPLE
        assert result.confidence == 0.95
        assert result.estimated_steps == 1
        assert "LLM analysis" in result.reasoning

    @pytest.mark.asyncio
    async def test_analyze_with_llm_moderate_task(self):
        """Test LLM analysis for moderate task."""
        mock_client = Mock()
        mock_client.get_current_model = Mock(return_value="model")
        mock_client.switch_model = Mock()
        mock_client.chat_simple = AsyncMock(return_value="""
COMPLEXITY: MODERATE
CONFIDENCE: 0.85
REASONING: Multi-step task requiring exploration and modification
INDICATORS: Exploration, modification
ESTIMATED_STEPS: 3
""")

        detector = ComplexityDetector(ollama_client=mock_client)
        result = await detector.analyze_with_llm("add logging to API")

        assert result.complexity == TaskComplexity.MODERATE
        assert result.confidence == 0.85
        assert result.estimated_steps == 3

    @pytest.mark.asyncio
    async def test_analyze_with_llm_complex_task(self):
        """Test LLM analysis for complex task."""
        mock_client = Mock()
        mock_client.get_current_model = Mock(return_value="model")
        mock_client.switch_model = Mock()
        mock_client.chat_simple = AsyncMock(return_value="""
COMPLEXITY: COMPLEX
CONFIDENCE: 0.90
REASONING: Requires multi-phase orchestration with design, implementation, and testing
INDICATORS: Design requirements, multi-file changes, testing
ESTIMATED_STEPS: 8
""")

        detector = ComplexityDetector(ollama_client=mock_client)
        result = await detector.analyze_with_llm("implement authentication system")

        assert result.complexity == TaskComplexity.COMPLEX
        assert result.confidence == 0.90
        assert result.estimated_steps == 8

    @pytest.mark.asyncio
    async def test_analyze_with_llm_fallback_on_error(self):
        """Test that LLM analysis falls back to heuristic on error."""
        mock_client = Mock()
        mock_client.get_current_model = Mock(side_effect=Exception("API Error"))

        detector = ComplexityDetector(ollama_client=mock_client)
        result = await detector.analyze_with_llm("list files")

        # Should fall back to heuristic
        assert result.complexity == TaskComplexity.SIMPLE

    @pytest.mark.asyncio
    async def test_analyze_with_llm_model_switching(self):
        """Test that LLM analysis switches models correctly."""
        mock_client = Mock()
        mock_client.get_current_model = Mock(return_value="main-model")
        mock_client.switch_model = Mock()
        mock_client.chat_simple = AsyncMock(return_value="COMPLEXITY: SIMPLE\nCONFIDENCE: 0.9\nESTIMATED_STEPS: 1")

        detector = ComplexityDetector(
            ollama_client=mock_client,
            evaluation_model="eval-model"
        )

        await detector.analyze_with_llm("test task")

        # Verify model was switched to evaluation model and back
        assert mock_client.switch_model.call_count == 2
        mock_client.switch_model.assert_any_call("eval-model", verbose=False)
        mock_client.switch_model.assert_any_call("main-model", verbose=False)


class TestLLMPromptBuilding:
    """Tests for LLM prompt building."""

    def test_build_llm_prompt_basic(self):
        """Test basic prompt building."""
        detector = ComplexityDetector()
        prompt = detector._build_llm_prompt("test task", None)

        assert "test task" in prompt
        assert "COMPLEXITY:" in prompt
        assert "SIMPLE" in prompt
        assert "MODERATE" in prompt
        assert "COMPLEX" in prompt
        assert "ESTIMATED_STEPS" in prompt

    def test_build_llm_prompt_with_context(self):
        """Test prompt building with context."""
        detector = ComplexityDetector()
        prompt = detector._build_llm_prompt(
            "add feature",
            "Existing codebase has authentication"
        )

        assert "add feature" in prompt
        assert "authentication" in prompt

    def test_build_llm_prompt_no_context(self):
        """Test prompt building without context."""
        detector = ComplexityDetector()
        prompt = detector._build_llm_prompt("task", None)

        assert "task" in prompt
        assert "None" in prompt


class TestLLMResponseParsing:
    """Tests for parsing LLM responses."""

    def test_parse_llm_response_simple(self):
        """Test parsing response with SIMPLE complexity."""
        detector = ComplexityDetector()
        response = """
COMPLEXITY: SIMPLE
CONFIDENCE: 0.9
REASONING: Single operation
ESTIMATED_STEPS: 1
"""
        result = detector._parse_llm_response(response, "test task")

        assert result.complexity == TaskComplexity.SIMPLE
        assert result.confidence == 0.9
        assert result.estimated_steps == 1

    def test_parse_llm_response_moderate(self):
        """Test parsing response with MODERATE complexity."""
        detector = ComplexityDetector()
        response = """
COMPLEXITY: MODERATE
CONFIDENCE: 0.8
REASONING: Multi-step process
ESTIMATED_STEPS: 3
"""
        result = detector._parse_llm_response(response, "test task")

        assert result.complexity == TaskComplexity.MODERATE
        assert result.confidence == 0.8
        assert result.estimated_steps == 3

    def test_parse_llm_response_complex(self):
        """Test parsing response with COMPLEX complexity."""
        detector = ComplexityDetector()
        response = """
COMPLEXITY: COMPLEX
CONFIDENCE: 0.85
REASONING: Multi-phase orchestration required
ESTIMATED_STEPS: 7
"""
        result = detector._parse_llm_response(response, "test task")

        assert result.complexity == TaskComplexity.COMPLEX
        assert result.confidence == 0.85
        assert result.estimated_steps == 7

    def test_parse_llm_response_missing_confidence(self):
        """Test parsing response with missing confidence."""
        detector = ComplexityDetector()
        response = "COMPLEXITY: SIMPLE\nESTIMATED_STEPS: 1"
        result = detector._parse_llm_response(response, "test")

        # Should use default confidence
        assert result.confidence == 0.7

    def test_parse_llm_response_missing_steps(self):
        """Test parsing response with missing steps."""
        detector = ComplexityDetector()
        response = "COMPLEXITY: MODERATE\nCONFIDENCE: 0.8"
        result = detector._parse_llm_response(response, "test")

        # Should use default steps
        assert result.estimated_steps == 3

    def test_parse_llm_response_ambiguous(self):
        """Test parsing ambiguous response."""
        detector = ComplexityDetector()
        response = "This task is somewhat complex but manageable"
        result = detector._parse_llm_response(response, "test")

        # "complex" keyword should trigger COMPLEX
        assert result.complexity == TaskComplexity.COMPLEX

    def test_parse_llm_response_no_complexity_keywords(self):
        """Test parsing response with no clear complexity."""
        detector = ComplexityDetector()
        response = "The task requires multiple steps"
        result = detector._parse_llm_response(response, "test")

        # Should default to MODERATE
        assert result.complexity == TaskComplexity.MODERATE

    def test_parse_llm_response_case_insensitive(self):
        """Test that parsing is case insensitive."""
        detector = ComplexityDetector()

        # Test lowercase
        response1 = "complexity: simple\nconfidence: 0.9\nestimated_steps: 1"
        result1 = detector._parse_llm_response(response1, "test")
        assert result1.complexity == TaskComplexity.SIMPLE

        # Test mixed case
        response2 = "CoMpLeXiTy: ComPLex\nConFiDence: 0.8\nEstimated_Steps: 5"
        result2 = detector._parse_llm_response(response2, "test")
        assert result2.complexity == TaskComplexity.COMPLEX

    def test_parse_llm_response_reasoning_included(self):
        """Test that reasoning is extracted from response."""
        detector = ComplexityDetector()
        response = "COMPLEXITY: SIMPLE\nREASONING: This is a simple task\nCONFIDENCE: 0.9"
        result = detector._parse_llm_response(response, "test")

        assert "LLM analysis" in result.reasoning
        assert len(result.reasoning) > 0

    def test_parse_llm_response_long_response_truncated(self):
        """Test that long responses are truncated in reasoning."""
        detector = ComplexityDetector()
        long_response = "COMPLEXITY: SIMPLE\n" + ("x" * 300)
        result = detector._parse_llm_response(long_response, "test")

        # Should truncate to 200 chars in reasoning
        assert len(result.reasoning) < 250  # "LLM analysis: " + 200 chars

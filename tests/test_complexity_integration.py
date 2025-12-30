"""Integration tests for ComplexityDetector with ConversationManager."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from hrisa_code.core.conversation import ConversationManager, OllamaConfig
from hrisa_code.core.planning import TaskComplexity


class TestComplexityDetectorIntegration:
    """Tests for ComplexityDetector integration in ConversationManager."""

    def test_complexity_detector_initialized(self, tmp_path):
        """Test that ComplexityDetector is initialized in ConversationManager."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )
        assert manager.complexity_detector is not None
        assert manager.complexity_detector.ollama_client is not None

    @pytest.mark.asyncio
    async def test_simple_task_complexity_display(self, tmp_path):
        """Test that simple task complexity is displayed."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Mock the ollama client to avoid actual API calls
        mock_response = {
            "message": {
                "role": "assistant",
                "content": "Here are the files: file1.py, file2.py"
            },
            "done": True
        }
        manager.ollama_client.chat_raw = AsyncMock(return_value=mock_response)

        # Capture console output
        with patch.object(manager.console, 'print') as mock_print:
            await manager.process_message("list all Python files")

            # Check that complexity was displayed
            calls = [str(call) for call in mock_print.call_args_list]
            complexity_displayed = any("Task Complexity" in str(call) for call in calls)
            assert complexity_displayed, "Complexity should be displayed to user"

    @pytest.mark.asyncio
    async def test_moderate_task_complexity_display(self, tmp_path):
        """Test that moderate task complexity is displayed."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Mock the ollama client
        mock_response = {
            "message": {
                "role": "assistant",
                "content": "I'll add logging to the API endpoints."
            },
            "done": True
        }
        manager.ollama_client.chat_raw = AsyncMock(return_value=mock_response)

        # Capture console output
        with patch.object(manager.console, 'print') as mock_print:
            await manager.process_message("add logging to API endpoints")

            # Check that complexity was displayed
            calls = [str(call) for call in mock_print.call_args_list]
            complexity_displayed = any("Task Complexity" in str(call) for call in calls)
            assert complexity_displayed

    @pytest.mark.asyncio
    async def test_complex_task_complexity_display(self, tmp_path):
        """Test that complex task complexity is displayed."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Mock the ollama client
        mock_response = {
            "message": {
                "role": "assistant",
                "content": "I'll implement the authentication system."
            },
            "done": True
        }
        manager.ollama_client.chat_raw = AsyncMock(return_value=mock_response)

        # Capture console output
        with patch.object(manager.console, 'print') as mock_print:
            await manager.process_message("implement authentication system")

            # Check that complexity was displayed
            calls = [str(call) for call in mock_print.call_args_list]
            complexity_displayed = any("Task Complexity" in str(call) for call in calls)
            assert complexity_displayed

    def test_display_complexity_analysis_simple(self, tmp_path):
        """Test display method for simple task."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Create mock analysis
        from hrisa_code.core.planning import ComplexityAnalysis
        analysis = ComplexityAnalysis(
            complexity=TaskComplexity.SIMPLE,
            confidence=0.9,
            reasoning="Simple task",
            indicators=[],
            suggested_approach="Direct execution",
            estimated_steps=1
        )

        # Capture console output
        with patch.object(manager.console, 'print') as mock_print:
            manager._display_complexity_analysis(analysis)

            # Verify it was called
            mock_print.assert_called_once()
            call_args = str(mock_print.call_args)
            assert "SIMPLE" in call_args
            assert "1 step" in call_args

    def test_display_complexity_analysis_moderate(self, tmp_path):
        """Test display method for moderate task."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        from hrisa_code.core.planning import ComplexityAnalysis
        analysis = ComplexityAnalysis(
            complexity=TaskComplexity.MODERATE,
            confidence=0.8,
            reasoning="Moderate task",
            indicators=[],
            suggested_approach="Multi-step",
            estimated_steps=3
        )

        with patch.object(manager.console, 'print') as mock_print:
            manager._display_complexity_analysis(analysis)

            mock_print.assert_called_once()
            call_args = str(mock_print.call_args)
            assert "MODERATE" in call_args
            assert "3 steps" in call_args

    def test_display_complexity_analysis_complex(self, tmp_path):
        """Test display method for complex task."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        from hrisa_code.core.planning import ComplexityAnalysis
        analysis = ComplexityAnalysis(
            complexity=TaskComplexity.COMPLEX,
            confidence=0.85,
            reasoning="Complex task",
            indicators=[],
            suggested_approach="Orchestration",
            estimated_steps=7
        )

        with patch.object(manager.console, 'print') as mock_print:
            manager._display_complexity_analysis(analysis)

            mock_print.assert_called_once()
            call_args = str(mock_print.call_args)
            assert "COMPLEX" in call_args
            assert "7 steps" in call_args

    def test_complexity_analysis_uses_correct_detector(self, tmp_path):
        """Test that complexity analysis uses the detector instance."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Mock the detector's analyze method
        with patch.object(manager.complexity_detector, 'analyze') as mock_analyze:
            from hrisa_code.core.planning import ComplexityAnalysis
            mock_analyze.return_value = ComplexityAnalysis(
                complexity=TaskComplexity.SIMPLE,
                confidence=0.9,
                reasoning="Test",
                indicators=[],
                suggested_approach="Direct",
                estimated_steps=1
            )

            # Trigger analysis
            analysis = manager.complexity_detector.analyze("test task")

            # Verify analyze was called
            mock_analyze.assert_called_once_with("test task")
            assert analysis.complexity == TaskComplexity.SIMPLE


class TestComplexityDetectorEdgeCases:
    """Tests for edge cases in complexity detection integration."""

    def test_tools_disabled_still_has_detector(self, tmp_path):
        """Test that ComplexityDetector is still initialized when tools disabled."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            enable_tools=False
        )
        # ComplexityDetector should still be initialized
        assert manager.complexity_detector is not None

    @pytest.mark.asyncio
    async def test_empty_message_complexity(self, tmp_path):
        """Test complexity analysis with empty message."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Mock the ollama client
        mock_response = {
            "message": {
                "role": "assistant",
                "content": "I need more information."
            },
            "done": True
        }
        manager.ollama_client.chat_raw = AsyncMock(return_value=mock_response)

        # Should not crash with empty message
        with patch.object(manager.console, 'print'):
            await manager.process_message("")

    def test_detector_uses_correct_model(self, tmp_path):
        """Test that detector uses the correct evaluation model."""
        config = OllamaConfig(model="custom-model:latest")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Detector should use the same model as conversation
        assert manager.complexity_detector.evaluation_model == "custom-model:latest"

"""Model router for selecting the best model for specific tasks.

This module provides intelligent model selection based on task requirements,
available models, and user preferences.
"""

from typing import Optional, List, Set
from dataclasses import dataclass
from enum import Enum
import asyncio

from hrisa_code.core.model_catalog import (
    ModelCatalog,
    ModelProfile,
    ModelCapability,
    QualityTier,
    SpeedTier,
)


class TaskType(str, Enum):
    """Types of tasks that need model selection."""

    # Orchestration step types
    ARCHITECTURE_DISCOVERY = "architecture_discovery"
    COMPONENT_ANALYSIS = "component_analysis"
    FEATURE_IDENTIFICATION = "feature_identification"
    WORKFLOW_UNDERSTANDING = "workflow_understanding"
    DOCUMENTATION_SYNTHESIS = "documentation_synthesis"

    # Sub-task types
    FILE_LISTING = "file_listing"
    FILE_READING = "file_reading"
    SEARCH_PATTERN_GENERATION = "search_pattern_generation"
    CODE_ANALYSIS = "code_analysis"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    WORKFLOW_TRACING = "workflow_tracing"
    TEXT_SYNTHESIS = "text_synthesis"
    TECHNICAL_WRITING = "technical_writing"


@dataclass
class ModelSelectionStrategy:
    """Strategy for model selection."""

    prefer_speed: bool = False
    """Prefer faster models over quality"""

    prefer_quality: bool = True
    """Prefer quality over speed (default)"""

    allow_fallback: bool = True
    """Allow fallback to available models if preferred model not found"""

    available_models: Optional[Set[str]] = None
    """Set of actually available model names (pulled in Ollama)"""

    default_model: str = "qwen2.5-coder:32b"
    """Default fallback model if no suitable model found"""


class ModelRouter:
    """Routes tasks to the most appropriate model."""

    def __init__(
        self,
        catalog: Optional[ModelCatalog] = None,
        strategy: Optional[ModelSelectionStrategy] = None,
        available_models: Optional[List[str]] = None,
    ):
        """Initialize the model router.

        Args:
            catalog: Model catalog (creates default if None)
            strategy: Model selection strategy (uses default if None)
            available_models: List of actually available models in Ollama
        """
        self.catalog = catalog or ModelCatalog()
        self.strategy = strategy or ModelSelectionStrategy()

        # Update available models if provided
        if available_models:
            self.strategy.available_models = set(available_models)

    def _capability_for_task(self, task_type: TaskType) -> ModelCapability:
        """Map task type to required model capability.

        Args:
            task_type: Type of task to perform

        Returns:
            Required model capability
        """
        mapping = {
            # Orchestration steps
            TaskType.ARCHITECTURE_DISCOVERY: ModelCapability.ARCHITECTURE_ANALYSIS,
            TaskType.COMPONENT_ANALYSIS: ModelCapability.CODE_ANALYSIS,
            TaskType.FEATURE_IDENTIFICATION: ModelCapability.PATTERN_GENERATION,
            TaskType.WORKFLOW_UNDERSTANDING: ModelCapability.WORKFLOW_TRACING,
            TaskType.DOCUMENTATION_SYNTHESIS: ModelCapability.DOCUMENTATION_WRITING,

            # Sub-tasks
            TaskType.FILE_LISTING: ModelCapability.FILE_OPERATIONS,
            TaskType.FILE_READING: ModelCapability.FILE_OPERATIONS,
            TaskType.SEARCH_PATTERN_GENERATION: ModelCapability.PATTERN_GENERATION,
            TaskType.CODE_ANALYSIS: ModelCapability.CODE_ANALYSIS,
            TaskType.ARCHITECTURE_ANALYSIS: ModelCapability.ARCHITECTURE_ANALYSIS,
            TaskType.WORKFLOW_TRACING: ModelCapability.WORKFLOW_TRACING,
            TaskType.TEXT_SYNTHESIS: ModelCapability.TEXT_SYNTHESIS,
            TaskType.TECHNICAL_WRITING: ModelCapability.TECHNICAL_WRITING,
        }

        return mapping.get(task_type, ModelCapability.CODE_ANALYSIS)

    def select_model_for_task(self, task_type: TaskType) -> str:
        """Select the best model for a specific task type.

        Args:
            task_type: Type of task to perform

        Returns:
            Model name to use
        """
        # Get required capability
        capability = self._capability_for_task(task_type)

        # Get best model for capability
        best_model = self.catalog.get_best_model_for_capability(
            capability,
            prefer_speed=self.strategy.prefer_speed
        )

        if not best_model:
            return self.strategy.default_model

        # Check if model is actually available
        if self.strategy.available_models is not None:
            if best_model.name in self.strategy.available_models:
                return best_model.name
            elif self.strategy.allow_fallback:
                # Find best available model with this capability
                candidates = self.catalog.get_models_by_capability(capability)
                available_candidates = [
                    m for m in candidates
                    if m.name in self.strategy.available_models
                ]

                if available_candidates:
                    # Return best available model
                    if self.strategy.prefer_speed:
                        quality_order = {QualityTier.EXCELLENT: 3, QualityTier.GOOD: 2, QualityTier.BASIC: 1}
                        speed_order = {SpeedTier.FAST: 3, SpeedTier.MEDIUM: 2, SpeedTier.SLOW: 1}
                        best_available = max(
                            available_candidates,
                            key=lambda m: (speed_order[m.speed_tier], quality_order[m.quality_tier])
                        )
                    else:
                        quality_order = {QualityTier.EXCELLENT: 3, QualityTier.GOOD: 2, QualityTier.BASIC: 1}
                        speed_order = {SpeedTier.FAST: 3, SpeedTier.MEDIUM: 2, SpeedTier.SLOW: 1}
                        best_available = max(
                            available_candidates,
                            key=lambda m: (quality_order[m.quality_tier], speed_order[m.speed_tier])
                        )
                    return best_available.name
                else:
                    # No available models with capability, use default if available
                    if self.strategy.default_model in self.strategy.available_models:
                        return self.strategy.default_model
                    # Return any available model
                    return list(self.strategy.available_models)[0]
            else:
                # Fallback not allowed, return preferred even if not available
                return best_model.name

        # No availability checking, return best model
        return best_model.name

    def select_model_for_orchestration_step(
        self,
        step_name: str,
        substep: Optional[str] = None
    ) -> str:
        """Select model for a specific orchestration step.

        Args:
            step_name: Name of the orchestration step (architecture, components, etc.)
            substep: Optional substep within the main step

        Returns:
            Model name to use
        """
        # Map step names to task types
        step_mapping = {
            "architecture": TaskType.ARCHITECTURE_DISCOVERY,
            "components": TaskType.COMPONENT_ANALYSIS,
            "features": TaskType.FEATURE_IDENTIFICATION,
            "workflows": TaskType.WORKFLOW_UNDERSTANDING,
            "synthesis": TaskType.DOCUMENTATION_SYNTHESIS,
        }

        task_type = step_mapping.get(step_name, TaskType.CODE_ANALYSIS)
        return self.select_model_for_task(task_type)

    def get_model_info(self, model_name: str) -> Optional[ModelProfile]:
        """Get information about a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Model profile if found, None otherwise
        """
        return self.catalog.get_profile(model_name)

    async def update_available_models(self, ollama_client) -> None:
        """Update the list of available models from Ollama.

        Args:
            ollama_client: OllamaClient instance to query available models
        """
        try:
            available = await ollama_client.list_models()
            self.strategy.available_models = set(available)
        except Exception as e:
            # If we can't get models, keep existing set or use None
            pass

    def get_model_comparison(self, model_names: List[str]) -> str:
        """Get a comparison of multiple models.

        Args:
            model_names: List of model names to compare

        Returns:
            Human-readable comparison text
        """
        lines = ["Model Comparison:\n"]

        for name in model_names:
            profile = self.catalog.get_profile(name)
            if profile:
                lines.append(f"\n{profile.name}:")
                lines.append(f"  Quality: {profile.quality_tier.value}")
                lines.append(f"  Speed: {profile.speed_tier.value}")
                lines.append(f"  Strengths: {profile.strengths}")
                if profile.weaknesses:
                    lines.append(f"  Weaknesses: {profile.weaknesses}")
                lines.append(f"  Capabilities: {', '.join(c.value for c in profile.capabilities)}")
            else:
                lines.append(f"\n{name}: (not in catalog)")

        return "\n".join(lines)

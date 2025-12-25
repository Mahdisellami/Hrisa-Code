"""Model catalog and routing system for multi-model orchestration.

This module provides a catalog of models with their capabilities and a router
to select the best model for specific tasks.
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


class ModelCapability(str, Enum):
    """Capabilities that models can have."""

    # File and search operations
    FILE_OPERATIONS = "file_operations"
    SIMPLE_SEARCH = "simple_search"
    PATTERN_GENERATION = "pattern_generation"

    # Code understanding
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"

    # Reasoning and analysis
    REASONING = "reasoning"
    COMPLEX_REASONING = "complex_reasoning"
    WORKFLOW_TRACING = "workflow_tracing"

    # Text generation
    TEXT_SYNTHESIS = "text_synthesis"
    DOCUMENTATION_WRITING = "documentation_writing"
    TECHNICAL_WRITING = "technical_writing"


class SpeedTier(str, Enum):
    """Speed tiers for models."""
    FAST = "fast"  # < 10 tokens/sec
    MEDIUM = "medium"  # 10-30 tokens/sec
    SLOW = "slow"  # > 30 tokens/sec


class QualityTier(str, Enum):
    """Quality tiers for models."""
    BASIC = "basic"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class ModelProfile:
    """Profile for a model with its capabilities and characteristics."""

    name: str
    """Model name as used in Ollama (e.g., 'qwen2.5-coder:32b')"""

    capabilities: List[ModelCapability]
    """List of capabilities this model excels at"""

    quality_tier: QualityTier
    """Overall quality tier of the model"""

    speed_tier: SpeedTier
    """Speed tier of the model"""

    strengths: str
    """Human-readable description of model strengths"""

    weaknesses: Optional[str] = None
    """Human-readable description of model weaknesses"""

    parameter_count: Optional[str] = None
    """Parameter count (e.g., '32B', '72B', '236B')"""

    recommended_for: List[str] = field(default_factory=list)
    """List of specific use cases this model is recommended for"""


class ModelCatalog:
    """Catalog of available models and their profiles."""

    def __init__(self):
        """Initialize the model catalog with predefined profiles."""
        self.profiles: Dict[str, ModelProfile] = {}
        self._initialize_default_profiles()

    def _initialize_default_profiles(self) -> None:
        """Initialize catalog with default model profiles."""

        # Small, fast models for simple operations
        self.add_profile(ModelProfile(
            name="qwen2.5-coder:7b",
            capabilities=[
                ModelCapability.FILE_OPERATIONS,
                ModelCapability.SIMPLE_SEARCH,
                ModelCapability.CODE_GENERATION,
            ],
            quality_tier=QualityTier.BASIC,
            speed_tier=SpeedTier.FAST,
            strengths="Fast execution, good for simple file operations and basic code tasks",
            weaknesses="Limited reasoning, may struggle with complex analysis",
            parameter_count="7B",
            recommended_for=["file_listing", "directory_structure", "simple_searches"]
        ))

        # Medium-sized coding models
        self.add_profile(ModelProfile(
            name="qwen2.5-coder:32b",
            capabilities=[
                ModelCapability.FILE_OPERATIONS,
                ModelCapability.SIMPLE_SEARCH,
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.CODE_GENERATION,
                ModelCapability.PATTERN_GENERATION,
            ],
            quality_tier=QualityTier.GOOD,
            speed_tier=SpeedTier.MEDIUM,
            strengths="Balanced coding capabilities, good instruction following",
            weaknesses="May generate incorrect search patterns, occasional hallucinations",
            parameter_count="32B",
            recommended_for=["general_coding", "file_operations", "basic_analysis"]
        ))

        self.add_profile(ModelProfile(
            name="codestral:22b",
            capabilities=[
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.CODE_GENERATION,
                ModelCapability.PATTERN_GENERATION,
            ],
            quality_tier=QualityTier.GOOD,
            speed_tier=SpeedTier.MEDIUM,
            strengths="Mistral's coding specialist, good code understanding",
            parameter_count="22B",
            recommended_for=["code_analysis", "pattern_generation"]
        ))

        # Large general-purpose models
        self.add_profile(ModelProfile(
            name="qwen2.5:72b",
            capabilities=[
                ModelCapability.PATTERN_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.ARCHITECTURE_ANALYSIS,
                ModelCapability.TEXT_SYNTHESIS,
                ModelCapability.TECHNICAL_WRITING,
            ],
            quality_tier=QualityTier.EXCELLENT,
            speed_tier=SpeedTier.SLOW,
            strengths="Strong reasoning, excellent instruction following, good pattern generation",
            parameter_count="72B",
            recommended_for=["pattern_generation", "architecture_analysis", "complex_reasoning"]
        ))

        self.add_profile(ModelProfile(
            name="llama3.1:70b",
            capabilities=[
                ModelCapability.REASONING,
                ModelCapability.TEXT_SYNTHESIS,
                ModelCapability.DOCUMENTATION_WRITING,
                ModelCapability.TECHNICAL_WRITING,
                ModelCapability.CODE_ANALYSIS,
            ],
            quality_tier=QualityTier.EXCELLENT,
            speed_tier=SpeedTier.SLOW,
            strengths="Excellent prose generation, coherent long-form writing, strong reasoning",
            parameter_count="70B",
            recommended_for=["documentation_synthesis", "technical_writing", "comprehensive_docs"]
        ))

        self.add_profile(ModelProfile(
            name="llama3.1:405b",
            capabilities=[
                ModelCapability.REASONING,
                ModelCapability.COMPLEX_REASONING,
                ModelCapability.TEXT_SYNTHESIS,
                ModelCapability.DOCUMENTATION_WRITING,
                ModelCapability.TECHNICAL_WRITING,
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.ARCHITECTURE_ANALYSIS,
            ],
            quality_tier=QualityTier.EXCELLENT,
            speed_tier=SpeedTier.SLOW,
            strengths="Extremely capable, best-in-class for complex tasks",
            weaknesses="Very slow, requires massive VRAM",
            parameter_count="405B",
            recommended_for=["complex_reasoning", "comprehensive_analysis", "high_quality_synthesis"]
        ))

        # Specialized large coding models
        self.add_profile(ModelProfile(
            name="deepseek-coder-v2:236b",
            capabilities=[
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.CODE_GENERATION,
                ModelCapability.ARCHITECTURE_ANALYSIS,
                ModelCapability.WORKFLOW_TRACING,
                ModelCapability.PATTERN_GENERATION,
            ],
            quality_tier=QualityTier.EXCELLENT,
            speed_tier=SpeedTier.SLOW,
            strengths="Best-in-class code understanding, excellent at tracing complex logic",
            parameter_count="236B",
            recommended_for=["deep_code_analysis", "architecture_analysis", "workflow_tracing"]
        ))

        # Reasoning models
        self.add_profile(ModelProfile(
            name="deepseek-r1:70b",
            capabilities=[
                ModelCapability.REASONING,
                ModelCapability.COMPLEX_REASONING,
                ModelCapability.WORKFLOW_TRACING,
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.ARCHITECTURE_ANALYSIS,
            ],
            quality_tier=QualityTier.EXCELLENT,
            speed_tier=SpeedTier.SLOW,
            strengths="Built-in chain-of-thought reasoning, excellent for complex multi-step tasks",
            parameter_count="70B",
            recommended_for=["workflow_tracing", "complex_reasoning", "step_by_step_analysis"]
        ))

        self.add_profile(ModelProfile(
            name="deepseek-r1:671b",
            capabilities=[
                ModelCapability.REASONING,
                ModelCapability.COMPLEX_REASONING,
                ModelCapability.WORKFLOW_TRACING,
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.ARCHITECTURE_ANALYSIS,
            ],
            quality_tier=QualityTier.EXCELLENT,
            speed_tier=SpeedTier.SLOW,
            strengths="Massive reasoning model, best-in-class for extremely complex tasks",
            weaknesses="Very slow, requires enormous VRAM",
            parameter_count="671B",
            recommended_for=["extreme_complexity", "research_level_analysis"]
        ))

    def add_profile(self, profile: ModelProfile) -> None:
        """Add a model profile to the catalog.

        Args:
            profile: The model profile to add
        """
        self.profiles[profile.name] = profile

    def get_profile(self, model_name: str) -> Optional[ModelProfile]:
        """Get profile for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Model profile if found, None otherwise
        """
        return self.profiles.get(model_name)

    def get_models_by_capability(
        self,
        capability: ModelCapability,
        quality_tier: Optional[QualityTier] = None
    ) -> List[ModelProfile]:
        """Get all models that have a specific capability.

        Args:
            capability: The capability to filter by
            quality_tier: Optional quality tier filter

        Returns:
            List of model profiles matching the criteria
        """
        models = [
            profile for profile in self.profiles.values()
            if capability in profile.capabilities
        ]

        if quality_tier:
            models = [m for m in models if m.quality_tier == quality_tier]

        return models

    def get_best_model_for_capability(
        self,
        capability: ModelCapability,
        prefer_speed: bool = False
    ) -> Optional[ModelProfile]:
        """Get the best model for a specific capability.

        Args:
            capability: The capability needed
            prefer_speed: If True, prefer faster models over quality

        Returns:
            Best model profile for the capability, or None if no match
        """
        models = self.get_models_by_capability(capability)

        if not models:
            return None

        if prefer_speed:
            # Prefer fast models, then by quality
            quality_order = {QualityTier.EXCELLENT: 3, QualityTier.GOOD: 2, QualityTier.BASIC: 1}
            speed_order = {SpeedTier.FAST: 3, SpeedTier.MEDIUM: 2, SpeedTier.SLOW: 1}
            return max(models, key=lambda m: (speed_order[m.speed_tier], quality_order[m.quality_tier]))
        else:
            # Prefer quality, then by speed
            quality_order = {QualityTier.EXCELLENT: 3, QualityTier.GOOD: 2, QualityTier.BASIC: 1}
            speed_order = {SpeedTier.FAST: 3, SpeedTier.MEDIUM: 2, SpeedTier.SLOW: 1}
            return max(models, key=lambda m: (quality_order[m.quality_tier], speed_order[m.speed_tier]))

    def list_all_models(self) -> List[str]:
        """Get list of all model names in catalog.

        Returns:
            List of model names
        """
        return list(self.profiles.keys())

    def get_models_by_use_case(self, use_case: str) -> List[ModelProfile]:
        """Get models recommended for a specific use case.

        Args:
            use_case: The use case to search for

        Returns:
            List of model profiles recommended for the use case
        """
        return [
            profile for profile in self.profiles.values()
            if use_case in profile.recommended_for
        ]

"""Complexity detection system for determining orchestration needs.

This module analyzes user tasks to determine if they require orchestration:
- Simple: Single-turn execution (direct tool call)
- Moderate: Multi-step sequential execution
- Complex: Multi-phase with exploration and planning

This enables intelligent routing and resource allocation.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"              # Single tool call, no orchestration
    MODERATE = "moderate"          # Multi-step sequential execution
    COMPLEX = "complex"            # Multi-phase with exploration


@dataclass
class ComplexityAnalysis:
    """Result of complexity analysis.

    Attributes:
        complexity: Detected complexity level
        confidence: Confidence score (0.0-1.0)
        reasoning: Why this complexity was assigned
        indicators: List of complexity indicators found
        suggested_approach: How to handle this task
        estimated_steps: Rough estimate of steps needed
    """
    complexity: TaskComplexity
    confidence: float
    reasoning: str
    indicators: List[str]
    suggested_approach: str
    estimated_steps: int


class ComplexityDetector:
    """Analyzes tasks to determine if orchestration is needed.

    Uses heuristics and pattern matching to classify task complexity:
    - Simple: "list files", "read config.py", "show git status"
    - Moderate: "add logging", "fix bug in auth", "update dependencies"
    - Complex: "implement auth system", "refactor codebase", "add feature X"

    The detector helps route tasks to appropriate execution strategies:
    - Simple → Direct tool execution
    - Moderate → Sequential multi-step execution
    - Complex → Full orchestration with planning
    """

    def __init__(self, ollama_client=None, evaluation_model: str = "qwen2.5-coder:7b"):
        """Initialize complexity detector.

        Args:
            ollama_client: Optional OllamaClient for LLM-based analysis
            evaluation_model: Model to use for complexity evaluation
        """
        self.ollama_client = ollama_client
        self.evaluation_model = evaluation_model

        # Build detection rules
        self._build_detection_rules()

    def _build_detection_rules(self) -> None:
        """Build heuristic rules for complexity detection."""

        # Simple task patterns (single tool call)
        self.simple_patterns = [
            # Read operations
            "list", "show", "display", "view", "read", "see", "check",
            "what is", "what's", "tell me", "print",
            # Status checks
            "git status", "git diff", "git log",
            # Single file operations
            "read file", "show file", "cat",
        ]

        # Moderate task patterns (multi-step sequential)
        self.moderate_patterns = [
            # Modifications to existing code
            "add", "update", "modify", "change", "fix", "improve",
            "remove", "delete", "rename",
            # Specific scoped tasks
            "add logging to", "fix bug in", "update config",
            "add error handling", "add validation",
            # Testing and verification
            "test", "verify", "validate",
        ]

        # Complex task patterns (multi-phase orchestration)
        self.complex_patterns = [
            # New features/systems
            "implement", "create system", "build", "develop",
            "design and implement", "add feature",
            # Large-scale changes
            "refactor", "restructure", "reorganize",
            "migrate", "upgrade", "convert",
            # Comprehensive tasks
            "comprehensive", "complete", "full", "entire",
            # Research + implementation
            "implement authentication", "add security",
            "create api", "build pipeline",
        ]

        # Complexity indicators
        self.complexity_indicators = {
            "multi_file": ["multiple files", "all files", "entire codebase", "across"],
            "exploration": ["find", "search for", "discover", "explore", "analyze"],
            "design": ["design", "architecture", "pattern", "approach", "strategy"],
            "testing": ["write tests", "test coverage", "integration tests"],
            "dependencies": ["and", "then", "after", "before", "with"],
            "uncertainty": ["how to", "best way", "should i", "which", "what approach"],
        }

    def analyze(self, task: str, context: Optional[str] = None) -> ComplexityAnalysis:
        """Analyze task complexity using heuristics.

        Args:
            task: User's task description
            context: Optional context (conversation history, codebase info)

        Returns:
            ComplexityAnalysis with detected complexity and reasoning
        """
        task_lower = task.lower()
        indicators = []

        # Check for simple patterns (highest priority - most specific)
        simple_score = self._check_patterns(task_lower, self.simple_patterns)
        if simple_score > 0:
            indicators.append(f"Simple operation pattern (score: {simple_score})")

        # Check for complex patterns (check before moderate to prioritize)
        complex_score = self._check_patterns(task_lower, self.complex_patterns)
        if complex_score > 0:
            indicators.append(f"Complex task pattern (score: {complex_score})")

        # Check for moderate patterns
        moderate_score = self._check_patterns(task_lower, self.moderate_patterns)
        if moderate_score > 0:
            indicators.append(f"Moderate task pattern (score: {moderate_score})")

        # Check complexity indicators
        indicator_scores = self._check_complexity_indicators(task_lower)
        indicators.extend([f"{k}: {v}" for k, v in indicator_scores.items() if v > 0])

        # Calculate total complexity signals
        total_indicators = sum(indicator_scores.values())

        # Determine complexity level
        complexity, confidence, reasoning, estimated_steps = self._classify_complexity(
            simple_score=simple_score,
            moderate_score=moderate_score,
            complex_score=complex_score,
            indicator_count=total_indicators,
            task_length=len(task.split()),
        )

        # Determine suggested approach
        suggested_approach = self._suggest_approach(complexity)

        return ComplexityAnalysis(
            complexity=complexity,
            confidence=confidence,
            reasoning=reasoning,
            indicators=indicators,
            suggested_approach=suggested_approach,
            estimated_steps=estimated_steps,
        )

    def _check_patterns(self, task: str, patterns: List[str]) -> int:
        """Check how many patterns match the task.

        Args:
            task: Task text (lowercase)
            patterns: List of patterns to check

        Returns:
            Number of matching patterns
        """
        matches = 0
        for pattern in patterns:
            if pattern in task:
                matches += 1
        return matches

    def _check_complexity_indicators(self, task: str) -> Dict[str, int]:
        """Check for complexity indicators in task.

        Args:
            task: Task text (lowercase)

        Returns:
            Dictionary of indicator types and their scores
        """
        scores = {}
        for indicator_type, patterns in self.complexity_indicators.items():
            score = self._check_patterns(task, patterns)
            if score > 0:
                scores[indicator_type] = score
        return scores

    def _classify_complexity(
        self,
        simple_score: int,
        moderate_score: int,
        complex_score: int,
        indicator_count: int,
        task_length: int,
    ) -> tuple[TaskComplexity, float, str, int]:
        """Classify task complexity based on scores.

        Args:
            simple_score: Simple pattern matches
            moderate_score: Moderate pattern matches
            complex_score: Complex pattern matches
            indicator_count: Total complexity indicators
            task_length: Number of words in task

        Returns:
            Tuple of (complexity, confidence, reasoning, estimated_steps)
        """
        # Simple tasks: Clear simple patterns, no complexity indicators
        # Exception: If has moderate patterns, prefer moderate over simple
        if simple_score > 0 and complex_score == 0 and indicator_count <= 1 and moderate_score == 0:
            confidence = 0.9 if simple_score > 1 else 0.8
            reasoning = f"Task matches {simple_score} simple pattern(s), requires single tool call"
            return TaskComplexity.SIMPLE, confidence, reasoning, 1

        # Complex tasks: Strong complex signals or many indicators
        if complex_score > 0 or indicator_count >= 3:
            confidence = 0.85 if complex_score > 1 else 0.75
            reasoning = (
                f"Task matches {complex_score} complex pattern(s), "
                f"has {indicator_count} complexity indicator(s), "
                "requires multi-phase orchestration"
            )
            estimated_steps = 5 + indicator_count  # Rough estimate
            return TaskComplexity.COMPLEX, confidence, reasoning, estimated_steps

        # Moderate tasks: Moderate patterns or some complexity
        if moderate_score > 0 or indicator_count > 0:
            confidence = 0.8 if moderate_score > 1 else 0.7
            reasoning = (
                f"Task matches {moderate_score} moderate pattern(s), "
                f"has {indicator_count} complexity indicator(s), "
                "requires multi-step execution"
            )
            estimated_steps = 2 + indicator_count
            return TaskComplexity.MODERATE, confidence, reasoning, estimated_steps

        # Default: Short tasks are simple, long tasks are moderate
        if task_length <= 5:
            confidence = 0.6
            reasoning = "Short task with no clear complexity signals, likely simple"
            return TaskComplexity.SIMPLE, confidence, reasoning, 1
        else:
            confidence = 0.6
            reasoning = "Task has unclear complexity, defaulting to moderate approach"
            return TaskComplexity.MODERATE, confidence, reasoning, 3

    def _suggest_approach(self, complexity: TaskComplexity) -> str:
        """Suggest execution approach based on complexity.

        Args:
            complexity: Detected complexity level

        Returns:
            Suggested execution approach
        """
        approaches = {
            TaskComplexity.SIMPLE: (
                "Direct tool execution - task can be completed with single tool call"
            ),
            TaskComplexity.MODERATE: (
                "Sequential multi-step execution - explore, plan, implement in sequence"
            ),
            TaskComplexity.COMPLEX: (
                "Full orchestration - multi-phase execution with planning, exploration, "
                "implementation, and verification"
            ),
        }
        return approaches[complexity]

    async def analyze_with_llm(
        self,
        task: str,
        context: Optional[str] = None,
    ) -> ComplexityAnalysis:
        """Analyze task complexity using LLM (more accurate but slower).

        Args:
            task: User's task description
            context: Optional context

        Returns:
            ComplexityAnalysis with LLM-based assessment
        """
        if not self.ollama_client:
            # Fall back to heuristic analysis
            return self.analyze(task, context)

        # Build prompt for LLM
        prompt = self._build_llm_prompt(task, context)

        try:
            # Get LLM evaluation
            original_model = self.ollama_client.get_current_model()
            self.ollama_client.switch_model(self.evaluation_model, verbose=False)

            response = await self.ollama_client.chat_simple(
                message=prompt,
                system_prompt=(
                    "You are a task complexity analyzer. Classify tasks as simple, "
                    "moderate, or complex. Be concise and specific."
                ),
            )

            # Restore original model
            self.ollama_client.switch_model(original_model, verbose=False)

            # Parse response
            return self._parse_llm_response(response, task)

        except Exception:
            # Fall back to heuristic analysis on error
            return self.analyze(task, context)

    def _build_llm_prompt(self, task: str, context: Optional[str]) -> str:
        """Build prompt for LLM complexity analysis.

        Args:
            task: User's task
            context: Optional context

        Returns:
            Formatted prompt
        """
        prompt = f"""TASK COMPLEXITY ANALYSIS

User's Task: {task}

Context: {context if context else "None"}

COMPLEXITY LEVELS:
1. SIMPLE - Single tool call (e.g., "list files", "show status")
2. MODERATE - Multi-step sequential (e.g., "add logging", "fix bug")
3. COMPLEX - Multi-phase orchestration (e.g., "implement auth", "refactor system")

CLASSIFY THIS TASK:

COMPLEXITY: [SIMPLE/MODERATE/COMPLEX]
CONFIDENCE: [0.0-1.0]
REASONING: [Brief explanation]
INDICATORS: [List key indicators]
ESTIMATED_STEPS: [Number]

Be concise and specific."""

        return prompt

    def _parse_llm_response(self, response: str, task: str) -> ComplexityAnalysis:
        """Parse LLM response into ComplexityAnalysis.

        Args:
            response: LLM response text
            task: Original task

        Returns:
            ComplexityAnalysis
        """
        # Simple parsing (can be enhanced)
        response_upper = response.upper()

        # Extract complexity
        if "SIMPLE" in response_upper:
            complexity = TaskComplexity.SIMPLE
        elif "COMPLEX" in response_upper:
            complexity = TaskComplexity.COMPLEX
        else:
            complexity = TaskComplexity.MODERATE

        # Extract confidence (look for decimal number)
        import re
        confidence_match = re.search(r'CONFIDENCE[:\s]+([0-9.]+)', response_upper)
        confidence = float(confidence_match.group(1)) if confidence_match else 0.7

        # Extract steps
        steps_match = re.search(r'ESTIMATED_STEPS[:\s]+(\d+)', response_upper)
        estimated_steps = int(steps_match.group(1)) if steps_match else 3

        # Use response as reasoning
        reasoning = f"LLM analysis: {response[:200]}"

        suggested_approach = self._suggest_approach(complexity)

        return ComplexityAnalysis(
            complexity=complexity,
            confidence=confidence,
            reasoning=reasoning,
            indicators=["LLM-based analysis"],
            suggested_approach=suggested_approach,
            estimated_steps=estimated_steps,
        )

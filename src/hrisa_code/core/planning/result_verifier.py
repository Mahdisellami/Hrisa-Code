"""Result verification system for evaluating tool outputs.

This module provides immediate verification of tool results to determine if:
1. The tool result is relevant to the user's question
2. The result provides useful information
3. Additional tool calls are needed
4. The question can now be answered

This prevents wasted tool calls and helps the LLM stay focused.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class RelevanceScore(Enum):
    """Relevance of a tool result to the user's question."""
    HIGHLY_RELEVANT = "highly_relevant"      # Directly answers the question
    RELEVANT = "relevant"                    # Provides useful information
    SOMEWHAT_RELEVANT = "somewhat_relevant"  # Tangentially related
    NOT_RELEVANT = "not_relevant"            # Unrelated or useless


class InformationGap(Enum):
    """Assessment of remaining information gaps."""
    COMPLETE = "complete"                # All needed information gathered
    MINOR_GAPS = "minor_gaps"            # Small pieces missing
    SIGNIFICANT_GAPS = "significant_gaps"  # Major information still needed
    UNCLEAR = "unclear"                  # Can't assess, need clarification


@dataclass
class VerificationResult:
    """Result of verifying a tool output.

    Attributes:
        relevance: How relevant is this result to the user's question
        information_gap: Assessment of what's still missing
        key_findings: What useful information was found (if any)
        next_suggested_action: What should be done next
        can_answer_now: Can the question be answered with current info
        confidence: Confidence in this assessment (0.0-1.0)
    """
    relevance: RelevanceScore
    information_gap: InformationGap
    key_findings: List[str]
    next_suggested_action: Optional[str]
    can_answer_now: bool
    confidence: float


class ResultVerifier:
    """Verifies tool results against user's question to prevent wasted effort.

    After each tool execution, this verifier:
    1. Evaluates if the result is relevant
    2. Identifies what information was gained
    3. Determines what's still missing
    4. Suggests next steps
    5. Detects if we can answer the question now

    This helps the LLM:
    - Stop when enough information is gathered
    - Avoid irrelevant tool calls
    - Stay focused on the actual question
    - Recognize dead ends quickly
    """

    def __init__(
        self,
        ollama_client=None,
        evaluation_model: str = "qwen2.5-coder:7b",
        enable_verification: bool = True,
    ):
        """Initialize the result verifier.

        Args:
            ollama_client: OllamaClient for LLM evaluation
            evaluation_model: Lightweight model for quick checks
            enable_verification: Whether to enable verification (can disable for testing)
        """
        self.ollama_client = ollama_client
        self.evaluation_model = evaluation_model
        self.enable_verification = enable_verification

        # Track state across tool calls
        self.user_question: Optional[str] = None
        self.verification_history: List[VerificationResult] = []
        self.accumulated_findings: List[str] = []

    def set_user_question(self, question: str) -> None:
        """Set the user's question for this turn.

        Args:
            question: The user's question/request
        """
        self.user_question = question
        self.verification_history = []
        self.accumulated_findings = []

    async def verify_result(
        self,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        tool_result: str,
        had_error: bool = False,
    ) -> VerificationResult:
        """Verify a tool result against the user's question.

        Args:
            tool_name: Name of the tool that was executed
            tool_arguments: Arguments passed to the tool
            tool_result: The result returned by the tool
            had_error: Whether the tool execution had an error

        Returns:
            VerificationResult with assessment and suggestions
        """
        if not self.enable_verification or not self.ollama_client:
            # Fast path for testing or when disabled
            return self._create_default_verification()

        if not self.user_question:
            # No question set, can't verify
            return self._create_default_verification()

        if had_error:
            # Tool had an error, result is not useful
            return VerificationResult(
                relevance=RelevanceScore.NOT_RELEVANT,
                information_gap=InformationGap.UNCLEAR,
                key_findings=[],
                next_suggested_action=f"Fix error in {tool_name} call",
                can_answer_now=False,
                confidence=1.0,
            )

        # Build verification prompt
        verification_prompt = self._build_verification_prompt(
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            tool_result=tool_result,
        )

        try:
            # Use lightweight model for fast verification
            original_model = self.ollama_client.get_current_model()
            self.ollama_client.switch_model(self.evaluation_model, verbose=False)

            # Get evaluation
            response = await self.ollama_client.chat_simple(
                message=verification_prompt,
                system_prompt=(
                    "You are a result verifier. Analyze if a tool result helps answer "
                    "the user's question. Be concise and specific."
                ),
            )

            # Restore original model
            self.ollama_client.switch_model(original_model, verbose=False)

            # Parse the response
            verification = self._parse_verification_response(response)

            # Store in history
            self.verification_history.append(verification)
            self.accumulated_findings.extend(verification.key_findings)

            return verification

        except Exception as e:
            # If verification fails, assume it's relevant and continue
            return self._create_default_verification()

    def _build_verification_prompt(
        self,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        tool_result: str,
    ) -> str:
        """Build the verification prompt for the LLM.

        Args:
            tool_name: Tool that was executed
            tool_arguments: Tool arguments
            tool_result: Tool result

        Returns:
            Verification prompt string
        """
        # Truncate result if too long
        max_result_length = 2000
        display_result = tool_result
        if len(tool_result) > max_result_length:
            display_result = tool_result[:max_result_length] + f"\n... (truncated, {len(tool_result)} total chars)"

        prompt = f"""RESULT VERIFICATION TASK

User's Question: {self.user_question}

Tool Executed: {tool_name}
Arguments: {tool_arguments}

Tool Result:
{display_result}

Previous Findings:
{chr(10).join(f"- {finding}" for finding in self.accumulated_findings) if self.accumulated_findings else "None yet"}

EVALUATE THIS RESULT:

1. RELEVANCE: How relevant is this result to answering the user's question?
   - HIGHLY_RELEVANT: Directly answers the question
   - RELEVANT: Provides useful information toward the answer
   - SOMEWHAT_RELEVANT: Tangentially related
   - NOT_RELEVANT: Unrelated or useless

2. KEY_FINDINGS: What useful information did we learn? (bullet points)

3. INFORMATION_GAP: What's still missing to answer the question?
   - COMPLETE: We have everything needed
   - MINOR_GAPS: Small details missing
   - SIGNIFICANT_GAPS: Major information still needed
   - UNCLEAR: Can't assess

4. NEXT_ACTION: What should be done next? (one specific suggestion)

5. CAN_ANSWER: Can we answer the user's question now? (YES/NO)

RESPOND IN THIS FORMAT:
RELEVANCE: [one of the relevance levels]
KEY_FINDINGS:
- [finding 1]
- [finding 2]
INFORMATION_GAP: [one of the gap levels]
NEXT_ACTION: [specific suggestion or "Ready to answer"]
CAN_ANSWER: [YES or NO]

Be concise and specific. Focus on whether THIS result helps answer the question."""

        return prompt

    def _parse_verification_response(self, response: str) -> VerificationResult:
        """Parse the LLM verification response.

        Args:
            response: Raw LLM response

        Returns:
            Parsed VerificationResult
        """
        # Extract fields with fallbacks
        relevance_str = self._extract_field(response, "RELEVANCE")
        gap_str = self._extract_field(response, "INFORMATION_GAP")
        next_action = self._extract_field(response, "NEXT_ACTION")
        can_answer_str = self._extract_field(response, "CAN_ANSWER")

        # Parse relevance
        relevance_map = {
            "HIGHLY_RELEVANT": RelevanceScore.HIGHLY_RELEVANT,
            "RELEVANT": RelevanceScore.RELEVANT,
            "SOMEWHAT_RELEVANT": RelevanceScore.SOMEWHAT_RELEVANT,
            "NOT_RELEVANT": RelevanceScore.NOT_RELEVANT,
        }
        relevance = relevance_map.get(
            relevance_str.upper().strip(),
            RelevanceScore.RELEVANT  # Default to relevant
        )

        # Parse information gap
        gap_map = {
            "COMPLETE": InformationGap.COMPLETE,
            "MINOR_GAPS": InformationGap.MINOR_GAPS,
            "SIGNIFICANT_GAPS": InformationGap.SIGNIFICANT_GAPS,
            "UNCLEAR": InformationGap.UNCLEAR,
        }
        information_gap = gap_map.get(
            gap_str.upper().strip(),
            InformationGap.SIGNIFICANT_GAPS  # Default to gaps remaining
        )

        # Extract key findings
        key_findings = self._extract_findings(response)

        # Parse can_answer
        can_answer = "YES" in can_answer_str.upper()

        # Calculate confidence based on response clarity
        confidence = self._calculate_confidence(response)

        return VerificationResult(
            relevance=relevance,
            information_gap=information_gap,
            key_findings=key_findings,
            next_suggested_action=next_action if next_action else None,
            can_answer_now=can_answer,
            confidence=confidence,
        )

    def _extract_field(self, response: str, field_name: str) -> str:
        """Extract a field value from the response.

        Args:
            response: LLM response
            field_name: Field to extract

        Returns:
            Field value or empty string
        """
        import re
        pattern = rf"{field_name}:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, response, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_findings(self, response: str) -> List[str]:
        """Extract key findings from response.

        Args:
            response: LLM response

        Returns:
            List of findings
        """
        findings = []
        in_findings_section = False

        for line in response.split("\n"):
            if "KEY_FINDINGS:" in line.upper():
                in_findings_section = True
                continue

            if in_findings_section:
                # Stop at next section
                if ":" in line and line.strip().isupper():
                    break

                # Extract bullet points
                line = line.strip()
                if line.startswith("-") or line.startswith("•"):
                    finding = line[1:].strip()
                    if finding:
                        findings.append(finding)

        return findings

    def _calculate_confidence(self, response: str) -> float:
        """Calculate confidence in the verification.

        Args:
            response: LLM response

        Returns:
            Confidence score 0.0-1.0
        """
        # Simple heuristic: check if all fields are present
        required_fields = ["RELEVANCE", "KEY_FINDINGS", "INFORMATION_GAP", "CAN_ANSWER"]
        fields_present = sum(1 for field in required_fields if field in response.upper())
        return fields_present / len(required_fields)

    def _create_default_verification(self) -> VerificationResult:
        """Create a default verification when verification is disabled or unavailable.

        Returns:
            Default VerificationResult that allows continuation
        """
        return VerificationResult(
            relevance=RelevanceScore.RELEVANT,
            information_gap=InformationGap.SIGNIFICANT_GAPS,
            key_findings=[],
            next_suggested_action=None,
            can_answer_now=False,
            confidence=0.5,
        )

    def get_completion_assessment(self) -> Dict[str, Any]:
        """Get overall assessment of whether the question can be answered.

        Returns:
            Dictionary with completion assessment
        """
        if not self.verification_history:
            return {
                "can_answer": False,
                "confidence": 0.0,
                "reason": "No tool results verified yet",
            }

        # Check recent verifications
        recent_verifications = self.verification_history[-3:]  # Last 3

        # If any recent verification says we can answer, we probably can
        can_answer_votes = sum(1 for v in recent_verifications if v.can_answer_now)
        complete_gaps = sum(1 for v in recent_verifications if v.information_gap == InformationGap.COMPLETE)

        can_answer = can_answer_votes > 0 or complete_gaps > 0
        confidence = sum(v.confidence for v in recent_verifications) / len(recent_verifications)

        return {
            "can_answer": can_answer,
            "confidence": confidence,
            "total_findings": len(self.accumulated_findings),
            "reason": f"{can_answer_votes} recent verifications indicate completion" if can_answer else "More information needed",
        }

    def reset(self) -> None:
        """Reset the verifier state for a new conversation turn."""
        self.user_question = None
        self.verification_history = []
        self.accumulated_findings = []

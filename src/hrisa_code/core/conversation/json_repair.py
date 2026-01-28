"""JSON repair utilities for handling malformed tool call JSON from LLMs."""

import json
import re
from typing import Any, Dict, Optional, Tuple


def repair_json(json_str: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Attempt to repair common JSON issues in LLM-generated tool calls.

    Common issues this handles:
    - Unterminated strings
    - Missing commas between key-value pairs
    - Trailing commas
    - Invalid escape sequences
    - Single quotes instead of double quotes
    - Missing closing brackets

    Args:
        json_str: Potentially malformed JSON string

    Returns:
        Tuple of (parsed_dict, error_message)
        - If successful: (dict, None)
        - If failed: (None, error_description)
    """
    if not json_str or not json_str.strip():
        return None, "Empty JSON string"

    # Try parsing as-is first
    try:
        return json.loads(json_str), None
    except json.JSONDecodeError:
        pass  # Continue to repair attempts

    original_json = json_str
    repairs_attempted = []

    # Repair 1: Fix common escape sequence issues
    # Replace invalid escapes like \n in paths with \\n
    if '\\' in json_str and '\\\\' not in json_str:
        # Be careful not to break valid escapes
        json_str = json_str.replace('\\n', '\\\\n')
        json_str = json_str.replace('\\t', '\\\\t')
        json_str = json_str.replace('\\r', '\\\\r')
        repairs_attempted.append("escaped special chars")

        try:
            return json.loads(json_str), None
        except json.JSONDecodeError:
            pass

    # Repair 2: Replace single quotes with double quotes (be careful with content)
    if "'" in original_json and '"' not in original_json:
        json_str = original_json.replace("'", '"')
        repairs_attempted.append("replaced single quotes")

        try:
            return json.loads(json_str), None
        except json.JSONDecodeError:
            pass

    # Repair 3: Remove trailing commas before closing brackets
    json_str = re.sub(r',\s*}', '}', original_json)
    json_str = re.sub(r',\s*]', ']', json_str)
    if json_str != original_json:
        repairs_attempted.append("removed trailing commas")

        try:
            return json.loads(json_str), None
        except json.JSONDecodeError:
            pass

    # Repair 4: Add missing commas between key-value pairs
    # This is tricky and error-prone, so only try obvious cases
    json_str = re.sub(r'"\s*\n\s*"', '",\n    "', original_json)
    if json_str != original_json:
        repairs_attempted.append("added missing commas")

        try:
            return json.loads(json_str), None
        except json.JSONDecodeError:
            pass

    # Repair 5: Try to close unterminated strings
    # Count quotes to see if they're balanced
    quote_count = original_json.count('"') - original_json.count('\\"')
    if quote_count % 2 != 0:
        # Odd number of quotes - try adding one at the end
        json_str = original_json.rstrip() + '"'
        repairs_attempted.append("closed unterminated string")

        try:
            return json.loads(json_str), None
        except json.JSONDecodeError:
            pass

    # Repair 6: Try to close missing brackets
    open_braces = original_json.count('{') - original_json.count('\\{')
    close_braces = original_json.count('}') - original_json.count('\\}')
    if open_braces > close_braces:
        json_str = original_json + ('}' * (open_braces - close_braces))
        repairs_attempted.append(f"added {open_braces - close_braces} closing braces")

        try:
            return json.loads(json_str), None
        except json.JSONDecodeError:
            pass

    # All repair attempts failed
    repairs_str = ", ".join(repairs_attempted) if repairs_attempted else "no repairs attempted"
    return None, f"Could not repair JSON ({repairs_str})"


def extract_json_objects(text: str) -> list[str]:
    """Extract potential JSON objects from text.

    Uses a more robust approach than regex to find JSON-like structures.

    Args:
        text: Text that may contain JSON objects

    Returns:
        List of potential JSON strings
    """
    json_objects = []
    stack = []
    start_idx = None
    in_string = False
    escape_next = False

    for i, char in enumerate(text):
        # Handle string context
        if escape_next:
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        # Only process brackets outside strings
        if in_string:
            continue

        if char == '{':
            if not stack:  # Start of new potential JSON object
                start_idx = i
            stack.append('{')
        elif char == '}':
            if stack and stack[-1] == '{':
                stack.pop()
                if not stack and start_idx is not None:
                    # Found complete JSON object
                    json_str = text[start_idx:i+1]
                    json_objects.append(json_str)
                    start_idx = None

    return json_objects


def validate_tool_call_structure(obj: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate that a parsed JSON object has the expected tool call structure.

    Args:
        obj: Parsed JSON object

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(obj, dict):
        return False, "Not a dictionary"

    if "name" not in obj:
        return False, "Missing 'name' field"

    if "arguments" not in obj:
        return False, "Missing 'arguments' field"

    if not isinstance(obj["name"], str):
        return False, "'name' must be a string"

    if not isinstance(obj["arguments"], dict):
        return False, "'arguments' must be a dictionary"

    return True, None

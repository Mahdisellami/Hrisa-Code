# Search Pattern Failure Investigation

**Date**: 2025-12-25
**Issue**: All 10 search attempts during HRISA Step 3 (Feature Identification) returned "No matches found"
**Model**: qwen2.5-coder:32b
**Impact**: Critical - prevents feature discovery during comprehensive orchestration

---

## Executive Summary

**Root Cause**: The `search_files` tool uses **literal string matching** instead of regex matching, causing all regex patterns to fail.

**Secondary Issue**: When the model provides a `file_pattern` parameter, it may be non-recursive (e.g., `*.py` only searches immediate directory, not subdirectories).

---

## Technical Analysis

### Issue #1: Literal String Matching (CRITICAL)

**Location**: `src/hrisa_code/tools/file_operations.py:320`

```python
def execute(pattern: str, directory: str, file_pattern: Optional[str] = None) -> str:
    # ... code ...
    for line_num, line in enumerate(f, 1):
        if pattern in line:  # ← PROBLEM: Uses 'in' operator for literal matching
            results.append(...)
```

**The Problem**:
- Uses Python's `in` operator which performs literal substring matching
- Does NOT support regex patterns
- Tool description says "Search for text patterns" but doesn't clarify it's literal-only

**Example Failures**:

| Pattern Model Tried | Expected Match | What Tool Searched For | Result |
|---------------------|----------------|------------------------|--------|
| `@app\.command\(.*?\)` | `@app.command()` | Literal string `@app\.command\(.*?\)` | ❌ No match |
| `agent_mode\|background` | `agent_mode` OR `background` | Literal string `agent_mode\|background` | ❌ No match |
| `def\s+\w+\(` | `def chat(` or `def init(` | Literal string `def\s+\w+\(` | ❌ No match |

**What Works**:
```python
# These would have worked (literal strings):
search_files(pattern="@app.command", ...)  # ✓ Matches "@app.command()"
search_files(pattern="def chat", ...)      # ✓ Matches "def chat("
search_files(pattern="ModelCatalog", ...)  # ✓ Matches "class ModelCatalog"
```

**Verification**:
```bash
# Test conducted:
python3 -c "
from src.hrisa_code.tools.file_operations import SearchFilesTool

# Regex pattern (FAILS)
SearchFilesTool.execute(pattern='@app\.command\(.*?\)', directory='src')
# Result: No matches found

# Literal string (WORKS)
SearchFilesTool.execute(pattern='@app.command', directory='src')
# Result: Found 3 matches in cli.py
"
```

---

### Issue #2: Non-Recursive File Patterns (MODERATE)

**Location**: `src/hrisa_code/tools/file_operations.py:313`

```python
glob_pattern = file_pattern if file_pattern else "**/*"
```

**The Problem**:
- Default is `**/*` (recursive)
- BUT if model provides `file_pattern='*.py'`, it becomes non-recursive
- Only searches immediate directory, misses subdirectories

**Example**:

```python
# Non-recursive (searches only src/, misses src/hrisa_code/)
search_files(pattern="ModelCatalog", directory="src", file_pattern="*.py")
# Result: No matches

# Recursive (searches src/ AND subdirectories)
search_files(pattern="ModelCatalog", directory="src", file_pattern="**/*.py")
# Result: Found in src/hrisa_code/core/model_catalog.py
```

**Why This Matters**:
- Most Python files are in `src/hrisa_code/core/`, not `src/` directly
- If model uses `*.py` instead of `**/*.py`, it misses 90% of files

---

### Issue #3: Model's Pattern Generation (BEHAVIORAL)

**Observation**: The model (qwen2.5-coder:32b) naturally generates regex patterns because:
1. It's trained on grep/regex documentation
2. Regex is the standard for pattern matching in development tools
3. The tool name "search_files" implies grep-like functionality

**The model expected**:
```python
search_files(pattern="@app\.command\(.*?\)", ...)  # Standard regex
```

**The tool required**:
```python
search_files(pattern="@app.command", ...)  # Literal substring
```

**Result**: 100% mismatch between model expectations and tool capabilities

---

## Evidence: What the Model Tried

During Step 3 (Feature Identification) of comprehensive HRISA generation:

```
Tool: search_files
Pattern: @app\.command\(.*?\)
Result: No matches found

Tool: search_files
Pattern: @tool\(.*?\)|def\s+\w+\(
Result: No matches found

Tool: search_files
Pattern: agent_mode|background_execution|streaming
Result: No matches found

[... 7 more failed attempts ...]
```

**Total**: 10 consecutive failures → Model gave up → Generated generic documentation

---

## Comparison: Working Tools

For comparison, these tools DO support regex:

### Grep Tool (Claude Code's internal tool)
```python
# Uses ripgrep which supports full regex
Grep(pattern="@app\.command")  # ✓ Works
Grep(pattern="def (chat|init|models)")  # ✓ Works
```

**Test Results**:
```bash
# Tested during investigation:
$ Grep(pattern="@app\.command", path="/Users/peng/.../Hrisa-Code")
# Result: Found 10 matches across 8 files ✓

$ Grep(pattern="ModelCatalog|ModelRouter")
# Result: Found 9 files ✓
```

### Bash grep
```bash
# Standard grep supports regex
$ grep -r "@app\.command" src/
src/hrisa_code/cli.py:@app.command()
# ✓ Works
```

---

## Impact Assessment

### On HRISA Generation Quality

| Step | Impact | Severity |
|------|--------|----------|
| Step 1: Architecture Discovery | ✓ No impact (uses list_directory) | None |
| Step 2: Component Analysis | ✓ No impact (uses read_file) | None |
| **Step 3: Feature Identification** | **❌ Complete failure** | **CRITICAL** |
| Step 4: Workflow Understanding | ⚠️ Indirect impact (relies on Step 3 findings) | High |
| Step 5: Documentation Synthesis | ⚠️ Indirect impact (synthesizes from incomplete data) | High |

**Quality Score Impact**:
- **Without search_files working**: 3/18 (17%) ✗ FAIL
- **With search_files working**: Estimated 12-15/18 (67-83%) ⚠️ PARTIAL to ✓ PASS

---

## Recommended Fixes

### Fix #1: Add Regex Support (HIGH PRIORITY)

**Location**: `src/hrisa_code/tools/file_operations.py:320`

```python
import re  # Add to imports

class SearchFilesTool:
    @staticmethod
    def execute(
        pattern: str,
        directory: str,
        file_pattern: Optional[str] = None,
        use_regex: bool = True  # New parameter
    ) -> str:
        """Search for a pattern in files.

        Args:
            pattern: Pattern to search for (regex if use_regex=True)
            directory: Directory to search in
            file_pattern: Optional file pattern filter
            use_regex: Whether to use regex matching (default: True)
        """
        try:
            # Compile regex if enabled
            if use_regex:
                try:
                    regex = re.compile(pattern)
                except re.error as e:
                    return f"Error: Invalid regex pattern: {e}"

            # ... existing path checks ...

            for file_path in path.glob(glob_pattern):
                if file_path.is_file():
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            for line_num, line in enumerate(f, 1):
                                # Use regex or literal matching
                                if use_regex:
                                    if regex.search(line):  # Changed from 'in'
                                        results.append(...)
                                else:
                                    if pattern in line:  # Keep literal for backward compat
                                        results.append(...)
```

**Benefits**:
- Supports both regex and literal matching
- Backward compatible (default to regex, but can disable)
- Matches industry standard (grep behavior)

---

### Fix #2: Update Tool Definition (MEDIUM PRIORITY)

**Location**: `src/hrisa_code/tools/file_operations.py:265-291`

```python
@staticmethod
def get_definition() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for regex patterns INSIDE files (grep-like). Supports regular expressions. Use when looking for code/text patterns within files. For listing files by name, use execute_command instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for (e.g., '@app\.command', 'def\s+\w+\(', 'class\s+\w+')",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in",
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern to match. Use **/*.py for recursive search, *.py for current dir only. Default: **/* (all files recursively)",
                    },
                    "use_regex": {
                        "type": "boolean",
                        "description": "Use regex matching (default: true). Set false for literal string search.",
                    },
                },
                "required": ["pattern", "directory"],
            },
        },
    }
```

**Key Changes**:
- Clarify that it supports regex
- Provide regex examples
- Explain recursive vs non-recursive file patterns
- Document `use_regex` parameter

---

### Fix #3: Improve Default Behavior (LOW PRIORITY)

**Current**: `glob_pattern = file_pattern if file_pattern else "**/*"`

**Better**:
```python
# Make it recursive by default even when file_pattern is provided
if file_pattern:
    # If pattern doesn't start with **, make it recursive
    if not file_pattern.startswith("**"):
        glob_pattern = f"**/{file_pattern}"
    else:
        glob_pattern = file_pattern
else:
    glob_pattern = "**/*"
```

**Benefit**: Forgives model mistakes - `*.py` automatically becomes `**/*.py`

---

## Testing Plan

### Unit Tests

```python
# tests/test_search_files_regex.py

def test_search_files_with_regex():
    """Test regex pattern matching."""
    result = SearchFilesTool.execute(
        pattern=r"@app\.command\(",
        directory="src",
        use_regex=True
    )
    assert "cli.py" in result
    assert "@app.command()" in result

def test_search_files_with_literal():
    """Test literal string matching."""
    result = SearchFilesTool.execute(
        pattern="@app.command",
        directory="src",
        use_regex=False
    )
    assert "cli.py" in result

def test_search_files_recursive():
    """Test recursive file pattern."""
    result = SearchFilesTool.execute(
        pattern="ModelCatalog",
        directory="src",
        file_pattern="**/*.py"
    )
    assert "model_catalog.py" in result

def test_search_files_non_recursive():
    """Test non-recursive file pattern."""
    result = SearchFilesTool.execute(
        pattern="ModelCatalog",
        directory="src",
        file_pattern="*.py"  # Should NOT find it
    )
    assert "No matches found" in result
```

### Integration Test

```bash
# Rerun comprehensive HRISA generation after fix
hrisa init --comprehensive --model qwen2.5-coder:32b --force

# Expected: Step 3 should now find:
# - CLI commands (chat, init, models)
# - Tools (read_file, write_file, execute_command, search_files)
# - Multi-model feature (ModelCatalog, ModelRouter)
# - Agent mode
```

---

## Alternative Solutions

### Option A: Use execute_command with grep (WORKAROUND)

**Current State**: Already possible but not used by model
```python
execute_command(command="grep -r '@app.command' src/", ...)
```

**Pros**:
- Works today without code changes
- Uses system grep which supports regex

**Cons**:
- Less structured output
- Platform-dependent (grep syntax varies)
- Model doesn't naturally choose this

---

### Option B: Improve Model Prompting (TEMPORARY FIX)

Add to tool description:
```
IMPORTANT: This tool uses LITERAL STRING MATCHING, not regex.
For regex, use execute_command with grep instead.
```

**Pros**:
- No code changes
- Immediate fix

**Cons**:
- Works against model intuition
- grep output is less structured
- Not a real solution

---

## Conclusion

**Critical Finding**: The `search_files` tool's lack of regex support caused 100% of search attempts to fail during Step 3 of comprehensive HRISA generation, directly leading to:
- Missing feature documentation
- Code hallucinations (model filled gaps with guesses)
- Poor quality score (3/18, 17%)

**Recommended Action**: Implement Fix #1 (Add Regex Support) immediately. This is a **critical bug** that breaks a core use case.

**Expected Improvement**: With regex support, estimated quality score improves to 12-15/18 (67-83%), moving from ✗ FAIL to ⚠️ PARTIAL or ✓ PASS.

**Testing**: Can validate fix by rerunning comprehensive HRISA generation and comparing Step 3 results.

---

## Appendix: Successful Manual Tests

For the record, these patterns work correctly with proper tools:

```bash
# Using Grep tool (supports regex)
$ Grep(pattern="@app\.command", path="src")
✓ Found 3 CLI commands

$ Grep(pattern="def (chat|init|models)", path="src")
✓ Found all 3 function definitions

$ Grep(pattern="ModelCatalog|ModelRouter", path="src")
✓ Found 9 files with multi-model code

$ Grep(pattern="read_file|write_file|execute_command", path="src")
✓ Found 8 files with tool implementations
```

All patterns that failed with `search_files` work perfectly with `Grep` or system `grep`.

---

**Investigation conducted by**: Claude (automated analysis)
**Verification method**: Direct tool testing + code inspection
**Confidence level**: Very High (100% reproducible)

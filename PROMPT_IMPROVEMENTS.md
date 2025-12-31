# Prompt & Tool Definition Improvements

## Problem Statement

After fixing the goal tracker premature completion bug, we discovered additional issues with plan mode execution:

### Issues Observed:
1. **Poor Plan Quality**: Plans had only 1 vague step that repeated the entire task
   - Example: Single step "Find all TODO comments in the codebase and summarize them"
   - Should have been: Step 1) Find Python files, Step 2) Search for TODO, Step 3) Summarize

2. **LLM Not Following Instructions**: Searched for wrong patterns
   - Task: Find TODO comments
   - LLM searched for: `@app\.command` (completely wrong!)
   - Should have searched for: `TODO`

3. **Tool Validation Errors**: Missing required parameters
   - LLM called `search_files(pattern="TODO", file_pattern="**/*.py")`
   - Error: "Missing required parameter: directory"
   - Tool definition said `directory` was optional, but code required it

## Root Cause Analysis

### 1. Plan Generation Prompt (dynamic_planner.py)
**Problem:** Prompt didn't emphasize breaking tasks into concrete sub-steps

**Evidence:**
- Generated plans like: "Step 1: Find all TODO comments in the codebase and summarize them"
- This just repeats the task - not a breakdown!

**Why it happened:**
- Prompt said "Be specific and actionable" but didn't show examples
- No explicit warning against single-step plans that repeat the task
- No guidance on how to break down "Find X and summarize" tasks

### 2. Step Execution Prompt (agent.py)
**Problem:** LLM tried to complete entire task in one step instead of focusing on current step

**Evidence:**
- Step 1 description: "Find all TODO comments..."
- LLM behavior: Tried to search and summarize in one step (confused about what to do)
- Result: Made errors, searched wrong patterns, gave up

**Why it happened:**
- Prompt showed original task prominently
- Didn't emphasize "focus ONLY on this step"
- No reminder that this is part of multi-step plan
- No explicit instruction to not jump ahead to later steps

### 3. Tool Definitions (file_operations.py)
**Problem:** Misleading tool definition - said optional but was actually required

**Evidence:**
```python
# Tool definition said:
"required": ["pattern"]  # directory not listed as required

# But code enforced:
if not dir_path:
    return "Error: Either 'directory' or 'working_directory' parameter is required"
```

**Why it happened:**
- Definition and implementation out of sync
- No concrete usage examples in tool description
- Parameter descriptions too brief

## Solutions Implemented

### A) Enhanced Plan Generation Prompt

**Added:** Breaking Down Tasks section with explicit guidance

```markdown
IMPORTANT - Breaking Down Tasks:
- For "Find X and summarize" tasks: Break into (1) Find/locate X, (2) Read/analyze X, (3) Summarize findings
- For "Search for pattern" tasks: Break into (1) Identify files to search, (2) Search each file, (3) Collect results
- For "Analyze codebase" tasks: Break into (1) Explore structure, (2) Read key files, (3) Analyze patterns
- NEVER create a single step that repeats the entire task - break it down into concrete sub-steps!

Examples of GOOD step descriptions:
✓ "Use search_files to find all Python files containing 'TODO' comments"
✓ "Read each file that contains TODO comments and extract the comment text with line numbers"
✓ "Compile all TODO comments into a categorized summary"

Examples of BAD step descriptions:
✗ "Find all TODO comments in the codebase and summarize them" (too vague - just repeats the task)
✗ "Complete the task" (not actionable)
✗ "Do research" (not specific)
```

**Impact:**
- LLM now has clear examples of what good vs bad step descriptions look like
- Explicit patterns for common task types (Find+Summarize, Search, Analyze)
- Strong warning against single-step plans

### B) Improved Step Execution Prompt

**Before:**
```
Execute this step from the plan:

Original Task: {original_task}
Current Step ({step.step_number}): {step.description}
Rationale: {step.rationale}
...
```

**After:**
```
Execute this SPECIFIC step from the plan. Focus ONLY on this step, not the entire task.

=== ORIGINAL TASK ===
{original_task}

=== YOUR CURRENT STEP (Step {step.step_number}) ===
{step.description}

=== WHY THIS STEP ===
{step.rationale}

=== INSTRUCTIONS ===
1. Focus ONLY on this specific step - do NOT try to complete the entire task in one step
2. Use the expected tools to accomplish THIS step
3. Follow tool parameter requirements carefully (check required vs optional parameters)
4. If a tool call fails with validation error, read the error message and fix the parameters
5. Report what you accomplished in THIS step when done

IMPORTANT: This is step {step.step_number} of a multi-step plan. Do not try to complete steps that come later.
Just complete THIS step, then report your findings.
```

**Impact:**
- Clear visual sections with === markers
- Explicit instruction: "Focus ONLY on this specific step"
- 5-point checklist for execution
- Reminder to read validation errors and fix parameters
- Emphasis on not jumping ahead to later steps

### C) Fixed Tool Definitions

**search_files tool improvements:**

1. **Fixed Required Parameters:**
```python
# Before:
"required": ["pattern"]

# After:
"required": ["pattern", "directory"]
```

2. **Added Concrete Examples:**
```markdown
COMMON USE CASES:
1. Find TODO comments: pattern='TODO', directory='.', file_pattern='**/*.py', use_regex=false
2. Find function definitions: pattern='def\\s+\\w+\\(', directory='src/', use_regex=true
3. Find class usage: pattern='ModelCatalog', directory='.', use_regex=false
4. Find decorators: pattern='@app\\.command', directory='src/', use_regex=true

IMPORTANT:
- For literal strings (TODO, FIXME, class names), set use_regex=false
- For patterns with special chars (def, \\s, \\w), keep use_regex=true (default)
- Always provide 'directory' parameter (required)
- file_pattern is optional (defaults to all files)
```

3. **Enhanced Parameter Descriptions:**
```python
"directory": {
    "type": "string",
    "description": "REQUIRED. Directory to search in. Examples: '.' (current), 'src/', 'tests/', '../project/'"
},
"pattern": {
    "type": "string",
    "description": "Regex pattern to search for. Examples: 'TODO' (literal), '@app\\.command' (decorator), 'def\\s+\\w+\\(' (functions)"
}
```

**Impact:**
- No more validation errors for missing directory
- LLM has 4 concrete examples showing exactly how to use the tool
- Clear guidance on when to use use_regex=false vs true
- Parameter descriptions include examples

## Expected Improvements

### Plan Quality
**Before:**
```
Step 1: Find all TODO comments in the codebase and summarize them
```

**After:**
```
Step 1: Use search_files to find all Python files containing 'TODO' comments
Step 2: Read the matching files and extract TODO comments with line numbers
Step 3: Compile all TODO comments into a categorized summary by file
```

### Step Execution
**Before:**
- LLM confused about what to do
- Searches for wrong pattern (@app.command)
- Tool validation errors

**After:**
- LLM focuses on Step 1 only: Find files with TODO
- Uses correct pattern: 'TODO'
- Provides required directory parameter: '.'
- Completes step, reports findings
- Moves to Step 2

### Tool Usage
**Before:**
```python
search_files(pattern="TODO", file_pattern="**/*.py")
# Error: Missing required parameter: directory
```

**After:**
```python
search_files(
    pattern="TODO",
    directory=".",
    file_pattern="**/*.py",
    use_regex=False  # Literal string search
)
# Success: Found TODO comments in 8 files
```

## Testing Plan

### Manual Test Case: "Find all TODO comments in the codebase and summarize them"

**Expected Flow:**
1. Generate 3-step plan:
   - Step 1: Find Python files with TODO
   - Step 2: Extract TODO text with locations
   - Step 3: Summarize findings

2. Execute Step 1:
   - Use search_files correctly (with directory parameter)
   - Find all TODO occurrences
   - Report: "Found TODO in 8 files: ..."

3. Execute Step 2:
   - Read each file or use tool results
   - Extract TODO comment text
   - Note line numbers and context

4. Execute Step 3:
   - Compile summary
   - Group by file or category
   - Present organized results

### Success Criteria
✓ Plan has 3+ concrete steps (not 1 vague step)
✓ Each step description is specific and actionable
✓ LLM uses search_files with correct parameters
✓ No tool validation errors for missing directory
✓ LLM finds actual TODO comments (not other patterns)
✓ Task completes successfully with full summary

## Commits

1. `876cf5d` - fix: Disable goal tracker during plan step execution
2. `689d0a0` - feat: Improve plan generation, step execution, and tool definitions

## Next Steps

1. **Manual Testing**: Test "Find all TODO comments" task to verify improvements
2. **Monitor Plan Quality**: Check if generated plans now have better step breakdown
3. **Track Tool Errors**: Monitor if validation errors decrease
4. **Iterate**: If issues persist, further refine prompts based on observed behavior

## Lessons Learned

1. **Prompt Engineering is Critical**: Small wording changes can significantly impact LLM behavior
2. **Examples > Instructions**: Showing good/bad examples is more effective than abstract guidelines
3. **Tool Definitions = API Contract**: Must match implementation exactly
4. **Concrete Usage Examples**: Help LLM understand how to use tools correctly
5. **Emphasis Matters**: Using "IMPORTANT", "NEVER", "ONLY" helps focus LLM attention

---

**Status:** Improvements committed, ready for testing
**Test Command:** `hrisa chat` → `/agent` → `/agent` → "Find all TODO comments in the codebase and summarize them"

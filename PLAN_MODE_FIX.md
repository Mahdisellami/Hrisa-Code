# Plan Mode Fix: Goal Tracker Premature Completion

## Issue Discovered

User tested plan mode with the task: "Find all TODO comments in the codebase and summarize them"

**Expected behavior:**
1. Generate plan with steps
2. Execute step: Find Python files
3. Execute step: Search each file for TODO comments
4. Summarize all TODO comments found

**Actual behavior:**
1. Generated plan with 1 step
2. Executed step: Find Python files (✓)
3. **Plan marked complete without searching file contents**
4. No TODO comments were found or summarized

## Root Cause Analysis

### The Problem

When executing plan steps via `agent._execute_step()`, the conversation manager's goal tracker was evaluating completion against the **ORIGINAL user question** instead of the **SPECIFIC step requirement**.

**Goal Tracker Evaluation:**
```
User asked: "Find all TODO comments in the codebase and summarize them"

Tool results obtained:
- find_files: Found 42 Python files

Question: Can we answer the user's question?
→ LLM Response: "COMPLETE - we have the list of files"
```

**The flaw:** Goal tracker thinks "we CAN answer the question" (we know which files exist), but it doesn't realize we need to **search within those files** for TODO comments.

### Why This Happened

1. **Plan Step Execution Flow:**
   ```
   agent.execute_with_plan()
   → agent._execute_step(step)
      → conversation.process_message(step_prompt)
         → [tool calls execute]
         → goal_tracker.check_progress()  ← PROBLEM HERE
            → "Can we answer user's question?"
            → Returns COMPLETE (too early!)
         → Stops execution, forces final response
   ```

2. **Goal Tracker's Perspective:**
   - Evaluates: "Based on these tool results, can we answer the user's question?"
   - In normal/agent mode: Correct behavior (detect when task is done)
   - In plan mode: Incorrect behavior (evaluates overall task, not step completion)

3. **Step vs Task Completion:**
   - Plan steps are **sub-tasks**, not the complete answer
   - Goal tracker doesn't distinguish between:
     - "Is this STEP complete?" (what plan mode needs)
     - "Is the overall TASK complete?" (what goal tracker checks)

## Solution Implemented

### Approach: Conditional Goal Tracking

Add a flag to temporarily disable goal tracking during plan step execution, letting plan orchestration handle step completion logic instead.

### Code Changes

#### 1. ConversationManager (`conversation.py`)

**Added flag:**
```python
self._goal_tracking_enabled = True  # Can be disabled during plan step execution
```

**Check flag before evaluation:**
```python
# Before: Always check goal progress
if goal_status == GoalStatus.UNKNOWN and self.goal_tracker.should_check_progress():
    goal_status = await self.goal_tracker.check_progress()

# After: Only check if enabled
if self._goal_tracking_enabled and goal_status == GoalStatus.UNKNOWN and self.goal_tracker.should_check_progress():
    goal_status = await self.goal_tracker.check_progress()
```

**Check flag before intervention:**
```python
# Before: Always handle intervention
if goal_status in (GoalStatus.COMPLETE, GoalStatus.STUCK, ...):
    intervention_msg = self.goal_tracker.get_intervention_message(goal_status)

# After: Only if enabled
if self._goal_tracking_enabled and goal_status in (GoalStatus.COMPLETE, ...):
    intervention_msg = self.goal_tracker.get_intervention_message(goal_status)
```

**Check flag before forcing response:**
```python
# Before: Force final response if complete
tools_for_next_round = None if goal_status == GoalStatus.COMPLETE else self.tool_definitions

# After: Only enforce if enabled
tools_for_next_round = None if (self._goal_tracking_enabled and goal_status == GoalStatus.COMPLETE) else self.tool_definitions
```

#### 2. AgentLoop (`agent.py`)

**Disable during step execution:**
```python
async def _execute_step(self, step: "PlanStep", original_task: str) -> str:
    """Execute a single plan step."""
    prompt = self._build_step_prompt(step, original_task)

    # Disable goal tracking during plan step execution
    # Goal tracker evaluates overall task completion, but we're executing a specific step
    # Let the plan orchestration handle step completion logic instead
    original_goal_tracking = self.conversation._goal_tracking_enabled
    self.conversation._goal_tracking_enabled = False

    try:
        # Execute via conversation manager
        response = await self.conversation.process_message(prompt)
        return response or "Step completed"
    finally:
        # Restore original goal tracking state
        self.conversation._goal_tracking_enabled = original_goal_tracking
```

## Impact

### What Changed

**Plan Mode:**
- Goal tracker disabled during step execution
- Steps can run to completion without premature interruption
- Plan orchestration determines when step is done

**Normal/Agent Mode:**
- Goal tracker remains enabled (default behavior)
- No change in functionality
- Still detects task completion automatically

### Testing

**All 48 tests pass**, including:
- Goal tracker integration tests
- Approval manager tests
- Tool execution tests
- Multi-turn conversation tests

### New Execution Flow

```
agent.execute_with_plan()
→ agent._execute_step(step)
   → [DISABLE goal tracking]
   → conversation.process_message(step_prompt)
      → [tool calls execute]
      → [NO goal tracking interruption]
      → [LLM can continue with more tool calls]
   → [RESTORE goal tracking]
   → step completes when LLM provides response
→ plan.mark_step_complete()
```

## Example: Before vs After

### Before (Broken)

```
User: Find all TODO comments in the codebase and summarize them

[Plan generated with 1 step]

► Step 1/1: Find all TODO comments...

Tool: find_files → Found 42 Python files
Goal Tracker: "You have enough info to answer" ✗
[Forced to final response]

Agent: I found 42 Python files in the codebase.
[Task incomplete - no TODO comments found!]
```

### After (Fixed)

```
User: Find all TODO comments in the codebase and summarize them

[Plan generated with proper steps]

► Step 1/2: Find all Python files
Tool: find_files → Found 42 Python files
[Goal tracking DISABLED - step continues]

► Step 2/2: Search files for TODO comments
Tool: search_files → Found TODO comments in 8 files
Tool: read_file → Read files with TODOs
[Goal tracking DISABLED - step continues]

Agent: I found 15 TODO comments across 8 files:
1. src/core/config.py:54 - TODO: Add validation
2. src/tools/git_operations.py:123 - TODO: Add git push
...
[Task complete - all TODOs found and summarized!]
```

## Design Considerations

### Why Not: Modify Goal Tracker to Understand Steps?

**Alternative considered:** Make goal tracker aware of plan context
- Would require passing step information to goal tracker
- More complex: goal tracker would need to evaluate "is THIS STEP done?"
- Tighter coupling between goal tracker and plan orchestration

**Why disabled flag is better:**
- Simple: 1 flag, 3 checks
- Clear separation of concerns:
  - Goal tracker: Evaluates overall task completion
  - Plan orchestration: Manages step execution
- Easy to test and reason about
- No architectural changes needed

### Why Not: Use Separate Conversation Instance?

**Alternative considered:** Create new conversation manager for plan steps
- Would lose conversation history
- Would need to duplicate tool setup
- More resource intensive
- Harder to maintain state across steps

**Why flag toggle is better:**
- Preserves conversation history
- Reuses existing conversation manager
- Minimal memory overhead
- State persists across steps

## Future Enhancements

### Potential Improvements:

1. **Step-Aware Goal Tracking:**
   - Goal tracker could evaluate "is this step done?" vs "is task done?"
   - Would require passing step description and success criteria
   - More intelligent but more complex

2. **Adaptive Goal Tracking:**
   - Enable for exploration steps (where early completion is desired)
   - Disable for execution steps (where full completion needed)
   - Context-aware goal tracking behavior

3. **Plan Refinement Integration:**
   - If step discovers complexity, generate sub-plan
   - Goal tracker could signal "need more detail in plan"
   - Dynamic plan expansion based on progress

## Summary

**Fixed:** Plan mode now executes steps fully without premature completion

**Root Cause:** Goal tracker evaluated overall task completion instead of step completion

**Solution:** Disable goal tracking during plan step execution, re-enable after

**Testing:** All 48 tests pass, no regressions

**Impact:** Plan mode can now handle multi-step tasks correctly!

---

**Commit:** `876cf5d` - fix: Disable goal tracker during plan step execution

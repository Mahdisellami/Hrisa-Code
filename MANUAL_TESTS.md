# Manual Tests for Plan Mode

This document provides manual test scenarios to validate the plan mode integration end-to-end.

## Prerequisites

1. Make sure Ollama is running: `ollama serve`
2. Have a capable model pulled: `ollama pull qwen2.5-coder:32b` (recommended)
3. Install hrisa-code: `pip install -e .`

## Test Suite

### Test 1: Mode Cycling - Basic UI

**Objective:** Verify mode switching works correctly with visual feedback.

**Steps:**
1. Start interactive session:
   ```bash
   hrisa chat
   ```

2. Observe the welcome banner:
   - Should show current mode: `Mode: normal`
   - Mode should be dim/gray (default state)

3. Press SHIFT+TAB or type `/agent`
   - Mode should change to `agent` (cyan/blue color)
   - Panel should display "Agent Mode" description
   - Should explain autonomous multi-step execution

4. Press SHIFT+TAB or type `/agent` again
   - Mode should change to `plan` (magenta/pink color)
   - Panel should display "Plan Mode" description
   - Should explain intelligent planning

5. Press SHIFT+TAB or type `/agent` again
   - Mode should cycle back to `normal` (dim/gray)
   - Panel should display "Normal Mode" description

6. Type `/help`
   - Should show current mode with color coding
   - Should explain mode cycling

**Expected Result:** Clean mode cycling with color-coded visual feedback.

---

### Test 2: Plan Mode - Simple Task

**Objective:** Execute a simple task in plan mode to verify basic functionality.

**Task:** "List all Python files in the src/ directory"

**Steps:**
1. Start hrisa chat: `hrisa chat`
2. Switch to plan mode: `/agent` (twice to get to plan mode)
3. Enter the task: `List all Python files in the src/ directory`
4. Observe the execution

**Expected Result:**
- Complexity detector should classify as SIMPLE
- Plan may be minimal (1-2 steps) or fallback to normal execution
- Task completes successfully
- Mode resets to normal after completion

**What to Watch:**
- Does it generate a plan or fallback to direct execution?
- If plan generated: is it reasonable for this simple task?
- Does the task complete correctly?

---

### Test 3: Plan Mode - Moderate Task

**Objective:** Execute a moderate complexity task requiring multiple steps.

**Task:** "Add error logging to all functions in src/hrisa_code/tools/file_operations.py"

**Steps:**
1. Start hrisa chat: `hrisa chat`
2. Switch to plan mode: `/agent` (twice)
3. Enter the task above
4. Watch the plan generation and execution

**Expected Result:**
- Complexity detector classifies as MODERATE
- Plan generated with 3-5 steps, such as:
  1. Read the file to understand structure
  2. Identify functions without error logging
  3. Design logging approach
  4. Implement logging in each function
  5. Verify changes
- Visual progress tracking: 0% → 20% → 40% → 60% → 80% → 100%
- Step-by-step execution with clear indicators
- Plan completion panel at the end
- Mode resets to normal

**What to Watch:**
- Does the plan make sense for the task?
- Are dependencies handled correctly?
- Is progress tracking visible?
- Do steps execute in logical order?

---

### Test 4: Plan Mode - Complex Task

**Objective:** Execute a complex multi-phase task.

**Task:** "Refactor the ConversationManager class to use dependency injection for all its components"

**Steps:**
1. Start hrisa chat: `hrisa chat`
2. Switch to plan mode: `/agent` (twice)
3. Enter the task above
4. Watch the plan generation and execution

**Expected Result:**
- Complexity detector classifies as COMPLEX
- Detailed plan with 5-10 steps:
  1. Exploration: Read current ConversationManager implementation
  2. Exploration: Identify all dependencies
  3. Design: Design dependency injection approach
  4. Design: Plan migration strategy
  5. Implementation: Create dependency interfaces
  6. Implementation: Refactor constructor
  7. Implementation: Update instantiation sites
  8. Testing: Verify no functionality breaks
- Rich visual feedback with table display
- Dependencies between steps respected
- Comprehensive completion summary

**What to Watch:**
- Is the plan thorough and well-structured?
- Does it explore before implementing?
- Are design steps included?
- Does it consider testing?

---

### Test 5: Error Recovery

**Objective:** Verify plan mode handles errors gracefully.

**Task:** "Read a file that doesn't exist and then list the current directory"

**Steps:**
1. Start hrisa chat: `hrisa chat`
2. Switch to plan mode: `/agent` (twice)
3. Enter: `Read the file /nonexistent/fake/file.txt and then list files in the current directory`
4. Watch error handling

**Expected Result:**
- Plan generates with 2 steps
- First step fails (file not found)
- Error message displayed in red: `✗ Step 1 failed: ...`
- Second step still executes successfully
- Error count tracked
- Plan shows as incomplete but with partial progress
- Completion panel shows which steps succeeded/failed

**What to Watch:**
- Does execution continue after failure?
- Is the error clearly displayed?
- Does the completion summary reflect the failure?

---

### Test 6: Agent Mode Comparison

**Objective:** Compare agent mode vs plan mode for the same task.

**Task:** "Add type hints to all functions in src/hrisa_code/core/config.py"

**Steps - Part A (Agent Mode):**
1. Start hrisa chat: `hrisa chat`
2. Switch to agent mode: `/agent` (once)
3. Enter the task
4. Note the execution style

**Steps - Part B (Plan Mode):**
1. Type `/agent` twice to get to plan mode
2. Enter the same task
3. Note the execution style

**Expected Differences:**
- **Agent Mode:** Iterative execution, reflection between steps, autonomous decisions
- **Plan Mode:** Upfront plan generation, structured step-by-step execution, progress tracking

**What to Watch:**
- Which mode feels more predictable?
- Which provides better visibility?
- Which is more suitable for this task?

---

### Test 7: Plan Adaptation

**Objective:** See if plan mode adapts based on discoveries.

**Task:** "Find all TODO comments in the codebase and create a summary file"

**Steps:**
1. Start hrisa chat: `hrisa chat`
2. Switch to plan mode: `/agent` (twice)
3. Enter the task
4. Watch for plan adaptation triggers

**Expected Result:**
- Initial plan might estimate scope
- As it searches files, it discovers actual TODO count
- If significantly different from estimate, may show: `📋 Plan refined based on discoveries`
- Execution adapts to findings

**What to Watch:**
- Does the plan mention adaptation capability?
- If unexpected results found, does it adjust?
- Is the refinement message displayed?

---

### Test 8: Mode Reset After Task

**Objective:** Verify modes auto-reset to normal after execution.

**Steps:**
1. Start hrisa chat: `hrisa chat`
2. Switch to plan mode: `/agent` (twice)
3. Confirm mode is `plan` (magenta)
4. Execute any simple task: `List files in the current directory`
5. After task completes, check current mode
6. Type another message without changing modes

**Expected Result:**
- After task completes, mode automatically resets to `normal`
- Next message uses normal mode (standard conversation)
- Visual indicator shows `normal` mode

**What to Watch:**
- Does mode reset happen automatically?
- Is it clear to the user that mode changed?
- Can user easily enter plan mode again if needed?

---

### Test 9: Help Command in Different Modes

**Objective:** Verify `/help` shows current mode context.

**Steps:**
1. Start hrisa chat: `hrisa chat`
2. Type `/help` - note current mode display
3. Type `/agent` - switch to agent mode
4. Type `/help` - note current mode display (should be cyan)
5. Type `/agent` - switch to plan mode
6. Type `/help` - note current mode display (should be magenta)

**Expected Result:**
- Help panel always shows current mode with correct color
- Mode descriptions in help text make sense
- Easy to understand how to cycle modes

---

### Test 10: Stress Test - Multiple Tasks

**Objective:** Execute multiple tasks back-to-back in plan mode.

**Tasks:**
1. "Count all Python files in the src/ directory"
2. "Find the largest Python file by line count"
3. "List all function definitions in src/hrisa_code/cli.py"

**Steps:**
1. Start hrisa chat: `hrisa chat`
2. Switch to plan mode: `/agent` (twice)
3. Execute task 1, wait for completion
4. Switch back to plan mode: `/agent` (twice, since it resets)
5. Execute task 2, wait for completion
6. Switch back to plan mode again
7. Execute task 3, wait for completion

**Expected Result:**
- Each task generates appropriate plan
- Each task executes successfully
- Mode resets after each task
- No state leakage between tasks
- Error counts reset between tasks

**What to Watch:**
- Are plans independent?
- Does each task start fresh?
- Any performance degradation over multiple tasks?

---

## Quick Smoke Tests

If you're short on time, run these quick tests:

### Minimal Test (5 minutes)
1. Start: `hrisa chat`
2. Cycle modes: `/agent` → `/agent` → `/agent`
3. Try plan mode: `/agent` twice, then: "List all files in the current directory"
4. Verify completion and reset

### Medium Test (10 minutes)
1. Run Test 1 (Mode Cycling)
2. Run Test 2 (Simple Task)
3. Run Test 3 (Moderate Task)
4. Verify all work correctly

### Full Test (30-60 minutes)
Run all 10 tests in sequence and document any issues.

---

## What to Report

For each test, note:
- ✅ **Pass** - Worked as expected
- ⚠️ **Partial** - Worked but with minor issues
- ❌ **Fail** - Did not work as expected

Document any:
- Unexpected behavior
- Confusing UI elements
- Error messages
- Performance issues
- Suggestions for improvement

---

## Troubleshooting

**Issue:** Mode doesn't seem to change
- **Fix:** Make sure you're pressing SHIFT+TAB, not just TAB
- **Alternative:** Use `/agent` command instead

**Issue:** Plan mode doesn't generate a plan
- **Fix:** Task may be too simple, try a more complex task
- **Note:** Very simple tasks may fallback to direct execution

**Issue:** Ollama connection errors
- **Fix:** Make sure `ollama serve` is running
- **Fix:** Check model is pulled: `ollama list`

**Issue:** Tool execution failures
- **Fix:** Check file paths are correct
- **Fix:** Verify permissions on working directory

---

## Advanced Tests

Once basic tests pass, try these advanced scenarios:

1. **Parallel-suitable tasks:** "Search for both TODO and FIXME comments"
   - Watch if plan identifies parallelizable steps

2. **Uncertain scope:** "Fix any bugs in the authentication system"
   - Watch how it handles vague requirements

3. **Multi-file changes:** "Rename all instances of 'foo' to 'bar' across the codebase"
   - Watch if plan breaks down by file or by phase

4. **Research tasks:** "Analyze the architecture and suggest improvements"
   - Watch if plan includes analysis and synthesis steps

---

## Success Criteria

Plan mode is working correctly if:
- ✅ Mode cycling is smooth and visual
- ✅ Plans are generated for moderate/complex tasks
- ✅ Steps execute in logical order
- ✅ Progress tracking is visible
- ✅ Errors are handled gracefully
- ✅ Mode resets after tasks
- ✅ Visual feedback is clear and helpful
- ✅ Tasks complete successfully

Happy testing!

# Q3 2025 Real Project Test V5 - Instructions

**Date:** 2026-01-02
**Version:** V5 (Multi-Model Strategy Implementation)
**Objective:** Validate multi-model selection strategy - use right model for right task

---

## What's Different in V5?

### 🎯 Major Innovation: Multi-Model Strategy

**The Problem:**
- **V3 (deepseek-r1:70b)**: Thinks but doesn't act (6 hours, 0 files)
- **V4 (qwen2.5-coder:32b)**: Acts but loops/errors (1 hour, 2 broken files)

**V5 Solution - Use BOTH Models for Their Strengths:**

```
Step Type          | Model              | Why?
-------------------|--------------------|----------------------------------
Exploration        | qwen2.5:32b        | Fast, good at search/navigation
Design             | qwen2.5:32b        | Planning, no code needed
Implementation     | qwen2.5-coder:7b   | Smaller = fewer loops
Testing            | qwen2.5-coder:32b  | Larger = better test generation
Documentation      | qwen2.5:32b        | General text generation
Validation         | qwen2.5-coder:32b  | Code analysis
Refactoring        | qwen2.5-coder:7b   | Focused code changes
```

### 🆕 V5 Improvements

1. **Multi-Model Selection System**
   - Agent automatically switches models per step type
   - Configured via `model_mapping` in config.yaml
   - Console shows model switches: "→ Using qwen2.5-coder:7b for implementation step"

2. **Smaller Implementation Model**
   - Using qwen2.5-coder:7b instead of 32b for implementation
   - Hypothesis: Smaller model = less likely to over-search
   - Still using 32b for testing (needs more reasoning)

3. **Strategic Model Usage**
   - General models (qwen2.5:32b) for exploration/design
   - Code models (qwen2.5-coder) only when writing/testing code
   - Each model stays in its comfort zone

### What We're Keeping from V4

- ✅ Tool call verification (catches false completions)
- ✅ File existence checks
- ✅ CLI/CRUD heuristic (14-step specific plan)
- ✅ Code quality validator (syntax/import checks)
- ✅ Plan Mode UX (confirmation modal)

---

## Critical: V5 vs V3/V4 Expectations

| Metric | V3 (deepseek-r1) | V4 (qwen2.5-coder:32b) | **V5 Target (Multi-Model)** |
|--------|------------------|------------------------|------------------------------|
| **Strategy** | Single reasoning model | Single code model | Multi-model per step |
| **Implementation Model** | deepseek-r1:70b | qwen2.5-coder:32b | qwen2.5-coder:7b |
| **Execution Time** | 6 hours | ~1 hour (stopped) | 15-25 minutes |
| **Files Generated** | 1 (broken test) | 2 (wrong structure) | 5+ (correct structure) |
| **LOC** | 63 lines | 135 lines | 400-600 lines |
| **Tool Calls** | ~5 | ~70 (many loops) | 20-40 (fewer loops) |
| **Search Loops** | None (no tool calls) | 20 rounds x 2 steps | 0-5 rounds max |
| **Working Features** | 0% | 8% | 60-80% |
| **Expected Rating** | ⭐ (0%) | ⭐ (8%) | ⭐⭐ or ⭐⭐⭐ (60-95%) |

**Key Hypothesis:** Smaller code model (7b) will loop less than 32b, while general model (32b) handles exploration better.

---

## Pre-Test Verification

### 1. Verify Model Configuration

```bash
cat ~/.config/hrisa-code/config.yaml
```

**Expected output:**
```yaml
model:
  name: "qwen2.5:32b"  # ← Default for planning
  temperature: 0.7

  # Multi-model mapping for different step types
  model_mapping:
    exploration: "qwen2.5:32b"         # ← General model
    design: "qwen2.5:32b"              # ← General model
    implementation: "qwen2.5-coder:7b" # ← Smaller code model!
    testing: "qwen2.5-coder:32b"       # ← Larger code model
    documentation: "qwen2.5:32b"
    validation: "qwen2.5-coder:32b"
    refactoring: "qwen2.5-coder:7b"

ollama:
  host: "http://localhost:11434"

tools:
  enabled: true
```

**If config is wrong:**
```bash
# Config was updated to this in the latest changes
cat ~/.config/hrisa-code/config.yaml
```

### 2. Verify Required Models Exist

```bash
ollama list
```

**Required models:**
- ✅ qwen2.5:32b (or qwen2.5:latest)
- ✅ qwen2.5-coder:7b
- ✅ qwen2.5-coder:32b

**If any missing:**
```bash
ollama pull qwen2.5:32b
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:32b
```

### 3. Clean Previous Test State

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager

# Remove old test files
rm -rf *.py task_manager/ __pycache__/ *.db tests/

# Verify clean state
ls -la
# Should see only: TEST_*.md, requirements.txt, README.md
```

### 4. Verify Code Changes

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code

# Check agent.py has multi-model logic
grep -A 5 "_select_model_for_step" src/hrisa_code/core/planning/agent.py

# Check config.py has model_mapping
grep -A 3 "model_mapping" src/hrisa_code/core/config.py

# Expected: Both methods should exist
```

---

## Test Execution Steps

### Phase 1: Start HRISA Session

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
hrisa chat
```

**Expected:**
- Clean startup with no errors
- Shows available tools
- Ready for input

### Phase 2: Activate Plan Mode

**Type in chat:**
```
SHIFT + TAB  # Press once to cycle to Plan Mode
```

**Expected confirmation prompt:**
```
⚠ Entering Plan Mode

Plan Mode generates a multi-step execution plan...

The system will:
  1. Analyze task complexity
  2. Generate 4-15 step execution plan
  3. Execute each step with visual progress
  4. Use previous step results to avoid redundancy

Enter Plan Mode? (y/n):
```

**Type:** `y` + ENTER

**Expected banner:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ YOU ARE NOW IN PLAN MODE     ┃
┃                              ┃
┃ Your next task will be       ┃
┃ planned and executed         ┃
┃ step-by-step.                ┃
┃                              ┃
┃ Watch the bottom toolbar for ┃
┃ persistent mode indicator.   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Phase 3: Submit Task

**Paste this task (from requirements.txt):**
```
Build a Python CLI task management application with the following features:
1. Add tasks with title, description, priority, status, tags, due date
2. List all tasks with formatting
3. View task details by ID
4. Edit tasks
5. Delete tasks
6. Search and filter tasks
7. Use SQLite for data persistence
8. Use Typer for the CLI interface
```

**Press ENTER**

### Phase 4: Watch Plan Generation

**Expected output:**
```
Analyzing task complexity...
Task complexity: COMPLEX - generating execution plan...

Generated Plan: Build CLI Task Manager
Status: GENERATED
Steps: 14

Step 1: [PENDING] Review project structure and requirements
Step 2: [PENDING] Design data model with all required fields
Step 3: [PENDING] Design CLI command structure and interface
Step 4: [PENDING] Implement database layer and models.py
Step 5: [PENDING] Implement database connection in db.py
Step 6: [PENDING] Implement add command
Step 7: [PENDING] Implement list command
Step 8: [PENDING] Implement view command
Step 9: [PENDING] Implement edit command
Step 10: [PENDING] Implement delete command
Step 11: [PENDING] Implement search/filter command
Step 12: [PENDING] Create main entry point
Step 13: [PENDING] Create integration tests
Step 14: [PENDING] Create README documentation

Proceed with plan? (y/n):
```

**Type:** `y` + ENTER

### Phase 5: Watch Model Switching (NEW IN V5!)

**Expected console output as execution progresses:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1/14: Review project structure and requirements
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ Using qwen2.5:32b for exploration step    ← MODEL SWITCH!
Executing step 1: Review project structure and requirements...
[Tool calls appear here...]
✓ Step 1 complete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2/14: Design data model with all required fields
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ Using qwen2.5:32b for design step          ← SAME MODEL
Executing step 2: Design data model...
[Output appears...]
✓ Step 2 complete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4/14: Implement database layer and models.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ Using qwen2.5-coder:7b for implementation step  ← SWITCHED TO CODE MODEL!
Executing step 4: Implement database layer and models.py...
[write_file tool call...]
Successfully wrote to models.py
✓ Step 4 complete
```

**Key observations to note:**
1. ✅ Model switches announced before each step
2. ✅ Exploration/Design use qwen2.5:32b
3. ✅ Implementation uses qwen2.5-coder:7b (smaller!)
4. ✅ Testing uses qwen2.5-coder:32b (larger)

### Phase 6: Monitor Progress

**Watch for these success indicators:**

✅ **Good Signs:**
- Tool calls show `write_file` creating .py files
- Each implementation step creates 1+ files
- No 20-round search loops
- Files appear in root directory (not subdirectory!)
- Syntax validation passes
- Model switches between steps

⚠️ **Warning Signs (but OK):**
- Verification warnings (system is working)
- Import warnings (non-critical)
- Type hint warnings (non-critical)
- Short retries (1-3 rounds OK)

🚫 **Critical Issues (stop test):**
- Search loops lasting 10+ rounds
- Steps marked complete but no files written
- Continuous syntax errors
- Process hangs for 30+ minutes

**If critical issues occur:**
```
CTRL+C in terminal (stop test)
Save full output to TEST_OUTPUT_V5.txt
```

### Phase 7: Wait for Completion

**Expected duration:** 15-25 minutes

**Expected final output:**
```
✓ Step 14 complete

Plan complete!
Status: COMPLETED
```

---

## Post-Test Evaluation

### 1. Collect Generated Files

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager

# List all generated files
ls -lah

# Expected files:
# ✓ models.py (Task data model)
# ✓ db.py (Database connection)
# ✓ cli.py (Main CLI commands)
# ✓ main.py or __main__.py (Entry point)
# ✓ test_*.py (Tests)
# ✓ README.md (Maybe)
```

### 2. Count Lines of Code

```bash
find . -name "*.py" -exec wc -l {} + | tail -1
```

**V5 Target:** 400-600 lines total

### 3. Check File Quality

```bash
# Check syntax of all Python files
for file in *.py; do
  echo "=== $file ==="
  python3 -m py_compile "$file" && echo "✓ Syntax OK" || echo "✗ Syntax Error"
done
```

### 4. Test Basic Functionality

```bash
# Try installing dependencies
pip install -r requirements.txt

# Try running the CLI
python cli.py --help          # or python main.py --help
python cli.py add "Test task" # Try adding a task
python cli.py list            # Try listing tasks
```

**Expected:** At least 2-3 commands should work without errors

### 5. Analyze Tool Call Patterns

**Search test output for loop patterns:**
```bash
grep -c "search_files" TEST_OUTPUT_V5.txt  # Count search calls
grep -c "write_file" TEST_OUTPUT_V5.txt    # Count write calls
grep -c "Using qwen2.5-coder:7b" TEST_OUTPUT_V5.txt  # Count 7b model usage
```

**V5 Target:**
- search_files: 10-25 calls (not 50+)
- write_file: 5-10 calls
- qwen2.5-coder:7b usage: 6-8 times (one per implementation step)

---

## Success Criteria for V5

### Minimum Success (⭐⭐ - 60%)
- ✅ Plan generated (14 steps)
- ✅ Models switch per step type
- ✅ At least 3 files created
- ✅ 300+ LOC total
- ✅ 2+ commands work
- ✅ No syntax errors
- ✅ Execution time < 30 minutes

### Target Success (⭐⭐⭐ - 80%)
- ✅ All minimum criteria
- ✅ 5+ files created
- ✅ 400-600 LOC
- ✅ 4+ commands work
- ✅ Proper directory structure
- ✅ Search loops < 5 rounds
- ✅ Model switching visible

### Exceptional Success (⭐⭐⭐⭐ - 95%)
- ✅ All target criteria
- ✅ All 7 features work
- ✅ Tests run and pass
- ✅ Zero search loops
- ✅ Production-quality code
- ✅ Execution time < 20 minutes

---

## Troubleshooting

### Issue: Models Not Switching

**Symptom:** Console doesn't show "→ Using X for Y step"

**Fix:**
```bash
# Verify config loaded
cat ~/.config/hrisa-code/config.yaml | grep -A 10 model_mapping

# If empty, config not loading - check path
ls -la ~/.config/hrisa-code/

# Should see config.yaml there
```

### Issue: Model Not Found

**Symptom:** Error: "model qwen2.5-coder:7b not found"

**Fix:**
```bash
ollama pull qwen2.5-coder:7b
# Wait for download to complete
ollama list | grep qwen2.5-coder:7b
```

### Issue: Still Getting Search Loops

**Symptom:** Step shows 10+ search_files calls

**Action:**
- Note which step number
- Note which model was being used
- Let it continue (don't stop immediately)
- Check if loop detector stops it after 20 rounds
- This data is valuable for next iteration

### Issue: Syntax Errors in Generated Code

**Symptom:** Code quality validator blocks writes

**Action:**
- This is EXPECTED occasionally
- Check if model retries
- Note if same error repeats 3+ times
- If stuck on same error, stop test

---

## Data Collection for Evaluation

**Save the following information:**

1. **Full terminal output:**
   ```bash
   # Copy ALL output from test start to completion
   # Save to: TEST_OUTPUT_V5.txt
   ```

2. **Generated files:**
   ```bash
   tar -czf test_v5_files.tar.gz *.py task_manager/ tests/
   ```

3. **Execution metrics:**
   - Start time
   - End time
   - Total duration
   - Number of model switches observed
   - Number of search loops (if any)
   - Final file count
   - Final LOC count

4. **Subjective notes:**
   - Did model switching feel smooth?
   - Were smaller code models faster?
   - Any unexpected behaviors?
   - Which steps had the best results?

---

## Expected Outcome

**Hypothesis:** Multi-model strategy will combine strengths of both model types:
- General models (qwen2.5:32b) explore efficiently without over-searching
- Small code models (qwen2.5-coder:7b) implement without looping
- Large code models (qwen2.5-coder:32b) generate comprehensive tests

**Predicted Rating:** ⭐⭐ or ⭐⭐⭐ (60-80% feature completion)

**Key Innovation:** This is the first test where the system uses MULTIPLE models in a single session, each model doing what it does best.

---

## Next Steps After V5

If V5 succeeds (⭐⭐ or better):
1. Create TEST_EVALUATION_V5.md comparing all versions
2. Document multi-model best practices
3. Consider V6 with loop prevention (not just detection)
4. Test on different task types (API server, library, etc.)

If V5 still has issues:
1. Analyze which model caused which problems
2. Try different model combinations
3. Consider qwen2.5-coder:14b for implementation (middle ground)
4. Add retry logic for syntax errors

---

**Good luck with V5! This test validates your insight that multi-model strategy is the solution. 🚀**

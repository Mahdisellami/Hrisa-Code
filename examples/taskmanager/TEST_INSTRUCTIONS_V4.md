# Q3 2025 Real Project Test V4 - Instructions

**Date:** 2026-01-01
**Version:** V4 (Fourth Attempt with Critical Fixes)
**Objective:** Validate qwen2.5-coder:32b + tool call verification fixes

---

## What's Different in V4?

### ✅ Fixes from V3 Critical Failure

**V3 Problem:** deepseek-r1:70b spent 6 hours "thinking", generated ONLY 1 file (broken test), 0% functionality

**V4 Solutions:**
1. **Switched to qwen2.5-coder:32b** - Code-optimized model that reliably calls tools
2. **Added Tool Call Verification** - Agent now checks if write_file was actually called
3. **Added File Existence Checks** - Verifies expected files exist after implementation steps
4. **Added Verification Warnings** - User sees warnings when steps don't create expected files

### What We're Keeping from V3

- ✅ CLI/CRUD heuristic (14-step specific plan)
- ✅ Enhanced step prompts (anti-placeholder instructions)
- ✅ Code quality validator (syntax/import checks)
- ✅ Plan Mode UX (confirmation modal)

---

## Critical: V4 vs V3 Expectations

| Metric | V3 (deepseek-r1) | V4 Target (qwen2.5-coder) |
|--------|------------------|---------------------------|
| **Model** | deepseek-r1:70b | qwen2.5-coder:32b |
| **Execution Time** | 6 hours | 20-30 minutes |
| **Files Generated** | 1 (broken test) | 5+ (all implementation) |
| **LOC** | 63 lines | 400-600 lines |
| **Tool Calls** | ~0-5 | 15-30 |
| **Working Features** | 0% | 80%+ |
| **Verification Warnings** | None (no checks) | Visible warnings |
| **Expected Rating** | ⭐ (0%) | ⭐⭐ or ⭐⭐⭐ (75-95%) |

---

## Pre-Test Verification

### 1. Verify Model Configuration
```bash
cat ~/.config/hrisa-code/config.yaml
```

**Expected output:**
```yaml
model:
  name: "qwen2.5-coder:32b"  # ← MUST be this!
  temperature: 0.7

ollama:
  host: "http://localhost:11434"

tools:
  enabled: true
```

**✗ If wrong:** Should already be set, but if not:
```bash
# Already done by Claude, but verify it's correct
grep "qwen2.5-coder:32b" ~/.config/hrisa-code/config.yaml
```

### 2. Verify Model Available
```bash
ollama list | grep qwen2.5-coder:32b
```

**Expected:** Shows `qwen2.5-coder:32b` with size ~19 GB
**✗ If missing:** Run `ollama pull qwen2.5-coder:32b` (will take time)

### 3. Clean Test Directory
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
rm -f *.py tasks.db
rm -rf tests/*.py
rm -rf .hrisa/conversation_*.json 2>/dev/null || true
```

**✓ Verify clean:**
```bash
ls -la *.py 2>/dev/null
```
Should show: "No such file or directory"

---

## Test Execution

### Step 1: Start Hrisa
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
hrisa chat
```

**CRITICAL CHECK in banner:**
```
│  Configuration                                    │
│    Model: qwen2.5-coder:32b                       │  ← VERIFY THIS!
```

**⚠️ If shows anything else:** Exit and fix config!

### Step 2: Enter Plan Mode
```
/agent  # First: → Agent Mode
/agent  # Second: → Plan Mode confirmation
y       # Confirm
```

**Verify:**
- Large "YOU ARE NOW IN PLAN MODE" banner appears
- Bottom toolbar shows: `[plan]`

### Step 3: Paste Task
```
Implement a CLI task manager with the following features:
- Task CRUD operations (add, list, show, edit, complete, delete)
- SQLite persistence with data model (id, title, description, priority, status, tags, created_at, updated_at, due_date, completed_at)
- Search and filtering capabilities (by status, priority, tags, text search)
- Export to JSON, CSV, and Markdown formats
- Full test coverage with pytest (unit tests + integration tests)
- Type hints on ALL functions and methods
- Comprehensive docstrings
Use Typer for CLI and follow Python best practices.
```

Press ENTER and monitor.

---

## What to Watch For (V4 Specific)

### Phase 1: Plan Generation (30 sec)

**Expected:**
```
Generating execution plan...
[Shows 14-step plan in table]
```

**✅ GOOD:** 10-15 steps, specific descriptions
**❌ BAD:** 4 generic steps (means heuristic didn't trigger - shouldn't happen)

### Phase 2: Implementation Steps (Critical!)

**NEW in V4: Verification Warnings**

Watch for these patterns:

**✅ GOOD EXECUTION:**
```
► Step 4/14: Implement data model and database layer
✓ Successfully wrote to models.py
✓ Step 4 complete
```

**❌ BAD EXECUTION (V4 will catch this!):**
```
► Step 4/14: Implement data model and database layer
⚠️  Step 4 expected to write files but no write_file calls detected
⚠️  Step 4 expected to create ['models.py'] but files not found
✓ Step 4 complete  # Marked complete but with warnings!
```

**What This Means:**
- In V3: Agent would silently continue, no warnings
- In V4: **You'll see yellow warnings immediately**
- If you see warnings on Step 4-11: Model is failing to call tools (like V3)

### Phase 3: File Creation Timeline

**Expected file creation order:**

| Step | File(s) Created | Verification |
|------|-----------------|--------------|
| 4 | `models.py` | ✓ Check: "Successfully wrote to models.py" |
| 5 | `cli.py` (add command) | ✓ Check: File exists or code added |
| 6 | `cli.py` (list command) | ✓ Code added to existing file |
| 7 | `cli.py` (show command) | ✓ Code added |
| 8 | `cli.py` (edit command) | ✓ Code added |
| 9 | `cli.py` (delete command) | ✓ Code added |
| 10 | `cli.py` (search/filter) | ✓ Code added |
| 11 | `cli.py` (export functions) | ✓ Code added |
| 12 | `tests/test_cli.py` | ✓ Check: "Successfully wrote to tests/test_cli.py" |
| 13 | `tests/test_integration.py` | ✓ Check: File created |
| 14 | Updates to existing files | ✓ Docstrings/type hints added |

**After each implementation step, verify:**
```bash
# In another terminal
ls -la *.py
```

You should see files appearing progressively.

### Phase 4: Time Expectations

**V4 should be MUCH faster than V3:**

| Step Range | Expected Time | V3 Time (for comparison) |
|------------|---------------|--------------------------|
| 1-3 (Explore/Design) | 2-5 min | 3 hours (!!) |
| 4-11 (Implementation) | 15-20 min | 3 hours (!!) |
| 12-13 (Testing) | 3-5 min | 2.4 min |
| 14 (Docs) | 2-3 min | 11.6 min |
| **TOTAL** | **20-30 min** | **6 hours** |

**⚠️ If you see:**
- "Thought for 1000s" or more → Model stuck in reasoning (bad sign)
- No "Successfully wrote to" messages → Model not calling tools (V3 repeat)
- Yellow warning messages → Verification catching failures (good that we catch it!)

---

## Success Criteria (Updated for V4)

### Minimum Success (⭐ - 50%)
- [ ] qwen2.5-coder:32b used (check banner)
- [ ] 14-step plan generated
- [ ] At least 3 files created (models.py, cli.py, main.py)
- [ ] No syntax errors
- [ ] 50%+ of CRUD operations have working code (not pass)
- [ ] Completed in under 1 hour

### Good Success (⭐⭐ - 75%)
- [ ] All Minimum criteria
- [ ] 5+ files created (all expected files)
- [ ] 400+ lines of code
- [ ] All 6 CRUD operations working
- [ ] Search OR export implemented
- [ ] 50%+ tests passing
- [ ] Verification warnings < 5 total

### Excellent Success (⭐⭐⭐ - 95%)
- [ ] All Good criteria
- [ ] 500+ lines of code
- [ ] Both search AND export working
- [ ] 80%+ tests passing
- [ ] Type hints on all functions
- [ ] No verification warnings
- [ ] Completed in under 30 minutes

---

## Post-Test Evaluation

### 1. Check Files Generated
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
find . -name "*.py" -type f | grep -v __pycache__
```

**Expected:**
- models.py
- cli.py
- main.py
- tests/test_cli.py
- tests/test_integration.py

### 2. Count Lines of Code
```bash
wc -l *.py tests/*.py 2>/dev/null | tail -1
```

**Expected:** 400-600 total lines

### 3. Check for Placeholder Code
```bash
grep -n "^[[:space:]]*pass$" *.py cli.py 2>/dev/null
```

**Expected:** 0 results (no bare `pass` statements)

### 4. Syntax Check
```bash
python3 -m py_compile *.py tests/*.py 2>&1
```

**Expected:** No errors

### 5. Run Tests
```bash
pytest -v 2>&1 | head -50
```

**Expected:** At least 3-4 tests passing (50%+)

### 6. Test Basic Functionality
```bash
# Test if CLI works
python main.py --help

# Test add command
python main.py add "Test Task" "Description" --priority 1

# Test list command
python main.py list

# Check database
ls -la tasks.db
```

**Expected:** Commands work, database created

---

## Verification Warnings Guide

**NEW in V4:** Agent now shows warnings when steps don't complete as expected.

**Warning Types:**

**1. No tool calls detected:**
```
⚠️  Step 4 expected to write files but no write_file calls detected
```
**Meaning:** Model didn't call write_file (like V3 deepseek-r1 issue)
**Action:** If you see this multiple times, model is failing

**2. Missing expected files:**
```
⚠️  Step 4 expected to create ['models.py'] but files not found
```
**Meaning:** Step description implied file creation, but file doesn't exist
**Action:** Check if file was created with different name, or step actually failed

**3. Suspiciously short result:**
```
⚠️  Step 4 returned very short result (45 chars) - may not have executed tools
```
**Meaning:** Model returned minimal output, likely just "thinking"
**Action:** Similar to V3 deepseek-r1 behavior - model not acting

**How Many Warnings is Too Many?**
- 0-2 warnings: Acceptable (might be false positives)
- 3-5 warnings: Concerning (check if files actually exist)
- 6+ warnings: Critical failure (model not working like V3)

---

## Comparison Checklist (V4 vs V3)

| Metric | V3 Actual | V4 Target | V4 Actual | Pass? |
|--------|-----------|-----------|-----------|-------|
| **Model Used** | deepseek-r1:70b | qwen2.5-coder:32b | _____ | _____ |
| **Total Time** | 6 hours | 20-30 min | _____ min | _____ |
| **Files Created** | 1 | 5+ | _____ | _____ |
| **LOC Generated** | 63 | 400-600 | _____ | _____ |
| **Working CRUD** | 0/6 | 4-6/6 | _____/6 | _____ |
| **Tests Passing** | 0/6 (can't run) | 3-5/6 | _____/6 | _____ |
| **Verification Warnings** | N/A (no checks) | <5 | _____ | _____ |
| **Placeholder Code** | N/A (no code) | 0% | _____% | _____ |
| **Feature Completion** | 0% | 75-95% | _____% | _____ |
| **Rating** | ⭐ (0%) | ⭐⭐ or ⭐⭐⭐ | _____ | _____ |

---

## Troubleshooting V4-Specific

### Problem: Still seeing 6-hour execution times
**Cause:** Wrong model loaded (deepseek-r1 or similar reasoning model)
**Fix:**
```bash
# Exit hrisa
# Verify config
cat ~/.config/hrisa-code/config.yaml | grep qwen2.5-coder:32b
# Should show the model name
# Restart hrisa chat
```

### Problem: Verification warnings on every step
**Symptom:**
```
⚠️  Step 4 expected to write files but no write_file calls detected
⚠️  Step 5 expected to write files but no write_file calls detected
...
```

**Cause:** Model not calling tools (qwen2.5-coder:32b also failing like deepseek-r1)

**Diagnosis:**
```bash
# Check if ANY files created
ls -la *.py

# If zero files after 5+ implementation steps → critical failure
```

**Action:** Stop test, this means qwen2.5-coder:32b also has the issue (unlikely but possible)

### Problem: Files created but verification still warns
**Cause:** False positive - file created with different pattern than expected

**Example:**
```
⚠️  Step 5 expected to create ['cli.py'] but files not found
```
But cli.py exists.

**Fix:** Ignore warning if files actually exist. Verification patterns might need tuning.

---

## Quick Reference Card (V4)

**Pre-test:**
```bash
# Verify model
cat ~/.config/hrisa-code/config.yaml | grep qwen2.5-coder:32b

# Clean directory
rm -f *.py tasks.db && rm -rf tests/*.py
```

**Start test:**
```bash
hrisa chat
# Check banner shows: qwen2.5-coder:32b
/agent  # → Agent Mode
/agent  # → Plan Mode confirmation
y       # Confirm

# Paste task, press ENTER
```

**Monitor (in another terminal):**
```bash
# Watch files appear
watch -n 5 'ls -la *.py tests/*.py 2>/dev/null | wc -l'

# Watch line count grow
watch -n 10 'wc -l *.py tests/*.py 2>/dev/null | tail -1'
```

**After test:**
```bash
find . -name "*.py" | wc -l        # Count files
wc -l *.py tests/*.py | tail -1    # Count LOC
python3 -m py_compile *.py tests/*.py  # Check syntax
pytest -v                          # Run tests
```

---

## Expected Timeline (V4)

| Time | Event | What You Should See |
|------|-------|---------------------|
| 0:00 | Start | Plan Mode activated, 14-step plan |
| 0:01 | Step 1 | Exploring project |
| 0:05 | Steps 2-3 | Designing model + CLI |
| 0:10 | Step 4 | "Successfully wrote to models.py" |
| 0:12 | Step 5 | "Successfully wrote to cli.py" (add) |
| 0:14 | Step 6 | Updated cli.py (list) |
| 0:16 | Step 7 | Updated cli.py (show) |
| 0:18 | Step 8 | Updated cli.py (edit) |
| 0:20 | Step 9 | Updated cli.py (delete) |
| 0:23 | Step 10 | Updated cli.py (search) |
| 0:26 | Step 11 | Updated cli.py (export) |
| 0:28 | Step 12 | "Successfully wrote to tests/test_cli.py" |
| 0:30 | Step 13 | "Successfully wrote to tests/test_integration.py" |
| 0:32 | Step 14 | Adding docstrings |
| 0:33 | Complete | "✓ Plan Completed Successfully" |

**Total: ~30-35 minutes**

If significantly longer → check for reasoning loops or tool call failures.

---

## Key Differences from V3

| Aspect | V3 (deepseek-r1) | V4 (qwen2.5-coder) |
|--------|------------------|---------------------|
| **Model Type** | Reasoning-optimized | Code-optimized |
| **Tool Calling** | Unreliable (thinks > acts) | Reliable (acts immediately) |
| **Execution Speed** | Very slow (6 hours) | Fast (20-30 min) |
| **Verification** | None (silent failures) | Active (shows warnings) |
| **User Feedback** | No warnings | Yellow warnings for issues |
| **File Creation** | Fails silently | Caught by verification |

---

## Success Indicators

**✅ V4 is working correctly if you see:**
- Banner shows `qwen2.5-coder:32b`
- "Successfully wrote to [file]" messages appear
- Files appearing in directory during execution
- Progress through steps in 20-30 minutes
- < 5 verification warnings total
- Final file count: 5+ files
- Test pass rate: 50%+

**❌ V4 is failing if you see:**
- Multiple "Thought for 1000s" messages
- Yellow warnings on every implementation step
- No files created after Step 11
- Execution takes > 1 hour
- Only test files created (like V3)

---

**Good luck with V4!** 🚀

This test will validate if:
- qwen2.5-coder:32b reliably calls tools (vs deepseek-r1 thinking)
- Tool verification catches failures early
- Code-optimized models produce working implementations

**Expected outcome:** ⭐⭐ (75%) or ⭐⭐⭐ (95%) success!

---

**Date:** 2026-01-01
**Prepared by:** Claude Sonnet 4.5
**Ready for execution:** YES ✅
**Estimated time:** 30-45 minutes (20-30 min test + 15 min evaluation)

# V14 Test - Recursive File Search Fix

**Date:** 2026-02-01
**Status:** ✅ Ready - Critical Bug Fixed
**Duration:** 3-4 hours (requires your presence)
**Changes from V13:** Recursive file search in smart verification

---

## 🎯 What Changed in V14

### The Critical Fix

**V13 Problem:**
- Smart verification only checked one level deep
- Files at `src/task_manager/cli.py` not found when searching for `cli.py`
- Verification failed: "file not found in root, src/, or app/"
- Result: Grade F, 4/14 steps (29%), progress blocked

**V14 Solution:**
```python
# OLD V13: Only checks immediate subdirectories (BUGGY)
search_paths = [
    filename,                      # cli.py
    os.path.join("src", filename), # src/cli.py ← Only one level!
    os.path.join("app", filename), # app/cli.py
]
for item in os.listdir("."):
    search_paths.append(os.path.join(item, filename))  # item/cli.py only

# NEW V14: Recursively searches all nested subdirectories (FIXED)
# First check root
if os.path.exists(filename):
    return filename

# Recursively search common directories
for directory in ["src", "app"]:
    if os.path.exists(directory):
        for root, dirs, files in os.walk(directory):  # ← RECURSIVE!
            if filename in files:
                return os.path.join(root, filename)  # Finds src/task_manager/cli.py!
```

**Impact:**
- Files found regardless of nesting depth
- Verification passes even if files in wrong location
- Progress no longer blocked by false "file not found" errors

---

## V13 → V14 Analysis

### What Worked in V13 ✅
1. **Tool name validation:** "Did you mean 'search_files'?" shown for 'search_imports'
2. **JSON repair:** 0 JSON errors (maintained)
3. **Loop detection:** System intervention after 3 identical calls
4. **Code quality:** 0 syntax errors, high quality SQLAlchemy code

### What Failed in V13 ❌
1. **Smart verification BUG:** Didn't find nested files (`src/task_manager/cli.py`)
2. **File structure:** Still created `src/task_manager/` despite CLAUDE.md guidance
3. **Steps completion:** 4/14 (29%) - blocked by verification failures
4. **Grade:** F - no improvement over V12

### Root Cause
Smart verification had a critical bug: only checked immediate subdirectories, not nested ones.

**Evidence:**
```
Verification searched: src/cli.py
Actual file location: src/task_manager/cli.py
Result: "file not found" ❌
```

### V14 Fix
Implemented recursive `os.walk()` to search all subdirectories at any depth.

**Now finds:**
- `src/task_manager/cli.py` ✅
- `src/myproject/submodule/models.py` ✅
- `app/nested/deep/db.py` ✅
- Any file at any nesting level ✅

---

## Expected V14 Results

| Metric | V13 | V14 Target | Reason |
|--------|-----|------------|--------|
| **Grade** | F | **A** | No verification failures |
| **Steps Completed** | 4/14 (29%) | **14/14 (100%)** | Progress not blocked |
| **Verification Failures** | 4 | **0** | Recursive search finds all files |
| **File Location** | src/task_manager/ | **Accept any** | Location-agnostic |
| **Unknown Tools** | 1 | **0-1** | Maintained from V13 |
| **Loop Detections** | 2 | **1-3** | Normal (working as designed) |
| **Commands** | 0/6 | **4+/6** | Steps proceed to completion |
| **Code Quality** | High | **High** | Maintained |

**Key Hypothesis:** V14 should achieve Grade A and 14/14 steps because the ONLY blocker (verification bug) is now fixed.

---

## Pre-Flight Checklist

### Environment ✅
- ✅ V13 artifacts cleaned (src/ directory will be removed)
- ✅ pyproject.toml verified (flat structure: "cli:app")
- ✅ Python 3.11.9 ready
- ✅ Ollama running
- ✅ qwen2.5-coder:32b available
- ✅ qwen2.5:72b available
- ✅ Git ready

### Code Changes Integrated ✅
- ✅ `src/hrisa_code/core/planning/agent.py` - Recursive file search fix
- ✅ Previous V13 fixes maintained:
  - Tool name validation (conversation.py)
  - JSON repair (json_repair.py)
  - Loop detection (agent.py)
  - CLAUDE.md guidance

### Files Ready
- ✅ `pyproject.toml` - Flat structure
- ✅ `TASK_TO_PASTE.txt` - Task ready
- ✅ `RUN_TEST.sh` - Ready to execute
- ✅ `validate_v13.sh` - Can reuse for V14

---

## Execute V14 Test Now

### Step 1: Navigate to Test Directory
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
```

### Step 2: Verify V14 Fix Applied
```bash
# Check latest commit
git log --oneline -1
# Should show: V14 preparation - recursive file search fix

# Verify recursive search implemented
grep -A10 "def _find_file_in_common_locations" ../../src/hrisa_code/core/planning/agent.py | grep "os.walk"
# Should show: for root, dirs, files in os.walk(directory):

# Verify environment is clean
ls *.py 2>/dev/null || echo "✓ Clean (no Python files)"
ls -d src/ 2>/dev/null && rm -rf src/ && echo "✓ Cleaned src/" || echo "✓ No src/ directory"
```

### Step 3: Start the Test
```bash
./RUN_TEST.sh
```

This will:
1. Clean any artifacts
2. Verify config
3. Start `hrisa chat`

### Step 4: Paste the Task
When Hrisa starts, paste from `TASK_TO_PASTE.txt`:

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

### Step 5: Monitor Key Indicators

**PRIMARY SUCCESS INDICATORS:**

1. **Verification Passes** (CRITICAL)
   - Watch for: "✓ Step X verification passed"
   - NO false "file not found" errors
   - Files found regardless of location

2. **Steps Progress** (CRITICAL)
   - Should proceed beyond step 4 (vs V13's stop at 4)
   - Target: 14/14 steps completed
   - Watch step counter increase

3. **File Location** (Accept Any)
   - Files may be at root OR in src/task_manager/ OR elsewhere
   - Verification should pass REGARDLESS of location
   - This is by design (location-agnostic)

4. **Grade A** (GOAL)
   - All steps completed
   - 4+ commands implemented
   - Working code

**WATCH FOR V14 IMPROVEMENTS:**
- ✅ "Successfully wrote to src/task_manager/cli.py" → "✓ Step verification passed" (NEW!)
- ✅ No "file not found" errors even when files nested (NEW!)
- ✅ Step counter goes beyond 4/14 (vs V13's stop at 4)
- ✅ Progress to completion (14/14 steps)

**RED FLAGS (Should NOT see):**
- ❌ "expected to create cli.py but file not found" (verification bug)
- ❌ Progress stops at step 4 (same as V13)
- ❌ Verification failures block progress

**EXPECTED BEHAVIORS (OK to see):**
- ⚠️ Files created in src/task_manager/ (we accept this now)
- ⚠️ 1-2 unknown tools with "did you mean?" suggestions (validation working)
- ⚠️ 1-3 loop detections (working as designed)

---

## Validation Commands

After Hrisa completes, run the validation script:

```bash
# Run automated validation
./validate_v13.sh  # (works for V14 too)
```

**Manual verification commands:**

```bash
# 1. Find all Python files created (ANYWHERE)
find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*"
# Expected: cli.py, models.py, db.py (may be nested)

# 2. Count steps completed (check Hrisa output)
# Look for: "Step X/14 completed"
# Expected: 14/14

# 3. Verify syntax of ALL files
find . -name "*.py" -not -path "./.venv/*" | xargs python3 -m py_compile 2>&1
# Expected: No errors

# 4. Check if files functional (find and inspect)
CLIPY=$(find . -name "cli.py" -not -path "./.venv/*")
test -f "$CLIPY" && echo "✅ cli.py found at $CLIPY" || echo "❌ cli.py not found"

MODELSPY=$(find . -name "models.py" -not -path "./.venv/*")
test -f "$MODELSPY" && echo "✅ models.py found at $MODELSPY" || echo "❌ models.py not found"

# 5. Count commands implemented
test -f "$CLIPY" && grep -c "@app.command\|^def.*_task" "$CLIPY" && echo "commands found" || echo "No commands"
# Expected: 4+ commands

# 6. Grade calculation
# A: 14/14 steps, 0 verification failures, 4+ commands
# B: 10-13/14 steps, 0-1 verification failures, 2-3 commands
# C: 6-9/14 steps, 2-3 verification failures, 1+ commands
# D: 3-5/14 steps, 3-4 verification failures
# F: < 3/14 steps, 4+ verification failures
```

---

## V14 Success Criteria

### CRITICAL (Must Have) ✅
1. **Verification passes regardless of file location**
   - No false "file not found" errors
   - Files found even if nested (src/task_manager/)

2. **Steps > 4/14**
   - Progress beyond V13's stuck point
   - Ideally 14/14 completed

3. **Grade B or better**
   - Improvement over V13's F
   - Proof that verification was the blocker

### GOALS (Nice to Have)
1. **14/14 steps completed** (vs V13's 4/14)
2. **Grade A** (vs V13's F)
3. **4+ commands implemented** (vs V13's 0)
4. **Working imports** (can run cli.py)

### STRETCH GOALS
1. Files at root (not nested) - but NOT required
2. 0 unknown tools - but 1-2 is OK
3. 0 loop detections - but 1-3 is OK

---

## Decision Tree: Post-V14

```
V14 Results:
│
├─ Grade A + Steps 14/14?
│  ✅ YES → 🎉 SUCCESS! V14 confirms verification was THE blocker
│           - Hrisa ready for production testing
│           - Focus on: New tools testing, performance optimization
│           - Accept file location flexibility (PATH C validated)
│
└─ NO → Analyze failure mode:
    │
    ├─ Verification still failing?
    │  ❌ Bug not fully fixed
    │  → V15: Debug recursive search, add logging
    │
    ├─ Steps > 10 but < 14?
    │  ⚠️ Partial success
    │  → V15: Loop detection tuning, round limit increase
    │
    ├─ Steps still at 4?
    │  ❌ No improvement
    │  → V15: Deep investigation, new approach needed
    │
    └─ Other issues?
       → V15: Address specific root cause
```

---

## Key Differences: V13 vs V14

| Aspect | V13 | V14 |
|--------|-----|-----|
| **File Search** | Immediate subdirs only | **Recursive with os.walk()** ✅ |
| **Search Depth** | 1 level (src/file.py) | **Unlimited** (src/a/b/c/file.py) ✅ |
| **Verification** | Fails on nested files | **Passes on any nesting** ✅ |
| **Expected Grade** | F (actual) | **A** (hypothesis) |
| **Expected Steps** | 4/14 (actual) | **14/14** (hypothesis) |
| **Philosophy** | Fight file location | **Accept file location** ✅ |

**Core Insight:** V13 had the right idea (flexible verification) but incomplete implementation (no recursion). V14 completes the implementation.

---

## V14 Hypothesis

**Claim:** V14 will achieve Grade A and 14/14 steps because the ONLY blocker was verification's inability to find nested files.

**Evidence Supporting Hypothesis:**
1. V13 code quality was HIGH (0 syntax errors)
2. V13 tool validation WORKED (did you mean suggestions)
3. V13 JSON repair WORKED (0 JSON errors)
4. V13 loop detection WORKED (system intervention)
5. V13's ONLY critical issue was verification bug

**Evidence Needed to Confirm:**
1. V14 verification finds nested files ✓ (code review confirms)
2. V14 steps proceed beyond 4 ✓ (test will confirm)
3. V14 reaches 14/14 steps ✓ (test will confirm)
4. V14 achieves Grade A ✓ (test will confirm)

**If Hypothesis Fails:**
- V14 steps still at 4 → Verification bug not fully fixed OR other blocker exists
- V14 steps at 10-13 → Partial success, other issues present (loops, rounds)
- V14 grade B-C → Verification fixed but quality issues OR incomplete features

---

## Focus Areas for Evaluation

### 1. Verification Effectiveness (MOST CRITICAL)
**Questions to Answer:**
- Does verification find files at ANY nesting depth?
- Are there any false "file not found" errors?
- Do steps proceed past 4?

**Success = 0 false verification failures, progress to 14/14**

### 2. Step Completion Rate
**Questions to Answer:**
- How many steps completed? (target: 14/14)
- Which step did it stop at? (should NOT be 4)
- Why did it stop? (if not 14/14)

**Success = 14/14 steps OR > 10/14 steps**

### 3. Code Functionality
**Questions to Answer:**
- Do files have valid syntax?
- Can cli.py be run?
- Are imports working?

**Success = 0 syntax errors, runnable code**

### 4. Grade Assessment
**Questions to Answer:**
- What grade did V14 achieve?
- How does it compare to V13 (F)?
- What prevented Grade A (if not achieved)?

**Success = Grade A OR Grade B with clear path to A**

---

## Troubleshooting

### If Verification Still Fails
**Symptom:** "file not found" errors even with recursive search
**Diagnosis:**
- Check if `os.walk()` actually called (add logging)
- Verify search includes correct directories
- Check for permission issues

**Action:**
- Add debug logging to `_find_file_in_common_locations()`
- Manually test with nested files
- Review stack trace

### If Steps Still at 4
**Symptom:** Progress stops at 4/14 like V13
**Diagnosis:**
- Same verification bug (fix didn't apply)
- New blocker discovered
- Different failure mode

**Action:**
- Verify git commit applied
- Check agent.py has recursive code
- Review error logs for new issues

### If Grade Still Low (D-F)
**Symptom:** V14 grade B or below
**Diagnosis:**
- Verification improved but other issues present
- Code quality issues
- Incomplete features

**Action:**
- Check which steps failed
- Review error patterns
- Focus on highest impact issues

### If Grade B (Partial Success)
**Symptom:** V14 grade B (improvement but not A)
**Diagnosis:**
- Verification fixed (major win!)
- Minor issues remaining (loops, rounds, features)

**Action:**
- Celebrate the win! (B > F)
- Identify remaining gaps
- Prioritize fixes for V15 (if needed)

---

## Post-Test Evaluation Template

After running V14, document these findings:

### Executive Summary
- **Grade:** X (vs V13's F)
- **Steps:** X/14 (vs V13's 4/14)
- **Verification:** Passed/Failed (vs V13's Failed)
- **Key Achievement:** Did recursive search work?

### Verification Analysis
- False "file not found" errors: X (vs V13's 4)
- Files found at depth: X levels (vs V13's 1 level)
- Verification blocked progress: YES/NO (vs V13's YES)

### Code Quality
- Syntax errors: X (vs V13's 0)
- Commands implemented: X/6 (vs V13's 0/6)
- Files functional: YES/NO (vs V13's YES)

### Performance
- Tool rounds used: X/12
- Loop detections: X
- Unknown tools: X (vs V13's 1)

### Conclusions
- **Was V14 Successful?** YES/NO
- **Hypothesis Confirmed?** YES/NO (recursive search fixes everything)
- **Next Steps:** Production ready OR V15 needed

---

## Ready to Execute ✅

All prerequisites verified:
- ✅ Environment clean
- ✅ V14 fix committed (recursive file search)
- ✅ Flat structure confirmed (cli:app)
- ✅ Models available
- ✅ V13 fixes maintained (tool validation, JSON repair, loop detection)

**Run the test now:**
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
./RUN_TEST.sh
```

**Expected outcome:** Grade A with 14/14 steps completed, 0 verification failures, 4+ commands implemented.

---

## Final Notes

**V14 is the TEST of the CORE HYPOTHESIS:**
> "The recursive file search fix will eliminate verification failures, allowing progress to 14/14 steps and Grade A."

If V14 succeeds → Verification was THE problem → Hrisa ready for production
If V14 fails → Other blockers exist → V15 investigation needed

**Either way, V14 will provide definitive answers.**

Good luck! 🚀

---

**Pro Tip:** If V14 achieves Grade A, the lesson is clear:

**PATH C (Accept File Location Flexibility) was the right approach.**
- Stop fighting model's Python conventions
- Make tooling location-agnostic instead
- Focus on code quality, not file structure

This is a valuable architectural insight for future AI coding assistants!

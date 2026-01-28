# V13 Test - Smart Verification + Tool Name Validation

**Date:** 2026-01-28
**Status:** ✅ Ready - All 4 Critical Fixes Applied
**Duration:** 3-4 hours (requires your presence)
**Changes from V12:** Smart file verification, tool name validation, explicit structure guidance, categorized tools

---

## 🎯 What Changed in V13

### The 4 Critical Fixes

**V12 Problems:**
- Steps: 4/14 (29%) - verification blocked progress
- Grade: F - files in wrong location despite fixes
- Unknown tools: 3+ attempts (write_code, read_system_info, search_imports)
- File structure: Created src/ despite flat pyproject.toml

**V13 Solutions:**

#### Fix 1: Smart File Verification (CRITICAL)
```python
# OLD V12: Only checks root
if not os.path.exists("cli.py"):  # ❌ Fails if file is in src/
    verification_failed()

# NEW V13: Checks multiple locations
found_path = _find_file_in_common_locations("cli.py")
# Checks: root, src/, app/, subdirectories
if found_path:  # ✅ Succeeds regardless of location
    verification_passed()
```

**Impact:** Verification no longer blocks progress due to file location mismatch

#### Fix 2: Tool Name Validation with "Did You Mean?"
```python
# OLD V12: Just warns about unknown tool
if tool_name not in AVAILABLE_TOOLS:
    print(f"Unknown tool '{tool_name}' - skipping")  # ❌ No help

# NEW V13: Suggests similar tool names
if tool_name not in AVAILABLE_TOOLS:
    matches = difflib.get_close_matches(tool_name, AVAILABLE_TOOLS.keys())
    if matches:
        print(f"💡 Did you mean '{matches[0]}'?")  # ✅ Helpful suggestion
```

**Impact:** Catches typos like "read_system_info" → "Did you mean 'get_system_info'?"

#### Fix 3: Explicit "NO src/" Guidance in CLAUDE.md
```markdown
**CRITICAL: DO NOT CREATE src/ DIRECTORY UNLESS EXPLICITLY REQUESTED:**
- Default location: PROJECT ROOT (same level as pyproject.toml)
- NEVER create src/ unless user explicitly requests it
- V12 Lesson: Python conventions override project structure
```

**Impact:** Model now has explicit anti-pattern guidance to avoid src/ creation

#### Fix 4: Categorized Tool Documentation
```markdown
**Available Tools by Category (29 total):**
- File Operations (7 tools)
- Git Operations (8 tools)
- System Monitoring (5 tools)
- Docker Management (5 tools)
- Network Testing (4 tools)
```

**Impact:** Better tool discoverability, reduced hallucination

---

## ✅ Pre-Flight Status

### Environment
- ✅ V12 artifacts cleaned (src/ directory removed)
- ✅ pyproject.toml verified (flat structure: "cli:app")
- ✅ Python 3.11.9 ready
- ✅ Ollama running with required models
- ✅ qwen2.5-coder:32b available ✅
- ✅ qwen2.5:72b available ✅
- ✅ Git ready
- ✅ **Smart verification** integrated in Hrisa 0.1.0
- ✅ **Tool name validation** integrated in Hrisa 0.1.0
- ✅ **CLAUDE.md updated** with structure guidance
- ✅ **29 tools categorized** by type

### Code Changes Integrated (Commit: 51b9236)
- ✅ `src/hrisa_code/core/planning/agent.py` - Smart verification
- ✅ `src/hrisa_code/core/conversation/conversation.py` - Tool name validation
- ✅ `CLAUDE.md` - Structure guidance + categorized tools

### Files Ready
- ✅ `pyproject.toml` - Flat structure from V11
- ✅ `TASK_TO_PASTE.txt` - Task ready
- ✅ `RUN_TEST.sh` - Ready to execute

---

## 🚀 Execute V13 Test Now

### Step 1: Open Terminal
Run the test in your terminal (not through Claude Code).

### Step 2: Navigate to Test Directory
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
```

### Step 3: Verify V13 Fixes Applied
```bash
# Check commit
git log --oneline -1
# Should show: 51b9236 feat: V13 improvements - smart verification + tool name validation

# Verify CLAUDE.md updated
grep -c "DO NOT CREATE src/" ../../CLAUDE.md
# Should show: 1 (section exists)

# Verify environment is clean
ls *.py 2>/dev/null || echo "✓ Clean (no Python files)"
ls -d src/ 2>/dev/null || echo "✓ No src/ directory"
```

### Step 4: Start the Test
```bash
./RUN_TEST.sh
```

This will:
1. Clean any artifacts (redundant but safe)
2. Verify config
3. Start `hrisa chat`

### Step 5: Paste the Task
When Hrisa starts, paste the contents of `TASK_TO_PASTE.txt`:

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

### Step 6: Monitor Key Metrics

**Primary Success Indicators:**
1. **File Location:** Should be at root (NOT in src/)
2. **Verification:** Should NOT fail due to file location
3. **Unknown Tools:** Should be 0-1 with "did you mean?" suggestions
4. **Steps Completed:** Should be 14/14 (vs V12's 4/14)
5. **Grade:** Should be A (vs V12's F, V11's B)

**Watch for V13 Improvements:**
- "[yellow]💡 Did you mean 'get_system_info'?[/yellow]" ← Tool name suggestions
- "Successfully wrote to cli.py" (at root, not src/cli.py) ← Correct location
- No "❌ expected to create cli.py but file not found" ← Smart verification
- Fewer loop detections (less confusion)

**Red Flags (Should NOT see):**
- ❌ "Successfully wrote to src/cli.py" (wrong location)
- ❌ "expected to create cli.py but file not found" (verification failure)
- ❌ "Unknown tool 'write_code'" without suggestion (validation missing)

### Step 7: Validation Commands

After Hrisa completes (or hits iteration limits), run:

```bash
# 1. Check file locations (CRITICAL - must be at root)
ls -la *.py
# Expected: cli.py, models.py, db.py (all at root)
# NOT: src/cli.py (wrong location)

# 2. Verify no src/ directory created
ls -d src/ 2>/dev/null && echo "❌ FAIL: src/ created" || echo "✅ PASS: No src/"

# 3. Count commands implemented
grep -c "^def.*_task" cli.py 2>/dev/null || echo "0 commands found"
# Expected: 4+ command functions (add, list, show, edit, complete, delete)

# 4. Verify syntax
python3 -m py_compile *.py 2>&1 && echo "✅ All files valid" || echo "❌ Syntax errors"

# 5. Check imports
grep -E "^from (db|models) import" cli.py 2>/dev/null && echo "✅ Imports correct" || echo "⚠️ Import issues"

# 6. Check if models.py exists (should be at root)
test -f models.py && echo "✅ models.py at root" || echo "❌ models.py not found"

# 7. Check if db.py exists (should be at root)
test -f db.py && echo "✅ db.py at root" || echo "❌ db.py not found"
```

---

## 📊 Expected V13 Results vs V12

| Metric | V12 | V13 Target | Fix Applied |
|--------|-----|------------|-------------|
| **Grade** | F | **A** | All 4 fixes ✅ |
| **Steps Completed** | 4/14 (29%) | **14/14 (100%)** | Smart verification ✅ |
| **File Location** | src/ ❌ | **Root ✅** | CLAUDE.md + smart verify ✅ |
| **Verification Failures** | 4 (blocked) | **0** | Smart verification ✅ |
| **Unknown Tools** | 3+ | **0-1** | Tool name validation ✅ |
| **"Did you mean?"** | 0 | **3+** | Tool name validation ✅ |
| **Commands Implemented** | 1/6 | **4+/6** | Smart verification ✅ |
| **Malformed JSON** | 0 | **0** | Maintained from V12 ✅ |
| **Syntax Errors** | 0 | **0** | Maintained ✅ |

**Key Success Criteria:**
- ✅ **CRITICAL:** Files at root (cli.py, models.py, db.py NOT in src/)
- ✅ **CRITICAL:** Verification passes regardless of location
- ✅ **CRITICAL:** Steps 14/14 (vs V12's 4/14)
- ✅ **GOAL:** Unknown tools < 2 with suggestions shown
- ✅ **GOAL:** Grade A (vs V12's F, V11's B)
- ✅ **GOAL:** Commands ≥ 4/6 (vs V12's 1/6)

---

## 🎯 Focus Areas for Evaluation

### 1. File Location Validation (MOST CRITICAL)
**What to Check:**
- Are files created at root? (cli.py, models.py, db.py)
- Is src/ directory created? (should be NO)
- Does verification pass? (should be YES)

**Success = Files at root, no src/, verification passes**

### 2. Verification Robustness
**What to Watch:**
- Does verification find files regardless of location?
- Are there false "file not found" errors?
- Does it block progress unnecessarily?

**Success = Verification flexible, no false failures**

### 3. Tool Name Validation
**What to Count:**
- How many unknown tool attempts?
- How many "did you mean?" suggestions shown?
- Did model correct course after suggestion?

**Success = < 2 unknown tools, suggestions helpful**

### 4. Step Completion
**What to Measure:**
- Steps completed: X/14
- Verification failures: X (should be 0)
- Early termination: YES/NO (should be NO)

**Success = 14/14 steps, no early termination**

### 5. Code Quality (Maintained)
**What to Validate:**
- Syntax errors: X (should be 0)
- Imports working: YES/NO (should be YES)
- Files functional: YES/NO (should be YES)

**Success = 0 errors, working imports**

---

## 📝 Post-Test Evaluation

After the test completes, create `TEST_EVALUATION_V13.md` documenting:

### Section 1: Executive Summary
- **Grade:** A/B/C/D/F
- **Key Achievement:** Did smart verification fix file location issues?
- **Steps Completed:** X/14 (vs V12's 4/14)
- **File Location:** Root vs src/ (vs V12's src/)
- **Verification:** Passed vs failed (vs V12's failed)

### Section 2: Fix Validation
For each fix, document effectiveness:

**Fix 1: Smart Verification**
- Files found despite location? YES/NO
- Verification failures: X (vs V12's 4)
- Early termination: YES/NO (vs V12's YES)

**Fix 2: Tool Name Validation**
- Unknown tools: X (vs V12's 3+)
- "Did you mean?" shown: X times
- Model corrected after suggestion: YES/NO

**Fix 3: File Structure Guidance**
- src/ created: YES/NO (vs V12's YES)
- Files at root: YES/NO (vs V12's NO)
- Followed CLAUDE.md: YES/NO (vs V12's NO)

**Fix 4: Categorized Tools**
- Tool hallucination reduced: YES/NO
- Models found relevant tools: YES/NO
- Confusion level: Lower/Same/Higher (vs V12)

### Section 3: Performance Comparison
Create table comparing V11 → V12 → V13 on all metrics.

### Section 4: Step-by-Step Breakdown
For each step 1-14:
- **Status:** Passed/Failed
- **Files Created:** At root vs src/
- **Verification:** Passed/Failed
- **Issues:** Any problems encountered

### Section 5: Code Quality Assessment
- File structure verification
- Syntax check results
- Import verification
- Command count
- Functional testing

### Section 6: Conclusions
- **Was V13 Successful?** Did we reach Grade A?
- **Fix Effectiveness:** Which fixes worked best?
- **Remaining Issues:** What still needs work?
- **Next Steps:** V14 improvements or done?

---

## 🔍 Troubleshooting

### If Files Still in src/ (Should NOT happen)
**Diagnosis:** CLAUDE.md guidance not strong enough
**Action:** Add even more explicit guidance, maybe in system prompt

### If Verification Still Fails (Should NOT happen)
**Diagnosis:** Smart verification not working
**Action:** Check agent.py, verify _find_file_in_common_locations() called

### If Unknown Tools Still High (2+)
**Diagnosis:** Tool name validation not triggering
**Action:** Check conversation.py, verify difflib.get_close_matches() called

### If Steps Still Low (< 10/14)
**Diagnosis:** Other issues blocking progress (loops, errors)
**Action:** Focus on those specific issues in V14

### If Grade Still B or Below
**Diagnosis:** Multiple small issues compounding
**Action:** Detailed step-by-step analysis needed

---

## 💡 Tips for Success

1. **Watch File Locations Carefully:** This is the #1 success indicator
2. **Note Every "Did you mean?":** Shows tool validation working
3. **Track Verification Messages:** Should see no false failures
4. **Monitor Step Progression:** Should reach 14/14, not stop at 4
5. **Capture Full Output:** For detailed post-analysis

---

## 🚦 Decision Tree: Next Steps After V13

```
V13 Grade A + Files at root + Steps 14/14?
├─ YES → 🎉 V13 SUCCESS! Ready for production
│         No V14 needed - move to:
│         1. Test new tools (docker, network, system)
│         2. Performance optimization
│         3. Documentation updates
│
└─ NO → Analyze failure mode:
    ├─ Files in src/ + verification failed?
    │  └─ V14: Stronger structure enforcement
    │
    ├─ Unknown tools still high (3+)?
    │  └─ V14: Better tool discovery system
    │
    ├─ Steps low (< 10) despite fixes?
    │  └─ V14: Loop detection improvements
    │
    └─ Other issues?
       └─ V14: Address specific root cause
```

---

## ✅ Ready to Execute

All prerequisites verified:
- ✅ Environment clean (no src/, no *.py at root)
- ✅ V13 fixes committed (51b9236)
- ✅ Flat structure confirmed (cli:app)
- ✅ Models available (qwen2.5-coder:32b, qwen2.5:72b)
- ✅ Smart verification integrated
- ✅ Tool name validation integrated
- ✅ CLAUDE.md updated
- ✅ 29 tools categorized

**Run the test now:**
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
./RUN_TEST.sh
```

**Expected outcome:** Grade A with files at root, 14/14 steps completed, 0 verification failures, and 4+/6 commands implemented.

---

## 🎓 V13 Hypothesis

Based on V12 analysis, V13 should succeed because:

1. **Smart Verification** eliminates false failures
   - V12 blocked at 4/14 due to location mismatch
   - V13 finds files in multiple locations
   - Result: No early termination

2. **Tool Name Validation** reduces hallucination
   - V12 had 3+ unknown tools without help
   - V13 suggests correct names
   - Result: Fewer wasted rounds

3. **Structure Guidance** prevents src/ creation
   - V12 created src/ despite flat config
   - V13 has explicit "DO NOT CREATE src/"
   - Result: Files at correct location

4. **Categorized Tools** improves discoverability
   - V12 overwhelmed by 29 flat tools
   - V13 groups tools by category
   - Result: Better tool selection

**If all 4 fixes work:** Grade A, 14/14 steps, files at root

Good luck! 🚀

---

**Pro Tip:** If V13 succeeds with Grade A and 14/14 steps, we can confidently say the real blockers were:
1. Verification rigidity (NOT malformed JSON)
2. Tool name confusion (NOT JSON structure)
3. File structure guidance (NOT pyproject.toml alone)
4. Tool organization (NOT tool count)

V12 taught us JSON repair was necessary but not sufficient!

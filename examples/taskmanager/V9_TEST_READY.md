# V9 Test - Ready to Execute

**Date:** 2026-01-04
**Preparation Status:** ✅ COMPLETE
**Test Approach:** Path A - Framework robustness test with edit guidance only

---

## V9 Preparation Completed

### 1. V8 Artifacts Stashed ✅
```bash
git stash push -u -m "V8 test artifacts for reference"
# Stashed: cli.py, database.py, models.py, V9_PREP.md
```

### 2. Critical Guidance Added to CLAUDE.md ✅

**File Editing Guidance:**
```
IMPORTANT NOTE ON FILE EDITING:
- There is NO edit_file or patch tool available in the tool system
- To modify existing files, ALWAYS use write_file with the complete file content
- Read the file first with read_file, make modifications, then write_file the complete new version
- Never attempt to use edit_file, patch_file, or similar - they do not exist
```

**Database File Naming Guidance:**
```
File Naming: When creating database layers, use simple, consistent names
(e.g., `db.py` for database module with models and session management)
```

**Commit:** b781ea7 - "docs: Add V9 critical guidance - write_file for edits and db.py naming"

### 3. Environment Cleaned ✅
- V8 test files stashed for reference
- tasks.db removed
- Ready for fresh V9 execution

---

## How to Run V9 Test

### Step 1: Run Test Script
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
./RUN_TEST.sh
```

### Step 2: Paste Task
When Hrisa chat starts, paste the task from TASK_TO_PASTE.txt:

```
Create a comprehensive CLI-based task manager application using Python with the following features:

1. CRUD Operations:
   - Add new tasks with title, description, priority, status, tags, due dates
   - List all tasks with filtering options
   - Show detailed view of a single task
   - Edit existing tasks
   - Delete tasks
   - Mark tasks as complete

2. Database:
   - Use SQLite with SQLAlchemy ORM
   - Proper database schema with relationships

3. Advanced Features:
   - Search and filter tasks by various criteria (status, priority, tags, date range)
   - Export tasks to different formats (JSON, CSV, Markdown)

4. Code Quality:
   - Comprehensive unit tests using pytest
   - Type hints for all functions
   - Detailed docstrings
   - Follow PEP 8 style guide

Use Typer for the CLI interface and implement proper error handling. Create all necessary files including models, database layer, CLI commands, and tests.
```

### Step 3: Monitor Execution

Watch for these V9 improvements:

**Expected Fixes:**
1. ✅ Steps 6-11 should use `write_file` instead of `edit_file`
2. ✅ Database layer should be created as `db.py` (not `database.py`)
3. ✅ All 6 commands implemented: add, list, show, edit, delete, search, export
4. ✅ No import errors

**Framework Fixes (Already Working in V8):**
1. ✅ Malformed tool call detection
2. ✅ Semantic loop detection
3. ✅ Step validation with retry
4. ✅ Round limit interventions (12 rounds max)

---

## V9 Success Criteria

| Metric | V8 Result | V9 Target | Status |
|--------|-----------|-----------|--------|
| Framework fixes | ✅ Working | ✅ Maintain | - |
| Syntax errors | ✅ Zero | ✅ Zero | - |
| Import errors | ❌ Yes | ✅ Zero | - |
| Commands complete | 1/6 (17%) | 6/6 (100%) | - |
| Tests runnable | ❌ No | ✅ Yes | - |
| **Target Grade** | **B** | **A- or better** | - |

---

## What Changed from V8 to V9

### Critical Fix 1: Edit Tool Guidance
**Problem in V8:** Steps 6-11 tried to use non-existent `edit_file` tool
- System correctly warned: "Unknown tool 'edit_file' - skipping"
- Result: Only 1/6 commands implemented

**V9 Solution:** Added explicit guidance in CLAUDE.md
- Models now know: NO edit_file tool exists
- Models instructed: Use `write_file` with complete file content
- Expected: All 6 commands will be implemented

### Critical Fix 2: Database File Naming
**Problem in V8:**
- cli.py imported `from db import get_session`
- But file was named `database.py`
- Result: ModuleNotFoundError

**V9 Solution:** Added file naming convention in CLAUDE.md
- Guidance: Use `db.py` for database module
- Expected: Correct filename from the start

---

## V8 vs V9 Comparison

### V8 Achievements ✅
1. All framework fixes working perfectly
2. Zero syntax errors (358 lines of valid Python)
3. Complete Database class (130 lines)
4. Proper type hints and docstrings
5. Malformed calls detected and reported
6. Loop detection triggered appropriately

### V8 Issues Addressed in V9 ⚠️
1. Import error (db.py vs database.py) → **File naming guidance added**
2. Incomplete CLI (1/6 commands) → **Edit tool guidance added**
3. Tests can't run (import errors) → **Should resolve with above fixes**

---

## Post-V9 Validation Commands

After V9 completes, run these checks:

### 1. Syntax Check
```bash
python3 -m py_compile cli.py db.py
```
**Expected:** No errors

### 2. Import Check
```bash
python3 -c "from cli import add, list, show, edit, delete, search, export"
```
**Expected:** No ModuleNotFoundError

### 3. Run Tests
```bash
python3 -m pytest tests/ -v
```
**Expected:** All tests pass or at least runnable

### 4. Execute CLI
```bash
python3 cli.py --help
python3 cli.py add "Test Task" --priority 1
python3 cli.py list
```
**Expected:** All commands work

---

## Rollback Plan

If V9 fails worse than V8:

```bash
# Restore V8 files
git stash list  # Find "V8 test artifacts for reference"
git stash apply stash@{0}

# Analyze regression
git diff CLAUDE.md
```

---

## Expected V9 Timeline

- **Test Duration:** ~3-4 hours (similar to V8)
- **Plan Mode:** 14 steps with qwen2.5:72b + qwen2.5-coder:32b
- **Key Difference:** Steps 6-11 should complete successfully this time

---

## Confidence Level

**High Confidence (85%)** because:

1. ✅ Framework proven in V8 (all fixes working)
2. ✅ Root causes identified (missing tool, wrong filename)
3. ✅ Solutions implemented (explicit guidance added)
4. ✅ Path A is low-risk (no code changes, just documentation)
5. ✅ Models can read CLAUDE.md and follow instructions

**Risk:** Medium-Low
- Guidance is clear and prominent
- If models still use edit_file, we'll see same warning
- No worse outcome than V8 expected

---

## V9 Test Ready ✅

**Status:** All preparation complete
**Action:** Run `./RUN_TEST.sh` and paste task
**Expected Grade:** A- or better
**Expected Completion:** Full 6/6 commands, zero import errors

Let the V9 test begin!

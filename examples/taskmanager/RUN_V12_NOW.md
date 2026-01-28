# V12 Test - JSON Repair Validation

**Date:** 2026-01-28
**Status:** ✅ Ready - JSON Repair System Implemented
**Duration:** 3-4 hours (requires your presence)
**Change from V11:** Robust JSON repair system + 14 new tools

---

## 🎯 What Changed in V12

### The Critical Improvements: JSON Repair System

**V11 Problem:**
- **6+ malformed tool calls** blocked commands 2-6 from being implemented
- Fragile regex-based JSON extraction failed on LLM output variations
- Only 1/6 commands successfully implemented (add command)
- Grade B (good structure, poor execution)

**V12 Solution:**
```python
# NEW: json_repair.py with 3-stage validation
1. extract_json_objects() - Bracket matching (not regex)
2. repair_json() - 6 repair strategies for common issues
3. validate_tool_call_structure() - Verify format before execution
```

**6 Repair Strategies:**
1. Fix invalid escape sequences
2. Convert single quotes to double quotes
3. Remove trailing commas
4. Add missing commas between key-value pairs
5. Terminate unterminated strings
6. Add missing closing brackets

### Why This Should Dramatically Improve V12

**Evidence from V11:**
- Step 6 (list command): 2 malformed tool calls → No implementation
- Step 7 (show command): 2 malformed tool calls → No implementation
- Step 8 (edit command): 1+ wrong tool attempt → No implementation
- Steps 9-10 (complete/delete): Also blocked by tool call issues

**Expected V12 Result:**
- Malformed tool calls: 6+ → 0-1 (90%+ reduction)
- Commands implemented: 1/6 → 4+/6 (300%+ improvement)
- Grade: B → **A** (expecting near-perfect execution)
- Tool success rate: ~50% → ~95%

### Bonus: 14 New Coding Tools

**System Monitoring (5 tools):**
- `get_system_info` - OS, architecture, Python version
- `check_resources` - CPU, memory, disk usage
- `list_processes` - Running processes with filtering
- `check_port` - Port availability and listening ports
- `get_env_vars` - Environment variables

**Docker Management (5 tools):**
- `docker_ps` - List containers with filtering
- `docker_inspect` - Detailed container/image info
- `docker_logs` - Container logs with tail/since
- `docker_exec` - Execute commands in containers
- `docker_images` - List images with filtering

**Network Testing (4 tools):**
- `ping` - Connectivity and latency testing
- `http_request` - HTTP/HTTPS requests with methods
- `dns_lookup` - Hostname to IP resolution
- `netstat` - Active connections and listening ports

**Total Tools:** 29 (was 15, +14 new tools = 93% increase)

---

## ✅ Pre-Flight Status

### Environment
- ✅ V11 artifacts cleaned (all Python files removed)
- ✅ pyproject.toml verified (flat structure: "cli:app")
- ✅ Python 3.11.9 ready
- ✅ Ollama running with required models
- ✅ qwen2.5-coder:32b available ✅
- ✅ qwen2.5:72b available ✅
- ✅ Git ready
- ✅ **JSON repair system** integrated in Hrisa 0.1.0
- ✅ **29 tools** available (14 new tools ready)

### Files Ready
- ✅ `pyproject.toml` - Flat structure from V11
- ✅ `TASK_TO_PASTE.txt` - Task ready
- ✅ `RUN_TEST.sh` - Ready to execute

### Code Changes Integrated
- ✅ `src/hrisa_code/core/conversation/json_repair.py` - NEW
- ✅ `src/hrisa_code/core/conversation/conversation.py` - UPDATED
- ✅ `src/hrisa_code/tools/system_tools.py` - NEW
- ✅ `src/hrisa_code/tools/docker_tools.py` - NEW
- ✅ `src/hrisa_code/tools/network_tools.py` - NEW
- ✅ `src/hrisa_code/tools/file_operations.py` - UPDATED
- ✅ `pyproject.toml` - psutil dependency added

---

## 🚀 Execute V12 Test Now

### Step 1: Open Terminal
Run the test in your terminal (not through Claude Code).

### Step 2: Navigate to Test Directory
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
```

### Step 3: Verify Prerequisites
```bash
# Check Python
python3 --version  # Should show 3.11.9

# Check Ollama models
ollama list | grep -E "(qwen2.5-coder:32b|qwen2.5:72b)"

# Check Hrisa version
hrisa --version  # Should show 0.1.0

# Verify flat structure
grep -A 1 "\[project.scripts\]" pyproject.toml
# Should show: taskmanager = "cli:app"

# Verify environment is clean
ls *.py 2>/dev/null || echo "✓ Clean (no Python files)"
ls *.db 2>/dev/null || echo "✓ Clean (no database files)"
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
1. **Malformed Tool Calls:** Should be 0-1 (vs V11's 6+)
2. **Commands Implemented:** Should be 4+/6 (vs V11's 1/6)
3. **JSON Repair Messages:** Watch for "[yellow]→ Repaired malformed JSON" messages
4. **Tool Success Rate:** Should be ~95% (vs V11's ~50%)

**Secondary Indicators:**
5. **Loop Detections:** May still see 4-5 (not addressed yet)
6. **Steps Completed:** Expect 14/14 (same as V11)
7. **File Structure:** Should maintain root-level files from V11
8. **Syntax Errors:** Should remain 0 (same as V11)

**Watch for JSON Repair in Action:**
- Look for messages like: "[yellow]→ Repaired malformed JSON (trailing comma)[/yellow]"
- Or: "[yellow]→ Skipped malformed tool call: Could not repair JSON[/yellow]"
- These show the repair system is working

### Step 7: Validation Commands

After Hrisa completes (or hits iteration limits), run:

```bash
# Check file structure (should be at root)
ls -la *.py

# Count commands implemented
grep -c "^def.*_task" cli.py || echo "0 commands found"

# Expected: 4+ command functions (add, list, show, edit, complete, delete)

# Verify syntax
python3 -m py_compile *.py && echo "✓ All files valid" || echo "✗ Syntax errors"

# Check imports
grep -E "^from (db|models) import" cli.py && echo "✓ Imports correct" || echo "✗ Import issues"

# Count tool call errors in output (if you captured it)
# grep -c "malformed tool call" hrisa_output.log
```

---

## 📊 Expected V12 Results vs V11

| Metric | V11 | V12 Target | Improvement |
|--------|-----|------------|-------------|
| **Grade** | B | **A** | +1 grade 🎯 |
| **Steps Completed** | 14/14 | 14/14 | Maintain ✅ |
| **Malformed Tool Calls** | 6+ | **0-1** | -90%+ 🎯 |
| **Commands Implemented** | 1/6 (17%) | **4+/6 (67%+)** | +300%+ 🎯 |
| **Tool Success Rate** | ~50% | **~95%** | +90% 🎯 |
| **db.py at root** | ✅ | ✅ | Maintain ✅ |
| **Syntax errors** | 0 | 0 | Maintain ✅ |
| **Loop detections** | 4-5 | 4-5 | (Not fixed yet) |

**Key Success Criteria:**
- ✅ **CRITICAL:** Malformed tool calls < 2 (vs V11's 6+)
- ✅ **CRITICAL:** Commands implemented ≥ 4/6 (vs V11's 1/6)
- ✅ **GOAL:** Grade A (vs V11's B)
- ✅ Maintain all V11 structural successes

---

## 🎯 Focus Areas for Evaluation

### 1. JSON Repair Effectiveness
**What to Watch:**
- How many times does repair system activate?
- Which repair strategies are used most?
- Are any tool calls still failing despite repair?

**Success = Repair system catches most issues**

### 2. Command Implementation Rate
**What to Check:**
- Step 5 (add): Should succeed (like V11) ✅
- Step 6 (list): **Should succeed now** (failed in V11) 🎯
- Step 7 (show): **Should succeed now** (failed in V11) 🎯
- Step 8 (edit): **Should succeed now** (failed in V11) 🎯
- Step 9 (complete): **Should succeed** (blocked in V11) 🎯
- Step 10 (delete): **Should succeed** (blocked in V11) 🎯

**Success = 4+ commands implemented (vs V11's 1)**

### 3. Tool Call Quality
**What to Measure:**
- Total tool calls made
- Successful executions
- Repaired and succeeded
- Failed despite repair
- Unknown tool attempts

**Success = 95%+ success rate (vs V11's ~50%)**

### 4. Maintained Successes from V11
**Must Maintain:**
- ✅ db.py created at root (not in subdirectory)
- ✅ All imports work correctly
- ✅ Zero syntax errors
- ✅ 14/14 steps completed

---

## 📝 Post-Test Evaluation

After the test completes, create `TEST_EVALUATION_V12.md` documenting:

### Section 1: Executive Summary
- **Grade:** A/B/C/D/F
- **Key Achievement:** Did JSON repair fix the malformed tool call issue?
- **Commands Implemented:** X/6 (vs V11's 1/6)
- **Malformed Tool Calls:** X (vs V11's 6+)

### Section 2: JSON Repair Analysis
- **Total Repair Attempts:** Count from output
- **Repair Strategies Used:** Which ones activated?
- **Repair Success Rate:** How many were successfully repaired?
- **Remaining Failures:** Any that couldn't be repaired?

### Section 3: Performance Comparison
Create table comparing V11 → V12 on all metrics.

### Section 4: Step-by-Step Breakdown
For each step 5-10 (command implementations):
- **Status:** Passed/Failed
- **Tool Calls:** Total, successful, repaired, failed
- **Outcome:** What was created/modified
- **Issues:** Any problems encountered

### Section 5: Validation Results
- File structure verification
- Syntax check results
- Import verification
- Command count

### Section 6: Conclusions
- **Was V12 Successful?** Did we reach Grade A?
- **Root Cause Validation:** Did JSON repair fix the issue?
- **Remaining Issues:** What still needs work?
- **Next Steps:** What to tackle in V13 (if needed)

---

## 🔍 Troubleshooting

### If Malformed Tool Calls Still High (3+)
**Diagnosis:** JSON repair might not cover all edge cases
**Action:** Capture examples and analyze patterns for additional repair strategies

### If Commands Still Not Implemented Despite Fewer Errors
**Diagnosis:** May be hitting loop detection or other limits
**Action:** Focus on loop detection improvements for V13

### If Performance Worse Than V11
**Diagnosis:** JSON repair may have introduced regression
**Action:** Review repair logic, may need to roll back or adjust

### If Grade Still B
**Diagnosis:** Tool call issues partially resolved but not enough
**Action:** Need more aggressive repair strategies or model prompt improvements

---

## 💡 Tips for Success

1. **Monitor in Real-Time:** Watch the terminal output as it runs
2. **Note Repair Messages:** Count how many times repair activates
3. **Check Command Files:** After each step, verify cli.py contents
4. **Capture Output:** Consider using `script` or redirecting output for analysis
5. **Take Notes:** Document interesting patterns or unexpected behaviors

---

## 🚦 Decision Tree: Next Steps After V12

```
V12 Grade A + Malformed Calls < 2 + Commands ≥ 4/6?
├─ YES → 🎉 V12 SUCCESS!
│         Next: Focus on loop detection (A2)
│         Then: Test 14 new tools
│
└─ NO → Analyze failure mode:
    ├─ Malformed calls still high (3+)?
    │  └─ V13: Enhanced repair strategies
    │
    ├─ Commands low (< 4) despite fewer errors?
    │  └─ V13: Loop detection improvements
    │
    └─ Other issues?
       └─ V13: Address specific root cause
```

---

## ✅ Ready to Execute

All prerequisites verified:
- ✅ Environment clean
- ✅ Flat structure confirmed
- ✅ Models available
- ✅ JSON repair integrated
- ✅ 29 tools ready

**Run the test now:**
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
./RUN_TEST.sh
```

**Expected outcome:** Grade A with 90%+ reduction in malformed tool calls and 4+/6 commands successfully implemented.

Good luck! 🚀

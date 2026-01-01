# Q3 2025 Test - Session Guide

**Project:** CLI Task Manager Implementation
**Test Start:** 2026-01-01
**Status:** Ready for Phase 1

---

## What We're Testing

This is the Q3 2025 Real Project Implementation Test - using Hrisa Code to build a complete CLI task manager from scratch. This validates all v0.2.0 improvements in a real-world scenario.

---

## Setup Complete ✓

**Repository Initialized:**
- Location: `/Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager`
- Structure: src/taskmanager/, tests/, docs/
- Configuration: pyproject.toml with all dependencies
- Metrics tracking: METRICS.md ready for data collection

---

## Phase 1: Planning Session

### Your Task

Start an interactive Hrisa Code session and enter plan mode to generate the implementation plan.

### Commands to Execute

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
hrisa chat
```

Then in the chat:
1. Press **SHIFT+TAB** twice to enter **plan mode**
2. Paste the following task:

```
Implement a CLI task manager with the following features:
- Task CRUD operations (add, list, show, edit, complete, delete)
- SQLite persistence with data model (id, title, description, priority, status, tags, dates)
- Search and filtering capabilities
- Export to JSON, CSV, and Markdown formats
- Full test coverage with pytest
- Type hints and documentation
Use Typer for CLI, follow Python best practices.
```

### What to Watch For

**During Complexity Analysis:**
- Should detect as MODERATE or COMPLEX
- Should take 2-3 seconds with spinner

**During Plan Generation:**
- Should take 3-5 seconds with spinner
- Should generate 10-15 steps
- Should have proper phases: exploration → design → implementation → testing → documentation

**Plan Quality Indicators:**
- ✓ Each step is specific and actionable
- ✓ Clear dependencies between steps
- ✓ Good rationale for each step
- ✓ Appropriate tools mentioned (read_file, write_file, search_files, etc.)

### Capturing Metrics

After plan generation, record in METRICS.md:
- Time to generate plan (seconds)
- Number of steps
- Steps per phase breakdown
- Plan quality score (1-5) for specificity, completeness, dependencies, rationale

### What Happens Next

Once the plan is generated, Hrisa will start executing it step by step. Watch for:
- Step context passing (does Step 2 reference Step 1 results?)
- Tool parameter correctness (no missing required parameters?)
- Visual feedback (spinners for all operations?)
- Mode indicator (always visible at bottom?)

---

## Phase 2-4: Implementation, Refactoring, Analysis

After Phase 1 completes, you can either:

**Option A: Let it continue autonomously**
- Plan mode will execute all steps automatically
- Watch and take notes in METRICS.md

**Option B: Step-by-step manual execution**
- Exit after Phase 1
- Execute each module implementation as a separate task
- More control, more detailed metrics

**Option C: Hybrid approach**
- Let it execute Phases 1-2 autonomously
- Manually handle Phases 3-4 for detailed analysis

---

## Important Notes

1. **Metrics Tracking:** Keep METRICS.md updated as you go
2. **Session Log:** Save the full Hrisa transcript for analysis
3. **Time Tracking:** Note start/end times for each phase
4. **Manual Fixes:** Track every manual intervention needed
5. **Code Quality:** Run black, ruff, mypy after each module

---

## Success Criteria Reminder

**⭐ Minimum Success:**
- 50% of code written by Hrisa
- 70% of tests passing without fixes
- Project is functional

**⭐⭐ Good Success:**
- 70% of code written by Hrisa
- 85% of tests passing
- Minimal manual intervention

**⭐⭐⭐ Excellent Success:**
- 85%+ of code written by Hrisa
- 95%+ tests passing
- Production-quality output

---

## Current Status

- ✅ Project initialized
- ✅ Structure created
- ✅ Metrics template ready
- ⏳ Waiting for Phase 1: Planning session

**Next Action:** Run `hrisa chat` and enter plan mode with the task above

---

**Ready when you are!**

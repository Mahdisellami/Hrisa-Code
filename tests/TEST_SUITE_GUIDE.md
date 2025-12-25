# Test Suite Guide

## Overview

Hrisa Code now has a comprehensive regression test suite covering all features implemented so far. This is a **living document** that should be updated as new features are added.

---

## Test Files

### 1. **smoke_test.sh** - Quick Automated Tests
**Purpose**: Fast verification that core functionality works
**Runtime**: ~2 minutes
**Coverage**: 10 essential tests

```bash
./tests/smoke_test.sh
```

**Use when**:
- After making any code changes
- Before committing code
- Quick sanity check

**Tests**:
- Python imports
- CLI entry point
- Model catalog
- Model router
- Model switching
- CLI commands existence
- Config creation
- Orchestrator instantiation
- Backward compatibility

---

### 2. **COMPREHENSIVE_REGRESSION_TESTS.md** - Full Manual Suite
**Purpose**: Thorough testing of ALL features with output quality verification
**Runtime**: 2-4 hours (manual execution)
**Coverage**: 61 tests across 15 categories

```bash
cat tests/COMPREHENSIVE_REGRESSION_TESTS.md
```

**Use when**:
- Before major releases
- After significant feature additions
- Periodic quality assurance
- Investigating issues

**Categories**:
1. Basic CLI (3 tests)
2. Configuration Management (4 tests)
3. Ollama Integration (3 tests)
4. File Operations (5 tests)
5. Interactive Chat (5 tests)
6. Multi-Turn Tool Calling (3 tests)
7. Text-Based Tool Parsing (3 tests)
8. Simple HRISA Generation (3 tests)
9. Comprehensive HRISA Orchestration (3 tests)
10. Agent Mode (3 tests)
11. Background Task Execution (4 tests)
12. Multi-Model Orchestration (5 tests)
13. Error Handling & Edge Cases (5 tests)
14. **Output Verification & Quality** (10 tests) ⭐ NEW
15. Performance & Resource Usage (3 tests)

---

## What's Special About Category 14: Output Verification

This category goes beyond "does it work?" to ask **"does it work well?"**

### Quality Dimensions Tested

#### 1. **Tool Selection Appropriateness**
- Does the model choose the right tool for the task?
- Is it efficient? (e.g., using read_file instead of execute_command)

#### 2. **Response Accuracy**
- Are answers factually correct?
- Can it perform calculations correctly?
- Does it accurately report file contents?

#### 3. **Reasoning Quality**
- Does the model show clear logical steps?
- Can it explain its methodology?
- Is the reasoning coherent?

#### 4. **Planning Quality**
- Does comprehensive HRISA generation plan steps well?
- Are all necessary aspects covered?
- Is the analysis systematic?

#### 5. **Execution Correctness**
- Are tool results interpreted correctly?
- Does it handle JSON/structured data properly?
- Are counts and measurements accurate?

#### 6. **Response Completeness**
- Are multi-part questions fully answered?
- Are all aspects of a request addressed?
- Is important information included?

#### 7. **Code Understanding**
- Can it recognize design patterns?
- Does it understand code structure?
- Can it explain code behavior accurately?

#### 8. **Multi-Step Orchestration Quality**
- Does each orchestration step produce quality output?
- Is the final synthesis comprehensive?
- Are there hallucinations or inaccuracies?

#### 9. **Error Explanation Quality**
- Are errors explained clearly?
- Is guidance helpful?
- Does it maintain coherence after errors?

#### 10. **Context Retention Quality**
- Does it remember previous conversation?
- Can it reference earlier context?
- Is conversation flow natural?

### Scoring System

Each test in Category 14 uses a three-tier scoring:

- **✓ Pass**: Excellent quality, meets all criteria
- **⚠ Partial**: Acceptable but has issues, meets some criteria
- **✗ Fail**: Poor quality, does not meet criteria

This allows tracking **quality trends** over time:
- Are model improvements leading to better outputs?
- Do certain models perform better on specific tasks?
- Are there quality regressions after code changes?

---

## Test Execution Strategy

### Continuous Development
```bash
# After each code change:
./tests/smoke_test.sh

# If smoke tests pass, continue development
# If smoke tests fail, fix immediately
```

### Before Committing
```bash
# Run smoke tests
./tests/smoke_test.sh

# Run a few critical manual tests from comprehensive suite:
# - Test 5.1: Basic chat session
# - Test 8.1: Simple HRISA generation
# - Test 9.1: Comprehensive orchestration
# - Pick 2-3 from Category 14 (output quality)
```

### Before Release
```bash
# Run full comprehensive test suite
# Document results in tests/test-results/YYYY-MM-DD.md

# Ensure:
# - All critical tests pass
# - Output quality scores are acceptable
# - No regressions from previous version
```

### Periodic Quality Checks (Weekly/Monthly)
```bash
# Run Category 14 (Output Verification) tests
# Track quality metrics over time
# Identify areas for improvement
```

---

## Adding New Tests

When you add a new feature, update the comprehensive test suite:

### Step 1: Update Feature Matrix
Add your feature to the table at the top:
```markdown
| 13 | Your New Feature | ✅ | v0.2.0 |
```

### Step 2: Create Test Category (if major feature)
Or add to existing category if it's an enhancement:
```markdown
## CATEGORY X: Your Feature

### Test X.1: Basic Functionality ✓
**Feature**: Your Feature
**Command**: ...
**Expected**: ...
**Status**: [ ] Pass [ ] Fail
```

### Step 3: Write 2-5 Tests
Cover:
- **Happy path**: Normal usage
- **Error cases**: What happens when things go wrong
- **Edge cases**: Boundary conditions, special inputs
- **Output quality**: If applicable, verify response quality

### Step 4: Update Test Summary Template
Add your category to the summary:
```markdown
Category X: Your Feature  [  /5  ] tests passed
```

Update total count.

### Step 5: Consider Output Quality Tests
If your feature produces user-facing output, add quality verification:
- Is the output accurate?
- Is it complete?
- Is reasoning sound?
- Is it helpful?

---

## Test Results Tracking

### Directory Structure
```
tests/
├── smoke_test.sh
├── COMPREHENSIVE_REGRESSION_TESTS.md
├── TEST_SUITE_GUIDE.md (this file)
└── test-results/
    ├── 2025-12-25-baseline.md
    ├── 2026-01-15-after-feature-x.md
    └── ...
```

### Result Template
```markdown
# Test Run: YYYY-MM-DD

## Environment
- Version: 0.1.0
- Model Used: qwen2.5-coder:32b
- Ollama Version: ...

## Quick Tests
- Smoke test: ✅ 10/10 passed

## Comprehensive Tests
[Copy summary template from comprehensive test doc]

## Quality Metrics
[Category 14 results with scoring]

## Notable Observations
- [Anything interesting]
- [Improvements since last run]
- [Issues discovered]

## Action Items
- [ ] Fix test X.Y (if failed)
- [ ] Investigate quality issue in...
```

---

## Best Practices

### 1. **Run Tests Frequently**
- Don't wait for a bug to run tests
- Make it part of your development workflow
- Catch issues early

### 2. **Document Results**
- Record test runs, especially before/after major changes
- Track quality trends over time
- Share results with team/users

### 3. **Keep Tests Updated**
- When you fix a bug, add a test for it
- When you add a feature, add tests
- Remove obsolete tests

### 4. **Focus on Quality, Not Just Functionality**
- Category 14 tests are as important as functional tests
- Quality regressions are real regressions
- Track quality metrics seriously

### 5. **Clean Up After Tests**
- All tests should clean up temporary files
- Don't leave test artifacts in the system
- Tests should be repeatable

### 6. **Independent Tests**
- Tests shouldn't depend on each other
- Each test should set up its own environment
- Tests should be runnable in any order

---

## Quick Reference

### "Did I break anything?"
```bash
./tests/smoke_test.sh
```

### "Is this feature working correctly?"
Find relevant test in `COMPREHENSIVE_REGRESSION_TESTS.md`, run it

### "How good is the output quality?"
Run tests from Category 14

### "Is the system production-ready?"
Run full comprehensive suite + quality verification

### "How do I add tests for my new feature?"
Follow "Adding New Tests" section above

---

## Automation Roadmap

### Phase 1 (Current)
- ✅ Smoke test script (automated)
- ✅ Comprehensive manual test suite
- ✅ Output quality verification framework

### Phase 2 (Future)
- [ ] Automate more functional tests
- [ ] Create test result tracking system
- [ ] Add performance benchmarking
- [ ] Generate test reports automatically

### Phase 3 (Future)
- [ ] CI/CD integration
- [ ] Automated quality scoring
- [ ] Regression detection
- [ ] Trend analysis

---

## Summary

You now have:

1. **Quick tests** for rapid verification (`smoke_test.sh`)
2. **Comprehensive tests** for thorough validation (61 tests)
3. **Quality tests** to ensure output excellence (Category 14)
4. **Living documentation** that evolves with the codebase
5. **Clear process** for adding new tests

**The test suite grows with your project!**

When you add a feature, add tests. When you find a bug, add a test. Keep the documentation alive.

---

## Getting Started

```bash
# 1. Run smoke tests now
./tests/smoke_test.sh

# 2. Browse comprehensive tests
cat tests/COMPREHENSIVE_REGRESSION_TESTS.md

# 3. Pick a few manual tests to try
#    - Start with Category 5 (Interactive Chat)
#    - Then try Category 14 (Output Quality)

# 4. Document your experience
#    - What worked well?
#    - What needs improvement?
#    - Any issues discovered?
```

Happy testing! 🧪

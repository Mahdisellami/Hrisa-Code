# Hrisa Code Testing Strategy

**Last Updated:** 2025-12-26
**Status:** Professional Testing Framework Implementation

---

## Testing Philosophy

**Goal:** Achieve >80% code coverage with comprehensive unit, integration, and regression tests to ensure reliability and maintainability.

**Principles:**
1. **Test-Driven Development:** Write tests before or alongside new features
2. **Comprehensive Coverage:** Every critical path must be tested
3. **Fast Feedback:** Unit tests run in <1s, full suite in <10s
4. **Realistic Scenarios:** Integration tests simulate real usage
5. **Automated Regression:** Prevent breaking existing functionality

---

## Test Pyramid

```
           /\
          /  \         E2E Tests (Manual)
         /____\        - Real user workflows
        /      \       - Full system integration
       /        \      Integration Tests
      /__________\     - Component interaction
     /            \    - Tool system integration
    /              \   Unit Tests
   /________________\  - Individual functions
                       - Class methods
                       - Edge cases
```

**Distribution Target:**
- Unit Tests: 70% (fast, isolated, many)
- Integration Tests: 20% (component interaction)
- E2E/Manual Tests: 10% (full workflows)

---

## Current Test Coverage

### ✅ Well-Tested Components (>80% coverage)
- `config.py` - 84% coverage, 9 tests
- `search_files` with regex - 26 tests
- Git operations - 17 tests
- Loop detector - 27 tests

### ⚠️ Partially Tested (20-80% coverage)
- `ollama_client.py` - 29% coverage, 7 tests

### ❌ Untested Components (0% coverage)
- `conversation.py` - **CRITICAL** - Main orchestration
- `agent.py` - Autonomous mode
- `goal_tracker.py` - Task completion detection
- `task_manager.py` - Background execution
- `interactive.py` - CLI session
- `file_operations.py` - Tool system
- `hrisa_orchestrator.py` - Documentation generation
- `repo_context.py` - Repository analysis
- `model_catalog.py` - Model profiles
- `model_router.py` - Model selection

---

## Testing Roadmap

### Phase 1: Critical Components (High Priority) 🔥
**Goal:** Test components essential for core functionality

#### 1.1 Goal Tracker (`test_goal_tracker.py`)
- [ ] GoalStatus enum and ToolResult dataclass
- [ ] Goal tracking and tool result collection
- [ ] Progress evaluation (mocked LLM responses)
- [ ] Intervention message generation
- [ ] Round tracking and reset
- [ ] Heuristic methods (has_sufficient_info, is_making_progress)
- [ ] Integration scenarios

**Priority:** CRITICAL - Just implemented, needs tests
**Estimated Tests:** 25-30
**Time:** 2-3 hours

#### 1.2 Conversation Manager (`test_conversation_manager.py`)
- [ ] Initialization and configuration
- [ ] Tool call extraction from text
- [ ] Path validation (placeholder detection)
- [ ] Destructive operation detection
- [ ] Tool execution (mocked)
- [ ] Loop detector integration
- [ ] Goal tracker integration
- [ ] Multi-turn tool calling flow
- [ ] Error recovery

**Priority:** CRITICAL - Core orchestration logic
**Estimated Tests:** 40-50
**Time:** 6-8 hours

#### 1.3 Task Manager (`test_task_manager.py`)
- [ ] Task creation and lifecycle
- [ ] Background process management
- [ ] Output capture
- [ ] Task status tracking
- [ ] Process cleanup
- [ ] Error handling

**Priority:** HIGH - Background execution feature
**Estimated Tests:** 20-25
**Time:** 2-3 hours

### Phase 2: Tool System (High Priority) 🔧
**Goal:** Test all tool implementations

#### 2.1 File Operations Tools (`test_file_operations.py`)
- [ ] ReadFileTool - reading, line ranges, errors
- [ ] WriteFileTool - creation, overwrite, directories
- [ ] ListDirectoryTool - listing, recursive, filtering
- [ ] ExecuteCommandTool - execution, timeout, background
- [ ] SearchFilesTool - regex, literal, patterns, limits

**Priority:** HIGH - Core tool functionality
**Estimated Tests:** 30-35
**Time:** 3-4 hours

#### 2.2 Tool Integration (`test_tool_integration.py`)
- [ ] Tool registry and lookup
- [ ] Tool definition format
- [ ] get_all_tool_definitions()
- [ ] Tool parameter validation
- [ ] Tool execution flow

**Priority:** MEDIUM
**Estimated Tests:** 15-20
**Time:** 2 hours

### Phase 3: Agent & Orchestration (Medium Priority) 🤖
**Goal:** Test autonomous capabilities

#### 3.1 Agent Mode (`test_agent.py`)
- [ ] Agent initialization
- [ ] Task execution loop
- [ ] Reflection and planning
- [ ] Error recovery
- [ ] Completion detection
- [ ] Progress reporting

**Priority:** MEDIUM - Complex but less critical
**Estimated Tests:** 25-30
**Time:** 4-5 hours

#### 3.2 HRISA Orchestrator (`test_hrisa_orchestrator.py`)
- [ ] Step execution
- [ ] Model selection per step
- [ ] Context building
- [ ] File writing
- [ ] Error handling

**Priority:** MEDIUM
**Estimated Tests:** 20-25
**Time:** 3-4 hours

### Phase 4: Support Systems (Lower Priority) 📊
**Goal:** Test supporting infrastructure

#### 4.1 Model System (`test_model_system.py`)
- [ ] ModelCatalog - profiles, capabilities, queries
- [ ] ModelRouter - task routing, selection strategies
- [ ] Model switching

**Priority:** LOW - Already has smoke tests
**Estimated Tests:** 15-20
**Time:** 2 hours

#### 4.2 Repository Context (`test_repo_context.py`)
- [ ] File structure analysis
- [ ] Context gathering
- [ ] Caching

**Priority:** LOW
**Estimated Tests:** 15-20
**Time:** 2-3 hours

---

## Test Categories

### Unit Tests
**Location:** `tests/test_*.py`
**Purpose:** Test individual functions and methods in isolation
**Characteristics:**
- Fast (<1ms per test)
- No external dependencies
- Mock all I/O operations
- Test edge cases and error conditions

**Examples:**
```python
def test_loop_detector_detects_identical_calls():
    detector = LoopDetector(max_identical_calls=3)
    detector.add_call("git_status", {"directory": "."})
    detector.add_call("git_status", {"directory": "."})
    detector.add_call("git_status", {"directory": "."})

    status = detector.check_loop("git_status", {"directory": "."})
    assert status == LoopStatus.DETECTED
```

### Integration Tests
**Location:** `tests/integration/test_*.py`
**Purpose:** Test component interaction
**Characteristics:**
- Slower (10-100ms per test)
- Test real component interaction
- Mock only external services (Ollama API)
- Test critical workflows

**Examples:**
```python
async def test_conversation_with_loop_detection():
    # Test that conversation manager properly uses loop detector
    # to prevent repeated tool calls
    pass
```

### Regression Tests
**Location:** `tests/REGRESSION_TESTS.md`
**Purpose:** Manual verification of existing functionality
**Characteristics:**
- Manual execution
- Full system testing
- Real Ollama integration
- User workflow simulation

---

## Testing Tools & Configuration

### Test Framework
```bash
pytest                  # Test runner
pytest-cov             # Coverage reporting
pytest-asyncio         # Async test support
pytest-mock            # Mocking utilities
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/hrisa_code --cov-report=html

# Run specific test file
pytest tests/test_goal_tracker.py

# Run specific test
pytest tests/test_loop_detector.py::test_check_loop_detection

# Run with verbose output
pytest -v

# Run fast (skip slow tests)
pytest -m "not slow"
```

### Coverage Goals

**Overall Target:** >80%
**Per Module:**
- Core components: >90% (conversation, ollama_client, loop_detector, goal_tracker)
- Tools: >85% (file_operations, git_operations)
- Features: >80% (agent, task_manager, orchestrator)
- Support: >70% (config, repo_context, model system)

---

## Test Writing Guidelines

### 1. Test Naming Convention
```python
def test_<component>_<action>_<expected_result>():
    # Example: test_loop_detector_detects_repeated_calls()
    pass
```

### 2. Arrange-Act-Assert Pattern
```python
def test_example():
    # Arrange - Set up test data
    detector = LoopDetector(max_identical_calls=3)

    # Act - Execute the operation
    result = detector.check_loop("tool_name", {})

    # Assert - Verify the result
    assert result == LoopStatus.OK
```

### 3. Test One Thing
Each test should verify one specific behavior.

### 4. Use Descriptive Assertions
```python
# Bad
assert result

# Good
assert result == LoopStatus.DETECTED, "Expected loop to be detected after 3 identical calls"
```

### 5. Mock External Dependencies
```python
@pytest.fixture
def mock_ollama_client():
    client = Mock()
    client.chat_simple.return_value = "COMPLETE"
    return client

async def test_goal_tracker_with_mocked_llm(mock_ollama_client):
    tracker = GoalTracker(ollama_client=mock_ollama_client)
    status = await tracker.check_progress()
    assert status == GoalStatus.COMPLETE
```

### 6. Test Edge Cases
- Empty inputs
- None values
- Boundary conditions
- Error conditions
- Race conditions (for async code)

---

## Continuous Integration

### Pre-Commit Checks
```bash
# Run before committing
make test               # All tests must pass
make lint               # No linting errors
make type-check         # No type errors
make format             # Code formatted
```

### CI Pipeline (Future)
```yaml
# .github/workflows/tests.yml
on: [push, pull_request]
jobs:
  test:
    - Run pytest with coverage
    - Upload coverage report
    - Fail if coverage <80%
```

---

## Test Maintenance

### When to Update Tests
- ✅ When adding new features (write tests first)
- ✅ When fixing bugs (add regression test)
- ✅ When refactoring (ensure tests still pass)
- ✅ When changing APIs (update affected tests)

### Test Review Checklist
- [ ] Tests are independent (can run in any order)
- [ ] Tests are deterministic (same result every time)
- [ ] Tests are fast (<1s for unit, <10s for integration)
- [ ] Tests have clear names and documentation
- [ ] Tests cover happy path and error cases
- [ ] Mocks are used appropriately
- [ ] No hardcoded paths or environment assumptions

---

## Priority Implementation Schedule

### Week 1: Critical Components
- Day 1-2: Goal tracker tests (25-30 tests)
- Day 3-5: Conversation manager tests (40-50 tests)
- Day 6-7: Task manager tests (20-25 tests)

**Deliverable:** Core components >80% coverage

### Week 2: Tool System
- Day 1-3: File operations tests (30-35 tests)
- Day 4-5: Tool integration tests (15-20 tests)

**Deliverable:** Tool system >85% coverage

### Week 3: Agent & Orchestration
- Day 1-3: Agent mode tests (25-30 tests)
- Day 4-5: HRISA orchestrator tests (20-25 tests)

**Deliverable:** Autonomous features >80% coverage

### Week 4: Support & Polish
- Day 1-2: Model system tests (15-20 tests)
- Day 3-4: Repository context tests (15-20 tests)
- Day 5: Integration test suite
- Day 6-7: Documentation and CI setup

**Deliverable:** Complete test suite, >80% overall coverage

---

## Success Metrics

### Quantitative
- [ ] >80% code coverage overall
- [ ] >200 unit tests passing
- [ ] >50 integration tests passing
- [ ] All regression tests pass
- [ ] Test suite runs in <10 seconds
- [ ] Zero flaky tests

### Qualitative
- [ ] Developers confident in refactoring
- [ ] Bugs caught before production
- [ ] Clear test documentation
- [ ] Easy to add new tests
- [ ] Tests serve as usage examples

---

## Resources

- **pytest docs:** https://docs.pytest.org/
- **pytest-cov:** https://pytest-cov.readthedocs.io/
- **pytest-asyncio:** https://pytest-asyncio.readthedocs.io/
- **Test patterns:** https://docs.python-guide.org/writing/tests/

---

## Next Actions

**Immediate (This Sprint):**
1. ✅ Create this testing strategy document
2. ⏳ Write goal tracker unit tests (25-30 tests)
3. ⏳ Write conversation manager tests (40-50 tests)
4. ⏳ Write task manager tests (20-25 tests)
5. ⏳ Update regression tests with new features

**Short Term (Next Sprint):**
6. Write file operations tests
7. Write tool integration tests
8. Achieve >60% coverage

**Long Term:**
9. Write agent and orchestrator tests
10. Create integration test suite
11. Set up CI/CD pipeline
12. Achieve >80% coverage

---

**Document Owner:** Development Team
**Review Cycle:** Monthly
**Last Review:** 2025-12-26

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - Web UI Enhancements

### Added

#### 🎨 Advanced Visualizations (Category 4)
- **Network Graph** (🕸️): Real-time SVG force-directed graph showing agent relationships, parent-child workflows, and team connections
- **Activity Timeline** (📅): Chronological event feed with color-coded activities (created, started, completed, failed, stuck) and clickable agent IDs
- **Performance Charts** (📈): Time-series analysis with 24-hour trends - agent creation rate, success rate line charts, status distribution pie chart, and model performance comparison bars
- **Resource Usage Dashboard** (💾): Top 10 resource consumers with detailed metrics, runtime distribution (5 time buckets), efficiency metrics (tool calls/min, messages/agent, artifact rate, error rate), and activity intensity heatmap
- **System Metrics Dashboard** (🎛️): System health scoring (0-100) with multi-factor analysis, 4 KPI cards (total agents, success rate, active, tool calls), agent status distribution with progress bars, quick stats panel, top 5 models by usage, 24-hour activity timeline, and AI-powered smart recommendations based on system state

#### 📦 Export & Reporting (Category 5)
- **Session Export** (📦): Complete session snapshots in JSON format including all agents, teams, model metrics, statistics, and optional artifacts/logs
- **Agent Export** (📄): Individual agent data export in dual formats - JSON (structured data with messages, logs, artifacts) and Markdown (human-readable report with progress, task details)
- **Analytics Export** (📊): System-wide analytics reports with comprehensive statistics - agent breakdown by status/model/role, performance metrics (tool calls, messages, artifacts, success rate), model performance analysis, and team statistics
- **Log Export** (📋): Plain text log file export for individual agents with formatted timestamps, log levels, and full message history

#### ✨ User Experience Enhancements (Category 6)
- **Toast Notifications** (✅): Non-blocking notification system replacing all 13 alert() dialogs
  - 4 types: success (green), error (red), warning (orange), info (blue)
  - Auto-dismiss after 4 seconds with manual close option
  - Smooth slide-in/out animations from top-right
  - Stackable for multiple simultaneous notifications
  - Mobile-responsive full-width layout

- **Keyboard Shortcuts** (⌨️): Comprehensive hotkey system with 20+ shortcuts for power users
  - General: N (new agent), R (refresh), Esc (close), H (help modal), / (focus search)
  - Export: S (session), A (analytics)
  - Views: G (agents), T (teams), 1-7 (dashboard navigation)
  - Modifiers: Ctrl/Cmd + N (new), Ctrl/Cmd + R (refresh), Ctrl/Cmd + S (export)
  - Interactive help modal with visual kbd elements and grouped categories
  - Smart context handling (ignores shortcuts in input fields except Escape)

- **Advanced Search & Filter** (🔍): Real-time search with field-specific filtering
  - Search across all fields or specific: ID, Task, Model, Tags
  - Real-time filtering as you type
  - Quick filter buttons for field selection
  - Search indicator showing active filter
  - Escape key to clear and unfocus
  - Combined with existing status filters (AND logic)

- **Loading States & Animations** (⏳): Professional feedback and smooth interactions
  - Skeleton screens for initial agent list loads (animated shimmer effect)
  - Full-screen loading overlay with spinner and customizable text
  - Smooth transitions: card hover (lift + shadow), button press (scale), modal fade-in
  - Progress bars: determinate (smooth width transition) and indeterminate (moving bar)
  - Pulse animations for live status indicators
  - All CSS-only animations (GPU accelerated, 60fps)

#### 🔌 Integration Features (Category 7)
- **Webhooks System** (🔗): Generic HTTP POST callbacks to any endpoint
  - Subscribe to events: `agent.started`, `agent.completed`, `agent.failed`, `agent.stuck`
  - HMAC SHA-256 signature verification for security with configurable secrets
  - Custom headers support for authentication
  - Complete event history with response status, time, and error tracking
  - Enable/disable per webhook without deletion
  - 10-second timeout with comprehensive error handling
  - Event payload includes agent ID, status, task, model, progress, and timestamps

- **Notification Channels** (📢): Preconfigured integrations with popular services
  - **Slack Integration**: Webhook-based notifications with formatted messages, sections, and markdown support
  - **Discord Integration**: Rich embeds with color coding (🟢 completed, 🔴 failed, 🟠 stuck, 🔵 started) and structured fields
  - **Email Support**: SMTP configuration for email alerts (ready for production SMTP services)
  - Per-channel event subscriptions (mix and match events)
  - Usage statistics tracking (send count, failure count, last sent timestamp)
  - Independent enable/disable per channel

- **Integration Management UI** (🔌): Complete web-based management interface
  - Visual dashboard showing all webhooks and notification channels
  - Create modals with form validation and dynamic fields
  - Edit capabilities (name, URL, events, enabled status)
  - Delete with confirmation dialogs
  - Real-time statistics display (trigger count, failures, last used)
  - Event subscription checkboxes for easy configuration
  - Type-specific configuration forms (Slack/Discord webhooks, Email SMTP)

#### 🧪 Testing & Quality
- **Web API Tests** (test_web_api.py): 15 comprehensive tests
  - Webhook CRUD operations (create, list, update, delete)
  - Notification channel CRUD operations
  - Export endpoints (session, analytics, agent, logs)
  - Error handling for 404s and validation errors
  - Response structure validation
  - Mock agent_manager with proper fixtures

- **Integration Tests** (test_integrations.py): 15 async tests
  - Webhook triggering with success/failure scenarios
  - HMAC signature generation and verification
  - Notification sending for Slack and Discord
  - Disabled webhook/channel handling
  - Event history tracking and filtering
  - Webhook event pagination
  - Error resilience and retry logic

- **Testing Infrastructure**:
  - pytest fixtures for test client and mock managers
  - Async test support with pytest-asyncio
  - aiohttp HTTP client mocking
  - Comprehensive edge case coverage
  - Integration with existing test suite (48 tests)

#### 📚 Documentation
- **INTEGRATIONS.md**: Complete integration guide (200+ lines)
  - Overview of webhooks and notification channels
  - Step-by-step setup instructions for Slack, Discord, Email
  - HMAC signature verification examples (Python, Node.js)
  - Event type documentation with trigger conditions
  - Real-world examples (webhook handlers, Discord bots)
  - Security best practices and secret rotation
  - Troubleshooting guide with common issues
  - Complete API reference

### Changed

- **User Feedback**: Replaced all 13 blocking `alert()` dialogs with elegant toast notifications
- **Error Messages**: Enhanced error handling throughout with user-friendly, actionable messages
- **Visual Feedback**: Added loading states and skeleton screens for all async operations
- **Navigation**: Improved sidebar organization with categorized view buttons

### Technical Details

**Backend** (agent_manager.py, server.py):
- 3 new dataclasses: WebhookConfig, NotificationChannel, WebhookEvent
- 15+ new methods in WebAgentManager for integration management
- 11 new API endpoints for webhooks and notifications
- Async HTTP client integration with aiohttp
- HMAC signature generation using hashlib

**Frontend** (app.js, index.html, styles.css):
- 30+ new JavaScript functions for UI features
- 5 major visualization views with SVG rendering
- Integration management dashboard with modals
- Toast notification system with queue management
- Keyboard shortcut handler with context awareness
- Advanced search with real-time filtering
- Comprehensive CSS animations and transitions

**Testing** (tests/):
- 2 new test files with 30+ tests
- Mock-based testing for external services
- Async operation testing
- Response validation and error scenarios

**API Endpoints Added**:
```
POST   /api/webhooks                     Create webhook
GET    /api/webhooks                     List webhooks
PUT    /api/webhooks/{id}               Update webhook
DELETE /api/webhooks/{id}               Delete webhook
GET    /api/webhooks/{id}/events        Get event history

POST   /api/notifications/channels       Create channel
GET    /api/notifications/channels       List channels
PUT    /api/notifications/channels/{id}  Update channel
DELETE /api/notifications/channels/{id}  Delete channel

POST   /api/export/session              Export full session
GET    /api/export/agent/{id}           Export agent (JSON/MD)
GET    /api/export/analytics            Export analytics
GET    /api/export/logs/{id}            Export logs
```

**Performance Impact**:
- All animations GPU-accelerated (CSS-only)
- Skeleton screens reduce perceived load time
- Webhook triggers are fully async (non-blocking)
- Toast notifications stack without blocking UI
- Search filtering is debounced for performance

**Code Statistics**:
- 46 commits total (45 ahead of origin)
- ~3,500+ lines of code added
- 400+ lines backend (Python)
- 2,500+ lines frontend (JavaScript)
- 400+ lines styles (CSS)
- 647 lines tests (Python)

### Security

- HMAC SHA-256 signatures for webhook verification
- Configurable secrets per webhook
- HTTPS-only enforcement for production webhooks
- Input validation on all API endpoints
- Sanitized data display in UI (escapeHtml)
- Constant-time comparison for signature verification

## [0.2.0] - 2026-01-01

### Added

#### Step Context Passing
- Previous step results now automatically passed to next steps
- Eliminates 40-50% of redundant tool calls
- Steps can reference and build upon earlier findings
- Results truncated to 500 chars for context efficiency

#### Parameter Checklists
- Built-in parameter validation checklist in step prompts
- Concrete usage examples for common tools
- Reduces tool parameter errors by 70%
- First-try success rate significantly improved

#### Enhanced Heuristic Patterns
- Added refactor task pattern (analyze → design → implement → verify)
- Added optimize task pattern (profile → design → implement → measure)
- Added document task pattern (review → analyze → write)
- Added test task pattern (analyze → design → implement → verify)
- Total patterns increased from 4 to 8 (100% increase)

#### Visual Feedback System
- Animated spinners for all long-running LLM operations
- Spinner for complexity analysis (2-3 seconds)
- Spinner for plan generation (3-5 seconds)
- Spinner for each step execution (variable time)
- Descriptive status messages with color coding

#### Persistent Mode Indicator
- Bottom toolbar shows current mode at all times
- HTML-formatted mode display (normal/agent/plan)
- Color-coded for easy recognition (dim/cyan/magenta)
- Always visible during and between tasks

#### Plan Quality Validation
- Validates LLM-generated plans for quality
- Rejects single-step plans for MODERATE/COMPLEX tasks
- Forces fallback to better heuristic plans
- Ensures proper multi-step decomposition

#### Step Type Instructions
- Explicit explanations of step types (exploration/analysis/documentation)
- Clarifies "compile and summarize" means synthesis, not new searches
- Improves Step 3 quality (summaries instead of file lists)

#### Documentation
- Comprehensive plan mode user guide in README.md
- Performance metrics documented (40-50% reduction)
- Task pattern examples for all 8 heuristic patterns
- Tips for best results and usage expectations
- Created RELEASE_NOTES_v0.2.0.md
- Created SESSION_SUMMARY.md
- Created TESTING_RESULTS.md
- Created QUALITY_IMPROVEMENTS.md

### Changed

#### Mode Behavior
- Modes now persist until manually switched (no auto-reset)
- Mode indicator always visible in bottom toolbar
- Removed automatic reset to normal mode after task completion

#### Tool Definitions
- Made `directory` parameter explicitly required in `search_files`
- Enhanced tool descriptions with concrete usage examples
- Added 4 common use case examples per tool
- Clarified when to use `use_regex=false` vs `use_regex=true`

#### Plan Generation Prompts
- Enhanced with explicit "Breaking Down Tasks" section
- Added examples of good vs bad step descriptions
- Improved LLM guidance for multi-step decomposition
- Better rationale for step types and dependencies

#### Step Execution Prompts
- Added previous results context section
- Added tool parameter checklist
- Added step type understanding guidance
- Clearer instructions for synthesis vs exploration

### Fixed

#### Goal Tracker Premature Completion
- Goal tracking now disabled during plan step execution
- Steps complete properly without premature task termination
- Goal tracking still works for overall task completion detection
- Fixed via `_goal_tracking_enabled` flag with try/finally restoration

#### Mode Indicator Disappearing
- Mode indicator now persistent in bottom toolbar (not just prompt line)
- Uses prompt_toolkit's `bottom_toolbar` feature
- HTML formatting for dynamic color updates
- Always visible regardless of execution state

#### Tool Validation Errors
- Fixed `search_files` missing required `directory` parameter
- Added explicit parameter requirements to tool definitions
- Reduced validation errors from 2-3 per task to 0-1 per task
- Better error messages with concrete examples

#### Single-Step Plans
- Added quality validation to reject poor plans
- Enhanced heuristic fallback for find/search/locate/list tasks
- Better LLM prompt guidance for task decomposition
- MODERATE/COMPLEX tasks always get multi-step plans

#### ANSI Code Caching
- Switched from ANSI escape codes to prompt_toolkit HTML formatting
- Mode indicator colors now update dynamically
- No more cached prompt strings preventing color updates

### Performance

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Tool calls per task | 6-8 | 3-4 | 40-50% reduction |
| Parameter errors | 2-3 per task | 0-1 per task | 70% reduction |
| Self-correction rounds | 2-3 per step | 1 per step | 60% reduction |
| Heuristic coverage | 4 patterns | 8 patterns | 100% increase |

### Testing

- All 48 automated tests passing
- No regressions introduced
- Manual testing completed for all improvements
- Test coverage maintained at >80% for core modules

---

## [0.1.0] - 2025-12-30

### Added

#### Core Features
- Interactive CLI chat interface with prompt_toolkit
- Three execution modes: normal, agent, plan
- Mode switching with SHIFT+TAB or `/agent` command
- Ollama integration for local LLM support
- Async conversation management

#### Agent Mode
- Autonomous multi-step task execution
- Automatic task breakdown
- Proactive codebase exploration
- Self-reflection and adaptation
- Error recovery with retry logic

#### Plan Mode (Initial)
- Automatic task complexity detection (SIMPLE/MODERATE/COMPLEX)
- Dynamic plan generation with LLM
- Heuristic fallback patterns (analyze, implement, find, fix)
- Step-by-step execution with progress tracking
- Adaptive plan adjustment based on discoveries
- Error handling and recovery strategies

#### Complexity Detection
- Multi-factor analysis (keywords, scope, requirements, file count)
- Three complexity levels with clear criteria
- Integration with plan mode for step count determination

#### Tool System
- File operations (read, write, delete, list, search)
- Git operations (status, diff, log, branch, commit, push, pull, stash)
- Command execution with output capture
- Approval manager for write operations
- Loop detection to prevent repetitive tool calls

#### Background Tasks
- Task manager for background command execution
- Process management (create, monitor, kill)
- Task status tracking
- Output capture and retrieval

#### HRISA Orchestrator
- Multi-step repository analysis
- 5-phase orchestration (Architecture → Components → Features → Workflows → Synthesis)
- Guided LLM exploration
- Comprehensive HRISA.md generation

#### Configuration
- YAML-based configuration with Pydantic validation
- Three-level fallback (project → user → defaults)
- Model, tool, and server settings
- Example config included

#### CLI Commands
- `chat` - Interactive chat session
- `models` - List available Ollama models
- `init` - Initialize configuration
- `readme` - Generate README.md
- `contributing` - Generate CONTRIBUTING.md
- `api` - Generate API.md
- Progressive context-building variants for all documentation commands

### Documentation
- Comprehensive README.md
- Architecture documentation (docs/ARCHITECTURE.md)
- Docker guide (docs/DOCKER.md)
- Development guide (docs/DEVELOPMENT.md)
- Quickstart guide (docs/QUICKSTART.md)
- Project guide for AI assistants (CLAUDE.md)
- Future roadmap (FUTURE.md)

### Testing
- pytest test suite with >80% coverage
- Unit tests for all core modules
- Mock-based testing for Ollama API
- Test fixtures and helpers

### Development Tools
- Black code formatting (100 char line length)
- Ruff linting
- MyPy type checking
- Docker and Docker Compose support
- Makefile for common tasks

---

## [Unreleased]

### Planned for Q3 2025

#### Real Project Implementation Test
- Use Hrisa to implement complete real-world projects
- Test plan mode with sustained, complex development
- Discover gaps in multi-file coordination
- Validate across diverse task types

#### Future Enhancements
- Adaptive mode switching based on task complexity
- Performance optimization (quantization, caching, parallelization)
- Enhanced code analysis and review capabilities
- Full MCP (Model Context Protocol) integration
- Multi-file refactoring coordination
- Advanced error recovery strategies

---

[0.2.0]: https://github.com/yourusername/hrisa-code/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/hrisa-code/releases/tag/v0.1.0

# Changelog

All notable changes to DeepTrace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Changed - 2025-12-26

**Major Project Restructuring**
- Reorganized entire codebase to match monorepo structure from `project_spec.md`
- Renamed `deep_research.py` → `app.py` as primary entry point
- Moved all Python modules to `backend/app/` directory structure:
  - `backend/app/agents/` - All 5 agent modules (planner, search, writer, email, clarifying)
  - `backend/app/core/` - Core utilities (orchestrator, types, confidence, retry, monitoring)
  - `backend/app/data/` - Database layer (db.py, migrations/)
  - `backend/app/api/` - API layer (prepared for FastAPI migration)
  - `backend/app/search/` - Search integrations (prepared for future)
  - `backend/app/workers/` - Background tasks (prepared for future)
- Moved `research_manager.py` → `backend/app/core/orchestrator.py`
- Moved all test files to `backend/tests/`
- Moved `requirements.txt` → `backend/requirements.txt`
- Created `data/` directory for database files (research.db, memory-tool.db)
- Updated all import paths across Python files to reflect new structure
- Cleaned up 9 temporary implementation documentation files
- Updated `CLAUDE.md` with new file structure and commands
- Completely rewrote `README.md` with professional description and architecture overview
- Updated `.gitignore` to exclude `data/` directory

**Breaking Changes**
- Run command changed: `python deep_research.py` → `python app.py`
- Install command changed: `pip install -r requirements.txt` → `pip install -r backend/requirements.txt`
- All imports now reference `backend.app.*` instead of root-level modules

### Added - 2025-12-26

**Phase 1: MVP Core Foundation**

**Database Persistence Layer**
- SQLite database implementation with PostgreSQL migration compatibility
- Complete CRUD operations for reports, sources, and logs
- Schema with UUIDs (as TEXT), ISO timestamps, CHECK constraints
- Error handling: write operations raise exceptions, read operations return None/empty list
- Comprehensive test suite (`test_db.py` - 246 lines)
- Database documentation: README.md, INTEGRATION.md, QUICKSTART.md, EXAMPLES.md

**Enhanced Agent System**
- Expanded `ReportData` schema from 3 to 11 fields:
  - summary, goals, methodology, findings, competitors, risks, opportunities
  - recommendations, confidence_score, markdown_report, follow_up_questions
- Confidence scoring algorithm (`backend/core/confidence.py`)
  - Base score (0.3) + source bonus + quality indicators + consistency
  - Human-readable labels (Low to High Confidence)
- Retry logic with exponential backoff (`backend/core/retry.py`)
  - Configurable max_attempts, base_delay, max_delay
  - Automatic retry with increasing delays
- Graceful degradation throughout pipeline
  - System never crashes completely
  - Always returns partial results on failure
  - Structured error reports with `_create_error_report()`
- Clarifying agent (`clarifying_agent.py`) for vague query detection
- Updated `research_manager.py` with resilience features:
  - `_plan_searches_with_retry()`, `_perform_searches_resilient()`
  - `_search_with_retry()`, `_write_report_with_retry()`
  - Comprehensive error handling and logging

**Research Modes**
- Research mode types (`backend/core/types.py`)
  - ResearchMode enum: QUICK and DEEP
  - MODE_CONFIG with min/max sources and target times
  - Source count validation with three-tier enforcement
- Performance tracking (`backend/core/monitoring.py`)
  - PerformanceTracker class for phase-by-phase timing
  - Comparison against mode targets with warnings
- Mode-aware planner agent
  - Factory pattern: `create_planner_agent(mode)`
  - Dynamic instructions based on mode configuration
- Updated UI (`deep_research.py`) with mode selector
  - Radio button for Quick vs Deep selection
  - Mode descriptions in UI
- Updated pipeline with mode parameter throughout
  - Mode passed through all pipeline stages
  - Performance tracking integrated
- Validation test script (`test_modes.py`)

**Documentation**
- Complete implementation summaries for all three components
- Migration guides and integration instructions
- Quick reference guides for developers
- Data flow diagrams and architecture documentation

### Added - 2025-12-25

**Documentation Infrastructure**
- Created comprehensive documentation structure
- `architecture.md` - Complete system design and data flow
- `changelog.md` - Version history tracking
- `project_status.md` - Development progress tracking
- `project_spec.md` - Consolidated specifications (replaced 12 separate docs)
- Documentation update rules in CLAUDE.md
- Git workflow and repository etiquette guidelines

**Documentation Consolidation**
- Merged redundant documentation into single `project_spec.md`
- Removed 12 duplicate specification files
- Streamlined CLAUDE.md to focus on behavioral rules and current implementation
- Established clear documentation update workflow

### Planned
- Live execution logs in UI
- Stop button (hard kill)
- Reset button (wipe state)
- Integration of database persistence into pipeline
- Wire up confidence scoring in UI
- Partial results handling in UI
- Clarifying questions workflow

---

## [0.1.0] - 2025-12-25

### Added - Initial MVP
- Multi-agent research pipeline
  - Planner Agent for search strategy
  - Search Agent for parallel web searches
  - Writer Agent for report synthesis
  - Email Agent for optional delivery
- Gradio-based web UI
- OpenAI Agents SDK integration
- Async orchestration via `ResearchManager`
- Pydantic models for structured outputs
  - `WebSearchPlan` with reasoning
  - `ReportData` with summary, report, follow-up questions
- SendGrid email integration (optional)
- Environment variable configuration
- OpenAI trace link generation for debugging

### Documentation
- Comprehensive project specification (`docs/project_spec.md`)
- Agent behavioral rules (`docs/AGENT_INSTRUCTIONS.md`)
- Error handling policy (`docs/ERROR_HANDLING_POLICY.md`)
- Test strategy (`docs/TEST_STRATEGY.md`)
- Contributing guidelines (`docs/CONTRIBUTING.md`)
- Architecture documentation (`docs/architecture.md`)
- Project status tracking (`docs/project_status.md`)
- CLAUDE.md for AI assistant guidance

### Technical Details
- Default 3 web searches per query
- Search summaries: 2-3 paragraphs, <300 words each
- Report target: 5-10 pages, ≥1000 words
- All agents use `gpt-5-nano` model
- Parallel search execution via `asyncio`
- Graceful error handling (searches can fail independently)
- Email sending skips if API key not configured

### Dependencies
- gradio - Web UI
- python-dotenv - Environment management
- openai-agents - Agent framework
- pydantic - Data validation
- sendgrid - Email delivery

---

## Version History Summary

- **v0.1.0** (2025-12-25) - Initial MVP with multi-agent pipeline and Gradio UI
- **Unreleased** - SQLite persistence, live logs, mode selection, enhanced UX

---

*For detailed specifications, see [project_spec.md](project_spec.md)*
*For current development status, see [project_status.md](project_status.md)*

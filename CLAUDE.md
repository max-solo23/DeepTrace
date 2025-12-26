# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Documentation

### Core Documentation Files

- **[Architecture](docs/architecture.md)** - System design and data flow
- **[Changelog](docs/changelog.md)** - Version history
- **[Project Status](docs/project_status.md)** - Current progress
- **[Project Spec](docs/project_spec.md)** - Full requirements, API specs, architecture, data models, and tech details

### Documentation Update Rules

**Update files in `docs/` folder after:**
- Major milestones
- Major feature additions
- Architectural changes

**Use `/update-docs-and-commit` slash command when making git commits**
- Ensures documentation is updated alongside code changes
- Required for all significant changes

**Which files to update:**
- `architecture.md` - When system design or data flow changes
- `changelog.md` - After every feature/fix (follow Keep a Changelog format)
- `project_status.md` - After completing tasks or reaching milestones
- `project_spec.md` - When requirements or specifications change

---

## ⚠️ CRITICAL: Agent Behavioral Rules (MUST FOLLOW)

From `docs/AGENT_INSTRUCTIONS.md` - **These rules have MAXIMUM PRIORITY**:

### 1. Never Guess Silently
- Mark uncertainty explicitly
- Attempt clarification
- Fall back to safe defaults

### 2. Preserve Stability Over Smartness
Priority order:
1. System must not crash
2. Outputs must remain structured
3. Only then optimize intelligence

### 3. Always Follow the Pipeline
Do NOT improvise parallel flows unless explicitly allowed.

Required process:
1. Validate input
2. Clarify if required
3. Plan
4. Search
5. Analyze
6. Synthesize
7. Persist
8. Output

### 4. Logs Are Not Optional
Every meaningful step MUST log:
- Action name
- Step purpose
- Success/failure state

### 5. Respect Configurable Modes
- Quick vs Deep mode
- Search mode
- Reviewer toggles (future)

### 6. Partial Success is Better Than Failure
If something breaks:
- Retry if allowed
- Fallback
- Degrade gracefully
- Deliver partial results

### 7. Never Produce Malicious Content
Hard block:
- Illegal guides
- Exploitation
- Harm instructions

---

## Error Handling Policy (MAXIMUM PRIORITY)

From `docs/ERROR_HANDLING_POLICY.md`:

**Core Rule**: Errors must NEVER silently fail.

**Handling Strategy**:
1. Retry if allowed
2. Fallback to alternative
3. Degrade gracefully
4. Mark missing sections
5. Log everything

**User Communication**:
- Clear error messages
- No technical stack traces in UI
- Developer logs preserved internally

---

## Structured Output Requirements

From `docs/AGENT_INSTRUCTIONS.md`:
- Every research run MUST output required schema
- Missing blocks MUST be explicitly labeled (not omitted)

---

## Project Philosophy

From `docs/CONTRIBUTING.md`:
- **Quality > Speed**
- **Stability > Cleverness**
- Clear naming, explicit error handling, logging required

**Success Criteria**: ≥95% successful research completion rate

---

## Current Implementation

### Multi-Agent System

Orchestrated by `ResearchManager.run()` (async generator that yields status updates):

1. **Planner Agent** (`backend/app/agents/planner_agent.py`)
   - Analyzes query → generates `WebSearchPlan`
   - Mode-aware: creates different plans for Quick (4-6 sources) vs Deep (10-14 sources)
   - Factory pattern: `create_planner_agent(mode)`
   - Model: `gpt-5-nano`
   - Output: `WebSearchPlan` (Pydantic)

2. **Search Agent** (`backend/app/agents/search_agent.py`)
   - Executes web searches in parallel
   - Returns concise summaries: 2-3 paragraphs, <300 words
   - Uses `WebSearchTool(search_context_size="low")`
   - Model: `gpt-5-nano` with `tool_choice="required"`
   - Error handling: retry logic with exponential backoff

3. **Writer Agent** (`backend/app/agents/writer_agent.py`)
   - Synthesizes search results → detailed Markdown report
   - Target: 5-10 pages, ≥1000 words
   - Model: `gpt-5-nano`
   - Output: `ReportData` (Pydantic) with 11 fields:
     - summary, goals, methodology, findings, competitors, risks
     - opportunities, recommendations, confidence_score, markdown_report, follow_up_questions

4. **Email Agent** (`backend/app/agents/email_agent.py`)
   - Converts Markdown → HTML → SendGrid
   - Optional (skips if `SENDGRID_API_KEY` not set)
   - Model: `gpt-5-nano`

5. **Clarifying Agent** (`backend/app/agents/clarifying_agent.py`)
   - Detects vague queries that need clarification
   - Generates 2-3 focused clarifying questions
   - Model: `gpt-5-nano`
   - Output: `ClarificationResult` (Pydantic)

### Backend Core Modules

**`backend/app/core/`** - Core utilities and business logic:
- `orchestrator.py` - ResearchManager orchestration with retry logic & error handling
- `types.py` - ResearchMode enum, MODE_CONFIG, validation
- `confidence.py` - Confidence scoring algorithm
- `retry.py` - Retry logic with exponential backoff
- `monitoring.py` - Performance tracking
- `status_reporter.py` - Live status streaming to UI with real-time progress updates
- `error_handling.py` - Error report generation for graceful failure handling
- `persistence.py` - Database persistence wrapper with safe error handling
- `__init__.py` - Public API exports

**`backend/app/data/`** - Database persistence layer:
- `db.py` - SQLite CRUD operations (PostgreSQL-compatible)
- `__init__.py` - Public API exports

### File Structure (Current MVP)

```
app.py                  # Gradio UI entry point with mode selector
requirements.txt        # Python dependencies
.env.example           # Environment template
.gitignore             # Git ignore patterns
CLAUDE.md              # This file - Claude Code guidance
README.md              # Project README

backend/                # Backend application (follows project_spec.md structure)
  app/
    agents/             # AI agents
      planner_agent.py      # Mode-aware WebSearchPlan generator
      search_agent.py       # Parallel web search executor
      writer_agent.py       # Report synthesizer (11-field schema)
      email_agent.py        # SendGrid integration
      clarifying_agent.py   # Vague query detector
    api/                # API layer (prepared for FastAPI migration)
      routes/
    core/               # Core utilities and business logic
      orchestrator.py       # ResearchManager with retry logic & error handling
      types.py              # ResearchMode enum, MODE_CONFIG, validation
      confidence.py         # Confidence scoring algorithm
      retry.py              # Retry logic with exponential backoff
      monitoring.py         # Performance tracking
      status_reporter.py    # Live status streaming to UI
      error_handling.py     # Error report generation
      persistence.py        # Database persistence wrapper
      __init__.py           # Exports: ResearchMode, confidence, retry, etc.
    data/               # Database persistence layer
      db.py                 # SQLite CRUD operations (PostgreSQL-compatible)
      migrations/           # Future database migrations
      __init__.py           # Exports: init_db, save_report, get_report, etc.
    search/             # Search integrations (prepared for future)
    workers/            # Background task workers (prepared for future)
  tests/                # Test suite
    test_db.py              # Database layer tests
    test_pipeline.py        # Agent system integration tests
    test_agents.py          # Research modes validation tests
    test_db_integration.py  # Database integration tests
    test_export.py          # Export functionality tests

data/                   # Local data storage
  research.db          # SQLite database (gitignored)
  memory-tool.db       # Legacy database file (gitignored)

docs/                   # Documentation
  architecture.md       # System design and data flow
  changelog.md          # Version history
  project_status.md     # Current progress and roadmap
  project_spec.md       # Full project specifications
  AGENT_INSTRUCTIONS.md      # Behavioral rules
  ERROR_HANDLING_POLICY.md   # Error handling requirements
  TEST_STRATEGY.md           # Testing approach
  CONTRIBUTING.md            # Contribution guidelines

exports/                # Exported research reports (gitignored)
```

---

## Development Workflow

### Setup

**Requirements:**
- Python 3.13 or higher

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux
python3.13 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env: set OPENAI_API_KEY (required)
# Optional: SENDGRID_API_KEY, SENDGRID_FROM, SENDGRID_TO
```

### Git Workflow & Repository Etiquette

**CRITICAL**: Always use feature branches. **NEVER** commit directly to `main`.

#### Branch Naming Convention
- New features: `feature/description`
- Bug fixes: `fix/description`

#### Workflow for Major Changes

1. **Create a new branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Develop and commit on the feature branch**
   - Write clear commit messages describing the change
   - Keep commits focused on a single change

3. **Test locally before pushing**:
   ```bash
   python deep_research.py  # Test the application works
   # Add other tests as they become available (pytest, etc.)
   ```

4. **Push the branch**:
   ```bash
   git push -u origin feature/your-feature-name
   ```

5. **Create a Pull Request to merge into `main`**
   - Include a description of what changed and why
   - Reference any related issues or docs

6. **Use `/update-docs-and-commit` slash command for commits** (if available)
   - Ensures documentation is updated alongside code changes

#### Pull Request Requirements
- Create PRs for **ALL** changes to `main`
- **NEVER** force-push to `main`
- Include description of what changed and why

#### Before Pushing Checklist
- [ ] Test the application runs without errors
- [ ] Verify changes follow the architectural rules
- [ ] Update relevant documentation in `/docs` if needed
- [ ] Ensure error handling follows the Error Handling Policy

### Run Application

```bash
python app.py
```
- Launches Gradio UI with `inbrowser=True`
- Console prints OpenAI trace links: `https://platform.openai.com/traces/trace?trace_id={trace_id}`
- Database stored in `data/research.db`
- Exported reports saved to `exports/` directory

### Debugging

- Use OpenAI trace links to debug agent reasoning, tool calls, model interactions
- Check console logs for pipeline progression
- Email failures logged but don't block pipeline

---

## Test Strategy

From `docs/TEST_STRATEGY.md`:

### Testing Priorities
1. System must not crash
2. Output must ALWAYS follow schema
3. Failures must degrade gracefully

### Test Layers

**Unit Tests**: planner logic, search agent logic, writer formatting, DB layer, logging

**Integration Tests**: research pipeline full execution, quick mode, deep mode, partial failures, stop + reset behavior

**Reliability Tests**: retry logic, fallback logic, malformed input handling

**Security Tests**: malicious research blocking, sensitive topic handling

### Success Conditions
- 95% pass minimum
- No silent failures allowed

---

## Key Configuration Parameters

### Agent Models
All agents currently use: `gpt-5-nano`

### Planner Agent
- `HOW_MANY_SEARCHES = 3` in `planner_agent.py`

### Search Agent
- `search_context_size="low"` (WebSearchTool configuration)
- Summaries: 2-3 paragraphs, <300 words
- Parallel execution via `asyncio.as_completed()`

### Writer Agent
- Target: 5-10 pages, ≥1000 words
- Output format: Markdown with sections

### Performance Targets
See [Project Spec](docs/project_spec.md) for full details:
- Quick mode: ≤2 min, 4-6 sources
- Deep mode: ≤8 min, 10-14 sources
- Hard cap: 20 sources

---

## Email Integration

Email sending is **optional** and **safe to skip**:
- Checked via `os.environ.get("SENDGRID_API_KEY")`
- Returns `(False, ["SENDGRID_API_KEY not set"])` if not configured
- Failures wrapped in try/except, returning `(False, [error_message])`
- SendGrid requires verified sender/domain for `SENDGRID_FROM`

---

## Future Architecture

See [Project Spec](docs/project_spec.md) for:
- Monorepo structure (FastAPI backend + Next.js frontend)
- Database migration plan (SQLite → Postgres/Neon)
- API specifications
- UI design guidelines
- Engineering roadmap

**Migration Philosophy**: Zero redesign, only upgrade storage layer

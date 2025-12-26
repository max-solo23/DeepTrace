# Architecture

## System Overview

DeepTrace is a multi-agent AI research assistant built on the OpenAI Agents SDK. The system orchestrates specialized agents to produce comprehensive, structured research reports.

---

## Current Architecture (MVP)

### Tech Stack

- **Language**: Python 3.10+
- **Agent Framework**: OpenAI Agents SDK
- **UI**: Gradio (web-based)
- **LLM**: OpenAI GPT-5-nano
- **Dependencies**: pydantic, python-dotenv, sendgrid

### File Structure

```
DeepTrace/
├── deep_research.py        # Gradio UI entrypoint
├── research_manager.py     # Main orchestrator
├── planner_agent.py        # Query planning agent
├── search_agent.py         # Web search agent
├── writer_agent.py         # Report synthesis agent
├── email_agent.py          # Email delivery agent
├── requirements.txt
├── .env.example
├── CLAUDE.md              # Claude Code guidance
└── docs/
    ├── project_spec.md    # Complete specifications
    ├── architecture.md    # This file
    ├── changelog.md       # Version history
    └── project_status.md  # Current progress
```

---

## Data Flow

### Research Pipeline

```
User Query
    ↓
┌─────────────────────────────────────────┐
│ ResearchManager.run()                   │
│ (Async generator - yields UI updates)  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 1. Planner Agent                        │
│    Input: User query                    │
│    Output: WebSearchPlan (3 searches)   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. Search Agent (Parallel Execution)    │
│    Input: WebSearchItem[]               │
│    Uses: WebSearchTool                  │
│    Output: Summary[] (2-3 para each)    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. Writer Agent                         │
│    Input: Query + Summaries             │
│    Output: ReportData (markdown)        │
│    - short_summary                      │
│    - markdown_report (5-10 pages)       │
│    - follow_up_questions                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. Email Agent (Optional)               │
│    Input: Markdown report               │
│    Output: HTML email via SendGrid      │
│    (Skipped if SENDGRID_API_KEY unset)  │
└─────────────────────────────────────────┘
    ↓
Final Report + Status Updates
```

### Agent Details

#### Planner Agent
- **Model**: gpt-5-nano
- **Input**: Raw user query
- **Output**: Structured `WebSearchPlan` (Pydantic)
- **Config**: `HOW_MANY_SEARCHES = 3`
- **Purpose**: Analyzes query and generates targeted search terms with reasoning

#### Search Agent
- **Model**: gpt-5-nano
- **Input**: Individual `WebSearchItem` (query + reason)
- **Tool**: `WebSearchTool(search_context_size="low")`
- **Output**: Concise summary (2-3 paragraphs, <300 words)
- **Execution**: Parallel via `asyncio.as_completed()`
- **Error Handling**: Returns `None` on failure, continues pipeline

#### Writer Agent
- **Model**: gpt-5-nano
- **Input**: Original query + all search summaries
- **Output**: `ReportData` (Pydantic)
  - `short_summary`: 2-3 sentences
  - `markdown_report`: 5-10 pages, ≥1000 words
  - `follow_up_questions`: List of suggested topics
- **Purpose**: Synthesizes research into comprehensive markdown report

#### Email Agent
- **Model**: gpt-5-nano
- **Input**: Markdown report
- **Tool**: `send_email()` function (SendGrid API)
- **Output**: HTML-formatted email
- **Config**: Uses env vars (`SENDGRID_FROM`, `SENDGRID_TO`, `SENDGRID_DEFAULT_SUBJECT`)
- **Optional**: Skips gracefully if API key not configured

---

## State Management

### Current (MVP)
- **In-memory only** - no persistence
- State flows through async generator
- UI updates via yielded status messages

### Planned (Phase 1)
- **SQLite database** with tables:
  - `reports` - Research outputs
  - `sources` - URLs + reliability metadata
  - `logs` - Execution history
- Append-only logs
- Immutable reports after finalization

---

## Error Handling

### Philosophy
1. **Never fail silently**
2. **Retry → Fallback → Degrade**
3. **Partial success > total failure**

### Implementation
- Search failures return `None`, pipeline continues
- Email failures logged but don't block completion
- All errors logged to console
- UI shows clear error messages (no stack traces)

---

## External Dependencies

### Required
- **OpenAI API** (`OPENAI_API_KEY`)
  - Agent execution
  - Web search tool
  - GPT-5-nano model

### Optional
- **SendGrid API** (`SENDGRID_API_KEY`)
  - Email delivery
  - Gracefully skipped if not configured

---

## Future Architecture (Planned)

### Phase 2-4 Evolution

```
┌─────────────────────────────────────────────────┐
│              Frontend (Next.js)                 │
│  - App Router                                   │
│  - Shadcn UI components                         │
│  - Tailwind styling                             │
│  - TypeScript                                   │
└─────────────────────────────────────────────────┘
                      ↓ HTTP
┌─────────────────────────────────────────────────┐
│              Backend (FastAPI)                  │
│  /api/research     - Start/stop/status          │
│  /api/logs         - Live/historical logs       │
│  /api/export       - Download/email             │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           Orchestrator & Agents                 │
│  - Planner Agent                                │
│  - Search Agent                                 │
│  - Writer Agent                                 │
│  - Reviewer Agent (future)                      │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          Persistence (Postgres/Neon)            │
│  - Reports table (UUID primary keys)            │
│  - Sources table (reliability metadata)         │
│  - Logs table (execution history)               │
└─────────────────────────────────────────────────┘
```

### Key Changes
- **Monorepo structure** (`/backend`, `/frontend`, `/shared`)
- **FastAPI** REST API with Pydantic schemas
- **SQLite → Postgres (Neon)** migration
- **Gradio → Next.js** UI migration
- **Reviewer Agent** for verification (Phase 3)
- **Background workers** for long-running research

---

## Design Principles

1. **Backend as source of truth** - all logic in backend
2. **Frontend as pure consumer** - UI only, no business logic
3. **Shared schemas** - OpenAPI → TypeScript generation
4. **Agent-safe architecture** - clear boundaries for autonomous coding
5. **Zero redesign migrations** - architectural decisions support future upgrades

---

## Performance Targets

- **Quick Research**: ≤2 min, 4-6 sources
- **Deep Research**: ≤8 min, 10-14 sources
- **Hard cap**: 20 sources
- **Reliability**: ≥95% successful completion

---

## Security Considerations

- Environment variables for API keys (`.env` gitignored)
- No sensitive data in code or commits
- SendGrid requires verified sender/domain
- Malicious research queries hard-blocked
- No user authentication (MVP phase)

---

*Last updated: 2025-12-25*

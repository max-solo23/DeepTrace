# DeepTrace - Project Specification

## Project Overview

**Purpose**: Build a SERIOUS, RELIABLE AI Research Assistant that produces structured, trustworthy research to support real-world decisions.

**Primary Priorities**:
1. Backend stability & reliability
2. Agentic AI orchestration
3. Product readiness (future SaaS)

**Core Mission**: Make deep research EASY, CONTROLLED, AUDITABLE.

**Audience**:
- Phase 1 → Personal use
- Phase 2 → Selectable personas (developer, entrepreneur, marketer, student, etc.)

**Brand Identity**:
- Professional
- Analytical
- Enterprise-credible

**Success Criteria**:
- Produces research useful enough to support decision-making
- ≥ 95% successful research completion rate
- Structured, readable, credible output

---

## Product Requirements

### MVP Scope — MUST HAVE

- **Detailed live execution logging**
- **Stop button** (HARD kill instantly)
- **Reset button** (wipe system state + UI)
- **Search depth selector + auto mode**
- **Manual export**:
  - Email
  - Markdown report
- **Clarifying questions**:
  - Only when vague query or deep mode
- **Hybrid UI**:
  - Markdown structured report
  - Navigation sidebar
- **SQLite persistence**:
  - Reports
  - Sources + reliability metadata
  - Execution logs
- **Resilient system**:
  - Retries
  - Fallback strategies
  - Partial result handling

### MVP — OUT OF SCOPE

- Hallucination evaluator
- Reviewer LLM
- Agent debate mode
- Streaming everywhere
- Multi-user SaaS
- Authentication

### Research Modes

- **Quick Research** = speed priority
- **Deep Research** = depth priority

### Structured Research Report Spec

Required output schema:
```
summary
goals
methodology
findings
competitors
risks
opportunities
recommendations
confidence_score
sources[] {
  url
  reliability
}
```

### Partial Results Policy

If runtime or system failure occurs:
- Return structured partial output
- Clearly mark missing blocks

### Sensitive Topic Policy

Allowed but requires:
- Warnings
- Higher credibility threshold

**Malicious/illegal research = HARD BLOCK**

---

## Performance Requirements

### Quick Research
- **Time**: ≤ 2 minutes
- **Sources**: 4–6

### Deep Research
- **Time**: ≤ 8 minutes
- **Sources**: 10–14

### System Constraints
- **Hard cap**: 20 sources
- Graceful stop at limits
- Partial report allowed

### Reliability Target
- ≥ 95% successful completion

---

## Architecture

### Current Stack

- **Backend**: Python with **FastAPI** (framework is FIXED)
- **UI MVP**: Gradio
- **DB MVP**: SQLite
- **Future DB**: Neon/Postgres
- **Future UI**: Next.js

### Execution Pipeline

1. Receive query
2. If vague → clarifying questions
3. Planner → build research strategy
4. Search Agent → fetch sources
5. Reliability filters + dedupe
6. Writer → structured markdown report
7. Save to DB
8. Show output + export options

### Search Strategy (Hybrid)

- Independent APIs (default)
- OpenAI Web Search mode (toggle)
- Optional scraping for depth

### Source Policy

Balanced credibility:
- Prefer reputable sources
- Allow strong tech blogs
- Allow forums for emerging topics
- Recency improves trust

### Failure Strategy

- Retries
- Fallback sources
- Fallback summarization
- Partial report allowed

### Data Persistence

Persist:
- Report
- Sources + metadata
- Logs

**Storage transitions**: SQLite → Postgres (Neon)

### Multi-Agent Roadmap (Future V1)

Optional Reviewer System:
- Verification mode (primary)
- Debate mode (optional toggle)
- Audit summary (optional toggle)

---

## Data Models

Defines persistent structures in SQLite → Postgres future migration safe.

### Reports Table

```sql
reports {
  id UUID PRIMARY KEY
  query TEXT
  mode ENUM("quick","deep")
  summary TEXT
  goals TEXT
  methodology TEXT
  findings TEXT
  competitors TEXT
  risks TEXT
  opportunities TEXT
  recommendations TEXT
  confidence_score FLOAT
  created_at TIMESTAMP
}
```

### Sources Table

```sql
sources {
  id UUID PRIMARY KEY
  report_id UUID FOREIGN KEY -> reports.id
  url TEXT
  reliability FLOAT
  domain TEXT
  source_type ENUM("gov","academic","media","blog","forum","unknown")
  published_at TIMESTAMP NULL
}
```

### Execution Logs

```sql
logs {
  id UUID PRIMARY KEY
  report_id UUID FOREIGN KEY -> reports.id
  stage TEXT
  message TEXT
  timestamp TIMESTAMP
  status ENUM("running","ok","warning","error")
}
```

### Storage Philosophy

- Append-only logs
- Immutable reports once finalized
- Soft delete later if needed

---

## Migration Plan — SQLite → Postgres (Neon)

### Philosophy

Zero redesign. Only upgrade storage layer.

### Steps

1. Design schema with SQL portability
2. Ensure UUID instead of int IDs
3. Use migration framework
4. Abstract DB through DAL layer
5. Switch connection target later

### Must Stay True

- Same tables
- Same fields
- Same types conceptually
- No vendor-locked constraints

---

## API Specification (Future SaaS)

### Philosophy

Public API will allow:
- Trigger research
- Retrieve results
- Fetch logs
- Manage exports

### Endpoints (Draft)

#### POST /research
Start research request.

#### GET /research/{id}
Fetch structured report.

#### GET /research/{id}/logs
Streaming logs / historical logs.

#### POST /export/{id}
Trigger export actions.

### Security

- Authentication: bearer token
- Rate limiting required in SaaS mode

---

## Monorepo Code Structure — FastAPI + Next.js

Goal:
- Clear separation of concerns
- Backend as the single source of truth
- Frontend as a pure consumer
- Agent-safe, scalable layout

### Repository Layout

```
/deep-research-assistant
│
├── backend/                    # FastAPI backend (SOURCE OF TRUTH)
│   ├── app/
│   │   ├── api/
│   │   │   ├── main.py          # FastAPI entrypoint
│   │   │   ├── routes/
│   │   │   │   ├── research.py  # start / stop / status
│   │   │   │   ├── logs.py      # live + stored logs
│   │   │   │   └── export.py    # md / email export
│   │   │   ├── schemas.py       # Pydantic request/response models
│   │   │   └── deps.py          # dependencies (DB, config)
│   │   │
│   │   ├── agents/
│   │   │   ├── planner_agent.py
│   │   │   ├── search_agent.py
│   │   │   ├── writer_agent.py
│   │   │   └── reviewer_agent.py  # future
│   │   │
│   │   ├── core/
│   │   │   ├── orchestrator.py
│   │   │   ├── settings.py
│   │   │   ├── logger.py
│   │   │   └── retry.py
│   │   │
│   │   ├── search/
│   │   │   ├── api_search.py
│   │   │   ├── openai_search.py
│   │   │   └── scraper.py
│   │   │
│   │   ├── data/
│   │   │   ├── db.py
│   │   │   ├── models.py
│   │   │   └── migrations/
│   │   │
│   │   └── workers/
│   │       └── research_task.py  # background execution
│   │
│   ├── tests/
│   │   ├── test_pipeline.py
│   │   ├── test_agents.py
│   │   └── test_api.py
│   │
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                   # Next.js application
│   ├── app/                    # App Router
│   │   ├── page.tsx            # dashboard
│   │   ├── research/
│   │   │   └── [id]/page.tsx   # research viewer
│   │   ├── api/                # frontend-only API (auth, proxy)
│   │   │   └── proxy/          # optional backend proxy routes
│   │   └── layout.tsx
│   │
│   ├── components/
│   │   ├── LogsPanel.tsx
│   │   ├── ReportViewer.tsx
│   │   ├── ModeSelector.tsx
│   │   └── ExportButtons.tsx
│   │
│   ├── lib/
│   │   ├── api.ts              # FastAPI client
│   │   │   └── fetch wrapper
│   │   └── types.ts            # mirrors backend schemas
│   │
│   ├── styles/
│   ├── public/
│   ├── package.json
│   └── README.md
│
├── shared/                     # Shared contracts (IMPORTANT)
│   ├── schemas/                # OpenAPI / JSON Schema
│   └── constants/
│
├── docs/                       # Project documentation
│   ├── project_spec.md         # This file
│   ├── AGENT_INSTRUCTIONS.md
│   └── ...
│
├── AGENT_SYSTEM_PROMPT.txt
├── docker-compose.yml
├── .env.example
└── README.md
```

### Architectural Rules

#### Backend (FastAPI)
- Source of truth for business logic
- Owns agents, orchestration, persistence
- Exposes clean, versioned APIs
- No frontend logic

#### Frontend (Next.js)
- UI only
- Never contains research logic
- Consumes FastAPI via HTTP
- Uses shared schemas for type safety

#### Shared
- Prevents contract drift
- Enables OpenAPI → TypeScript generation

### Why This Structure Works

- Clear mental model for humans and agents
- Scales from MVP to SaaS
- Safe for autonomous coding agents
- Supports background jobs and streaming later
- Easy CI/CD separation

### Migration Safety

This layout supports:
- SQLite → Postgres (Neon)
- Gradio → Next.js
- Open-source core → SaaS

No structural rewrite required.

---

## Next.js UI Plan

### Goal

Move from Gradio → professional frontend UI.

### Core UI Concepts

- Dashboard layout
- Live logs pane
- Structured result viewer
- Download/export controls
- Mode selector
- Search configuration panel

### Architecture

- **Next.js** (App Router)
- **Tailwind** for styling
- **Shadcn UI** for components
- API to backend

### Design Guidelines

#### Visual Style
- Clean, minimal interface — the research report is the star
- Use Shadcn components for consistency
- Responsive design (mobile-first)
- No dark mode for MVP

#### Copy Tone
- Professional yet approachable
- Brief labels and instructions
- Helpful error messages that suggest next steps
- Clear status updates during research execution

#### Component Patterns
- **Shadcn UI** for all interactive elements (buttons, inputs, cards, dialogs)
- **Tailwind** for layout and spacing
- Keep components focused and small

### Phased Approach

**Phase 1**:
- Replicate Gradio functionality

**Phase 2**:
- Improved UX
- Persistent user settings

**Phase 3**:
- SaaS UI capabilities

---

## Prompt Engineering Standards

All LLM agent prompts **MUST**:
- Specify role, goal, constraints, output format
- Never allow free-form output without schema
- Always request uncertainty marking

### Planner Prompt Rules
- Focus on strategy, not answers
- Output structured plan only
- No speculation

### Search Agent Prompt Rules
- Focus on discovery and extraction
- No synthesis
- Preserve source URLs

### Writer Prompt Rules
- Synthesize only from provided inputs
- Enforce report schema
- Mark weak evidence explicitly

### Reviewer Prompt Rules (Future)
- Verify claims vs sources
- Flag unsupported statements
- No rewriting unless explicitly requested

---

## Engineering Roadmap

### Phase 1 — MVP Core (Current)

- [ ] Setup SQLite persistence
- [ ] Implement structured research pipeline
- [ ] Implement confidence heuristic
- [ ] Implement live logs
- [ ] Add stop + reset control
- [ ] Export .md + email system
- [ ] Partial results logic
- [ ] Quick vs Deep mode behavior

### Phase 2 — Stability + UX

- [ ] Improve heuristics
- [ ] Add source quality tiers
- [ ] Improve logging clarity
- [ ] Add UI improvements
- [ ] Add user setting persistence

### Phase 3 — Reviewer System (V1)

- [ ] Anti-hallucination evaluator
- [ ] Reviewer LLM toggle system
- [ ] Debate mode engine
- [ ] User-facing audit summary

### Phase 4 — Platform Evolution

- [ ] Database migration to Neon
- [ ] Move UI to Next.js
- [ ] API layer design
- [ ] Optional SaaS features

### Performance Defaults

**Sources**:
- Quick: 4–6
- Deep: 10–14
- Hard Cap: 20

**Runtime**:
- Quick: 1–2 min
- Deep: 5–8 min

# DeepTrace

DeepTrace is a professional AI Research Assistant built on the OpenAI Agents SDK. It intelligently plans web searches, synthesizes information from multiple sources, and produces comprehensive Markdown reports. The system features dual research modes (Quick and Deep), database persistence, and optional email delivery.

## Features

- **Multi-Agent System**: Orchestrated workflow with specialized AI agents
- **Dual Research Modes**: Quick (4-6 sources, ~2 min) or Deep (10-14 sources, ~8 min)
- **Smart Planning**: Mode-aware search strategy generation (`backend/app/agents/planner_agent.py`)
- **Parallel Search**: Concurrent web searches with result summarization (`backend/app/agents/search_agent.py`)
- **Report Synthesis**: Structured 11-field reports with confidence scoring (`backend/app/agents/writer_agent.py`)
- **Database Persistence**: SQLite storage for reports, sources, and logs (`backend/app/data/db.py`)
- **Export Options**: Markdown file export and optional email delivery (`backend/app/agents/email_agent.py`)
- **Query Clarification**: Automatic detection of vague queries with clarifying questions (`backend/app/agents/clarifying_agent.py`)
- **Gradio UI**: Interactive web interface with live execution logs

## Requirements

- Python 3.10+ recommended
- An OpenAI API key (`OPENAI_API_KEY`)
- Network access (the web-search tool and model calls require it)

## Setup

1. Create and activate a virtual environment.

   **Windows (PowerShell):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS/Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and set at least `OPENAI_API_KEY`.

## Run

Start the Gradio UI:

```bash
python app.py
```

This launches Gradio and opens a browser window (`inbrowser=True`). Select your research mode (Quick or Deep), enter your query, and click Run. The UI updates with live execution logs and displays the final Markdown report. Use the Export button to save reports as `.md` files in the `exports/` directory.

## Email (optional)

If `SENDGRID_API_KEY` is not set, emailing is skipped automatically.

To enable email sending, set:

- `SENDGRID_API_KEY`
- `SENDGRID_FROM` (must be a verified sender/domain in many SendGrid setups)
- `SENDGRID_TO`
- `SENDGRID_DEFAULT_SUBJECT` (optional)

## Project Structure

```
DeepTrace/
├── app.py                      # Gradio UI entry point
├── .env.example               # Environment variables template
├── CLAUDE.md                  # AI assistant instructions
├── README.md                  # This file
│
├── backend/                   # Backend application
│   ├── app/
│   │   ├── agents/           # AI agents
│   │   │   ├── planner_agent.py      # Search strategy planner
│   │   │   ├── search_agent.py       # Web search executor
│   │   │   ├── writer_agent.py       # Report synthesizer
│   │   │   ├── email_agent.py        # Email delivery
│   │   │   └── clarifying_agent.py   # Query clarification
│   │   ├── core/             # Core business logic
│   │   │   ├── orchestrator.py       # ResearchManager orchestration
│   │   │   ├── types.py              # ResearchMode enum & config
│   │   │   ├── confidence.py         # Confidence scoring
│   │   │   ├── retry.py              # Retry logic with backoff
│   │   │   └── monitoring.py         # Performance tracking
│   │   └── data/             # Database layer
│   │       └── db.py                 # SQLite CRUD operations
│   ├── tests/                # Test suite
│   └── requirements.txt      # Python dependencies
│
├── data/                     # Local data storage (gitignored)
│   └── research.db          # SQLite database
│
├── docs/                     # Documentation
│   ├── project_spec.md      # Full project specifications
│   ├── architecture.md      # System design
│   └── ...                  # Additional docs
│
└── exports/                  # Exported reports (gitignored)
```

## Architecture

DeepTrace follows a **multi-agent architecture** with clear separation of concerns:

1. **Orchestration Layer** (`backend/app/core/orchestrator.py`)
   - Manages the research pipeline
   - Handles retries, errors, and partial results
   - Provides live status updates to UI

2. **Agent Layer** (`backend/app/agents/`)
   - Specialized AI agents for each task
   - Stateless and composable
   - Uses OpenAI Agents SDK

3. **Data Layer** (`backend/app/data/`)
   - SQLite persistence (PostgreSQL-ready)
   - Stores reports, sources, and execution logs
   - Migration-ready for production scaling

See [`docs/architecture.md`](docs/architecture.md) for detailed system design and [`docs/project_spec.md`](docs/project_spec.md) for full specifications.

## Development

- **Documentation**: See [`CLAUDE.md`](CLAUDE.md) for development guidelines and agent instructions
- **Testing**: Run tests from `backend/tests/` directory

## Notes

- `.env` is gitignored; keep API keys out of source control
- Database files in `data/` are gitignored
- Exported reports in `exports/` are gitignored
- OpenAI trace links printed to console for debugging: `https://platform.openai.com/traces/trace?trace_id={trace_id}`

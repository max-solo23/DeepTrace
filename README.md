# DeepTrace

DeepTrace is a small "deep research" app built on the OpenAI Agents SDK. It plans a few web searches, summarizes results, writes a long-form Markdown report, and (optionally) emails the report via SendGrid. A simple Gradio UI lets you run the flow interactively.

## What it does

- Plans a short search strategy from your query (`planner_agent.py`)
- Runs web searches and summarizes each result (`search_agent.py`)
- Synthesizes a detailed Markdown report (`writer_agent.py`)
- Optionally emails the report if SendGrid is configured (`email_agent.py`)
- Prints an OpenAI trace link for each run (`research_manager.py`)

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
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and set at least `OPENAI_API_KEY`.

## Run

Start the Gradio UI:

```bash
python deep_research.py
```

This launches Gradio and opens a browser window (`inbrowser=True`). As the run progresses, the UI updates with status messages and finally the generated Markdown report.

## Email (optional)

If `SENDGRID_API_KEY` is not set, emailing is skipped automatically.

To enable email sending, set:

- `SENDGRID_API_KEY`
- `SENDGRID_FROM` (must be a verified sender/domain in many SendGrid setups)
- `SENDGRID_TO`
- `SENDGRID_DEFAULT_SUBJECT` (optional)

## Project layout

- `deep_research.py` — Gradio UI entrypoint
- `research_manager.py` — Orchestrates plan → search → write → email; yields UI updates
- `planner_agent.py` — Produces a small `WebSearchPlan` (default: 3 searches)
- `search_agent.py` — Uses `WebSearchTool` to retrieve and summarize results
- `writer_agent.py` — Produces `ReportData` including the final Markdown report
- `email_agent.py` — Converts the report to HTML and sends via SendGrid

## Notes

- `.env` is gitignored; keep keys out of source control.

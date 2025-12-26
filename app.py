import gradio as gr
import asyncio
from dotenv import load_dotenv
from backend.app.core.orchestrator import ResearchManager
from backend.app.core import ResearchMode
from backend.app.data import init_db
from datetime import datetime
from pathlib import Path


load_dotenv(override=True)

# Initialize database
print("Initializing database...")
try:
    init_db()
    print("✓ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization failed: {e}")
    print("   Research will continue but reports won't be saved")

# Create singleton manager instance
manager = ResearchManager()

# Store the last generated report for export
last_report = {"content": None, "query": None}


async def run(query: str, mode: str):
    """Run research with selected mode.

    Args:
        query: Research query
        mode: Research mode ("Quick" or "Deep")

    Yields:
        Status updates and final report
    """
    global last_report

    # Convert UI mode string to ResearchMode enum
    research_mode = ResearchMode.QUICK if mode == "Quick" else ResearchMode.DEEP

    # Manager already handles CancelledError, just propagate the yields
    full_output = ""
    async for chunk in manager.run(query, mode=research_mode):
        full_output = chunk  # Keep updating with latest chunk
        yield chunk

    # Store the final report for export (last chunk is the full markdown report)
    if full_output and len(full_output) > 100:  # Ensure it's the actual report
        last_report["content"] = full_output
        last_report["query"] = query


def stop_research() -> str:
    """Stop the current research operation."""
    manager.request_stop()
    return "Stopping research at next checkpoint..."


def export_report() -> str:
    """Export the last generated report as a markdown file.

    Returns:
        Path to the exported file, or None if no report available
    """
    global last_report

    if not last_report["content"]:
        return None

    # Create exports directory if it doesn't exist
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp and sanitized query
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_slug = last_report["query"][:50].replace(" ", "_").replace("/", "_") if last_report["query"] else "report"
    # Remove invalid filename characters
    query_slug = "".join(c for c in query_slug if c.isalnum() or c in ('_', '-'))
    filename = f"research_{query_slug}_{timestamp}.md"
    filepath = exports_dir / filename

    # Write the report to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(last_report["content"])
        print(f"Report exported to: {filepath}")
        return str(filepath)
    except Exception as e:
        print(f"Export failed: {e}")
        return None


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    gr.Markdown("""
    **Research Modes:**
    - **Quick**: Faster research with 4-6 sources (~2 minutes)
    - **Deep**: Comprehensive research with 10-14 sources (~8 minutes)
    """)

    query_textbox = gr.Textbox(
        label="What topic would you like to research?",
        placeholder="Enter your research query..."
    )

    mode_radio = gr.Radio(
        choices=["Quick", "Deep"],
        value="Quick",
        label="Research Mode",
        info="Choose between quick research (4-6 sources) or deep research (10-14 sources)"
    )

    with gr.Row():
        run_button = gr.Button("Run", variant="primary")
        stop_button = gr.Button("Stop", variant="stop")
        export_button = gr.Button("📥 Export", variant="secondary")

    report = gr.Markdown(label="Report")

    # File output for download
    export_file = gr.File(label="Exported Report", visible=False)

    run_button.click(fn=run, inputs=[query_textbox, mode_radio], outputs=report)
    query_textbox.submit(fn=run, inputs=[query_textbox, mode_radio], outputs=report)
    stop_button.click(fn=stop_research, outputs=report)
    export_button.click(fn=export_report, outputs=export_file)

ui.launch(inbrowser=True)
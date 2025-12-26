import gradio as gr
import asyncio
import os
from dotenv import load_dotenv
from backend.app.core.orchestrator import ResearchManager
from backend.app.core import ResearchMode
from backend.app.data import init_db
from datetime import datetime
from pathlib import Path


load_dotenv(override=True)

# Store default values from environment
DEFAULT_OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
DEFAULT_SERPER_KEY = os.environ.get("SERPER_API_KEY", "")
DEFAULT_SENDGRID_KEY = os.environ.get("SENDGRID_API_KEY", "")
DEFAULT_SENDGRID_FROM = os.environ.get("SENDGRID_FROM", "")
DEFAULT_SENDGRID_TO = os.environ.get("SENDGRID_TO", "")

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


async def run(
    query: str,
    mode: str,
    send_email: bool,
    search_provider: str,
    openai_key: str,
    serper_key: str,
    sendgrid_key: str,
    sendgrid_from: str,
    sendgrid_to: str
):
    """Run research with selected mode and configuration.

    Args:
        query: Research query
        mode: Research mode ("Quick" or "Deep")
        send_email: Whether to send email after completion
        search_provider: Web search provider ("OpenAI" or "Serper")
        openai_key: OpenAI API key
        serper_key: Serper API key
        sendgrid_key: SendGrid API key
        sendgrid_from: SendGrid from email
        sendgrid_to: SendGrid to email

    Yields:
        Status updates and final report
    """
    global last_report

    # Temporarily set environment variables based on user input
    # Store original values to restore later
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "SERPER_API_KEY": os.environ.get("SERPER_API_KEY"),
        "SENDGRID_API_KEY": os.environ.get("SENDGRID_API_KEY"),
        "SENDGRID_FROM": os.environ.get("SENDGRID_FROM"),
        "SENDGRID_TO": os.environ.get("SENDGRID_TO"),
    }

    try:
        # Set API keys from user input
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
        if serper_key:
            os.environ["SERPER_API_KEY"] = serper_key

        # Set SendGrid config only if email is enabled
        if send_email:
            if sendgrid_key:
                os.environ["SENDGRID_API_KEY"] = sendgrid_key
            if sendgrid_from:
                os.environ["SENDGRID_FROM"] = sendgrid_from
            if sendgrid_to:
                os.environ["SENDGRID_TO"] = sendgrid_to
        else:
            # Clear SendGrid key to prevent email sending
            os.environ.pop("SENDGRID_API_KEY", None)

        # Set search provider preference (for future use)
        os.environ["SEARCH_PROVIDER"] = search_provider.lower()

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

    finally:
        # Restore original environment variables
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)


async def run_with_status(
    query: str,
    mode: str,
    send_email: bool,
    search_provider: str,
    openai_key: str,
    serper_key: str,
    sendgrid_key: str,
    sendgrid_from: str,
    sendgrid_to: str
):
    """
    Wrapper around run() that also updates the status indicator.

    Yields:
        Tuple of (status, report) for simultaneous updates
    """
    # Initial status
    yield "🔄 Running research...", ""

    try:
        async for chunk in run(
            query, mode, send_email, search_provider,
            openai_key, serper_key, sendgrid_key,
            sendgrid_from, sendgrid_to
        ):
            # Keep showing "running" status while research progresses
            yield "🔄 Running research...", chunk

        # Research completed successfully
        yield "✅ Research complete", chunk

    except asyncio.CancelledError:
        # User stopped the research
        yield "⚠️ Stopped by user", chunk

    except Exception as e:
        # Error occurred
        yield f"❌ Error: {type(e).__name__}", chunk


def stop_research() -> tuple[str, str]:
    """Stop the current research operation."""
    manager.request_stop()
    return "⚠️ Stopping...", "Stopping research at next checkpoint..."


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

    # Configuration section
    with gr.Accordion("⚙️ Configuration", open=False):
        gr.Markdown("### API Keys")

        openai_key_input = gr.Textbox(
            label="OpenAI API Key",
            placeholder="sk-...",
            value=DEFAULT_OPENAI_KEY,
            type="password",
            info="Required for AI agents and OpenAI web search"
        )

        gr.Markdown("### Web Search Provider")
        search_provider_radio = gr.Radio(
            choices=["OpenAI", "Serper"],
            value="OpenAI",
            label="Search Provider",
            info="Choose which search API to use"
        )

        serper_key_input = gr.Textbox(
            label="Serper API Key",
            placeholder="Enter Serper API key...",
            value=DEFAULT_SERPER_KEY,
            type="password",
            visible=False,
            info="Required when using Serper search provider"
        )

        gr.Markdown("### Email Settings")
        send_email_checkbox = gr.Checkbox(
            label="Send Email Report",
            value=False,
            info="Send the completed report via email"
        )

        sendgrid_key_input = gr.Textbox(
            label="SendGrid API Key",
            placeholder="SG...",
            value=DEFAULT_SENDGRID_KEY,
            type="password",
            visible=False,
            info="Required for email delivery"
        )

        sendgrid_from_input = gr.Textbox(
            label="From Email",
            placeholder="research@example.com",
            value=DEFAULT_SENDGRID_FROM,
            visible=False,
            info="Sender email (must be verified in SendGrid)"
        )

        sendgrid_to_input = gr.Textbox(
            label="To Email",
            placeholder="recipient@example.com",
            value=DEFAULT_SENDGRID_TO,
            visible=False,
            info="Recipient email address"
        )

    with gr.Row():
        run_button = gr.Button("Run", variant="primary")
        stop_button = gr.Button("Stop", variant="stop")
        export_button = gr.Button("📥 Export", variant="secondary")

    # Status indicator
    status_box = gr.Textbox(
        label="Status",
        value="Ready",
        interactive=False,
        max_lines=1
    )

    report = gr.Markdown(label="Report")

    # File output for download
    export_file = gr.File(label="Exported Report", visible=False)

    # Dynamic visibility for conditional fields
    def update_serper_visibility(provider):
        return gr.update(visible=(provider == "Serper"))

    def update_email_fields_visibility(send_email):
        return [gr.update(visible=send_email)] * 3  # Show/hide all 3 email fields

    search_provider_radio.change(
        fn=update_serper_visibility,
        inputs=[search_provider_radio],
        outputs=[serper_key_input]
    )

    send_email_checkbox.change(
        fn=update_email_fields_visibility,
        inputs=[send_email_checkbox],
        outputs=[sendgrid_key_input, sendgrid_from_input, sendgrid_to_input]
    )

    # Wire up the run button with all inputs
    run_inputs = [
        query_textbox,
        mode_radio,
        send_email_checkbox,
        search_provider_radio,
        openai_key_input,
        serper_key_input,
        sendgrid_key_input,
        sendgrid_from_input,
        sendgrid_to_input
    ]

    # Run button outputs to both status and report
    run_button.click(fn=run_with_status, inputs=run_inputs, outputs=[status_box, report])
    query_textbox.submit(fn=run_with_status, inputs=run_inputs, outputs=[status_box, report])

    # Stop button updates both status and report
    stop_button.click(fn=stop_research, outputs=[status_box, report])

    # Export button only affects the file output
    export_button.click(fn=export_report, outputs=export_file)

ui.launch(inbrowser=True)
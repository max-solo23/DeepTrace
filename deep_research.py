import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from backend.core import ResearchMode


load_dotenv(override=True)


async def run(query: str, mode: str):
    """Run research with selected mode.

    Args:
        query: Research query
        mode: Research mode ("Quick" or "Deep")

    Yields:
        Status updates and final report
    """
    # Convert UI mode string to ResearchMode enum
    research_mode = ResearchMode.QUICK if mode == "Quick" else ResearchMode.DEEP

    async for chunk in ResearchManager().run(query, mode=research_mode):
        yield chunk


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

    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")

    run_button.click(fn=run, inputs=[query_textbox, mode_radio], outputs=report)
    query_textbox.submit(fn=run, inputs=[query_textbox, mode_radio], outputs=report)

ui.launch(inbrowser=True)
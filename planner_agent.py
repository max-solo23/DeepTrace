from pydantic import BaseModel, Field
from agents import Agent
from backend.core import ResearchMode, get_mode_config


def get_instructions(mode: ResearchMode) -> str:
    """Generate instructions for planner agent based on research mode.

    Args:
        mode: The research mode (QUICK or DEEP)

    Returns:
        Instructions string with appropriate search count
    """
    config = get_mode_config(mode)
    min_sources = config["min_sources"]
    max_sources = config["max_sources"]
    mode_desc = config["description"]

    return f"""You are a helpful research assistant operating in {mode.value.upper()} mode ({mode_desc}).

Given a user query, generate a comprehensive set of web searches to best answer the query.

You should output between {min_sources} and {max_sources} search terms.

Each search should:
- Target a specific aspect or angle of the query
- Use effective search keywords
- Avoid redundancy with other searches
- Be diverse to gather comprehensive information

Prioritize quality and diversity of sources over quantity."""

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")


def create_planner_agent(mode: ResearchMode) -> Agent:
    """Create a planner agent configured for the specified research mode.

    Args:
        mode: Research mode to configure agent for

    Returns:
        Configured Agent instance
    """
    instructions = get_instructions(mode)
    print(f"[PLANNER] Creating planner agent for {mode.value} mode")

    return Agent(
        name="PlannerAgent",
        instructions=instructions,
        model="gpt-5-nano",
        output_type=WebSearchPlan,
    )
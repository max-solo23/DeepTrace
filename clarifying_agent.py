"""
Clarifying Agent

Detects vague or ambiguous queries and generates clarifying questions
to help refine the research scope.

This agent is optional and should be used when:
- Query is very short or generic
- Query lacks context or specificity
- Deep mode is enabled (more time for clarification)
"""

from pydantic import BaseModel, Field
from agents import Agent


INSTRUCTIONS = """You are a research clarification specialist. Your job is to analyze research queries and determine if they need clarification.

Given a research query, you should:

1. **Assess Clarity**: Determine if the query is specific enough for effective research
   - Clear queries: specific topic, clear intent, well-defined scope
   - Vague queries: too broad, ambiguous terms, missing context

2. **Generate Clarifying Questions** (if needed):
   - Ask 2-3 focused questions that would help narrow the scope
   - Questions should be specific and actionable
   - Avoid yes/no questions - ask for details
   - Focus on: purpose, scope, constraints, specific interests

3. **Examples of Vague Queries**:
   - "AI" (too broad - what aspect of AI?)
   - "Best practices" (for what? in what context?)
   - "Market research" (which market? what product?)
   - "Latest trends" (in what field?)

4. **Examples of Clear Queries**:
   - "What are the best practices for implementing OAuth 2.0 in Node.js applications?"
   - "How does Tesla's battery technology compare to traditional EV manufacturers in 2024?"
   - "What are the current FDA regulations for clinical trials of mRNA vaccines?"

5. **Output**:
   - Set `needs_clarification` to True if query is vague
   - Provide 2-3 clarifying questions
   - Keep questions brief and focused
   - If query is clear, set `needs_clarification` to False and questions can be empty

Remember: Only request clarification when it would genuinely improve research quality. Don't over-clarify specific queries.
"""


class ClarificationResult(BaseModel):
    needs_clarification: bool = Field(
        description="True if the query is too vague and needs clarification, False if it's specific enough"
    )

    clarifying_questions: list[str] = Field(
        default_factory=list,
        description="2-3 focused questions to help narrow down the research scope. Empty if needs_clarification is False."
    )

    reasoning: str = Field(
        description="Brief explanation of why clarification is or isn't needed"
    )


clarifying_agent = Agent(
    name="ClarifyingAgent",
    instructions=INSTRUCTIONS,
    model="gpt-5-nano",
    output_type=ClarificationResult,
)


async def check_if_needs_clarification(query: str) -> ClarificationResult:
    """
    Check if a query needs clarification.

    Args:
        query: The research query to analyze

    Returns:
        ClarificationResult indicating if clarification is needed and what questions to ask

    Example:
        from agents import Runner

        result = await Runner.run(clarifying_agent, f"Query to analyze: {query}")
        clarification = result.final_output_as(ClarificationResult)

        if clarification.needs_clarification:
            print("This query needs clarification:")
            for question in clarification.clarifying_questions:
                print(f"  - {question}")
    """
    from agents import Runner

    result = await Runner.run(
        clarifying_agent,
        f"Query to analyze: {query}"
    )

    return result.final_output_as(ClarificationResult)

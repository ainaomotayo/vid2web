from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from ..prompts.generation_prompts import ARCHITECTURE_INSTRUCTION
from ..tools.architecture_tools import save_page_structure

architecture_agent = Agent(
    name="architecture_agent",
    model=Gemini(model="gemini-3-flash-preview"),
    description="Creates the information architecture and site structure",
    instruction=ARCHITECTURE_INSTRUCTION + "\n\nIMPORTANT: You MUST use the `save_page_structure` tool to save your plan.",
    tools=[save_page_structure],
    output_key="site_architecture",
)

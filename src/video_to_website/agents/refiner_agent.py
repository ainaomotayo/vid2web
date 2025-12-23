from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from ..tools.refinement_tools import apply_code_fixes
from ..prompts.validation_prompts import REFINEMENT_INSTRUCTION

refiner_agent = Agent(
    name="refiner_agent",
    model=Gemini(model="gemini-2.5-flash"),
    description="Applies fixes and improvements based on validation feedback",
    instruction=REFINEMENT_INSTRUCTION,
    tools=[apply_code_fixes],
    output_key="refinement_results",
)

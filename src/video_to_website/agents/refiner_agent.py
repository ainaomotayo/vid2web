from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from ..prompts.validation_prompts import REFINEMENT_INSTRUCTION

refiner_agent = Agent(
    name="refiner_agent",
    model=Gemini(model="gemini-2.5-flash"),
    description="Applies fixes and improvements based on validation feedback",
    instruction=REFINEMENT_INSTRUCTION,
    output_key="refinement_actions",
)

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from ..tools.validation_tools import (
    validate_accessibility,
    check_responsive_layout,
    launch_browser_preview,
    measure_performance,
)
from ..tools.loop_tools import check_validation_status
from ..prompts.validation_prompts import VALIDATION_INSTRUCTION

validator_agent = Agent(
    name="validator_agent",
    model=Gemini(model="gemini-2.5-flash"),
    description="Performs automated testing on the generated website",
    instruction=VALIDATION_INSTRUCTION,
    tools=[
        validate_accessibility,
        check_responsive_layout,
        launch_browser_preview,
        measure_performance,
        check_validation_status,
    ],
    output_key="validation_results",
)

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from ..tools.validation_tools import (
    launch_browser_preview,
    capture_screenshot,
    validate_accessibility,
    check_responsive_layout,
    measure_performance,
)
from ..prompts.validation_prompts import VALIDATION_INSTRUCTION

validator_agent = Agent(
    name="validator_agent",
    model=Gemini(model="gemini-2.5-flash"),
    description="Performs automated testing using Agents for browser automation",
    instruction=VALIDATION_INSTRUCTION,
    tools=[
        launch_browser_preview,
        capture_screenshot,
        validate_accessibility,
        check_responsive_layout,
        measure_performance,
    ],
    output_key="validation_results",
)

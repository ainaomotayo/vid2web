from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from ..tools.code_tools import generate_html, generate_css, generate_javascript
from ..tools.file_tools import save_artifact
from ..prompts.generation_prompts import CODE_GENERATION_INSTRUCTION

code_generator_agent = Agent(
    name="code_generator",
    model=Gemini(model="gemini-3-flash-preview"),
    description="Generates production-ready HTML, CSS, and JavaScript",
    instruction=CODE_GENERATION_INSTRUCTION,
    tools=[generate_html, generate_css, generate_javascript, save_artifact],
    output_key="generated_code",
)

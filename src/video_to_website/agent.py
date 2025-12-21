from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent
from google.adk.models.google_llm import Gemini
from google.adk.apps import App
from google.adk.plugins import ReflectAndRetryToolPlugin
from google.genai import types

from .agents.video_analyzer import video_analyzer_agent
from .agents.content_extractor import content_extractor_agent
from .agents.architecture_agent import architecture_agent
from .agents.code_generator import code_generator_agent
from .agents.validator_agent import validator_agent
from .agents.refiner_agent import refiner_agent
from .plugins.model_fallback_plugin import ModelFallbackPlugin
from .plugins.stagger_plugin import StaggerPlugin

# Use Gemini 2.5 Flash for better parallel throughput
MODEL_NAME = "gemini-2.5-flash"

# Configure retry options for robustness against quota limits
retry_options = types.HttpRetryOptions(
    attempts=5,
    initial_delay=1.0,
    max_delay=60.0,
    exp_base=2.0,  # Multiplier
    http_status_codes=[429, 500, 503, 504]
)

# Configure HTTP timeout
http_options = types.HttpOptions(
    timeout=300.0  # 300 seconds
)

# Create a shared GenerateContentConfig
generate_config = types.GenerateContentConfig(
    http_options=http_options
)

# Update models for all sub-agents with retry and http configuration
video_analyzer_agent.model = Gemini(model=MODEL_NAME, retry_options=retry_options, config=generate_config)
content_extractor_agent.model = Gemini(model=MODEL_NAME, retry_options=retry_options, config=generate_config)
architecture_agent.model = Gemini(model=MODEL_NAME, retry_options=retry_options, config=generate_config)
code_generator_agent.model = Gemini(model=MODEL_NAME, retry_options=retry_options, config=generate_config)
validator_agent.model = Gemini(model=MODEL_NAME, retry_options=retry_options, config=generate_config)
refiner_agent.model = Gemini(model=MODEL_NAME, retry_options=retry_options, config=generate_config)


# Analysis phase runs video and content extraction in parallel
analysis_agent = ParallelAgent(
    name="analysis_phase",
    description="Parallel analysis of video and content",
    sub_agents=[video_analyzer_agent, content_extractor_agent],
)

# Validation loop for iterative refinement
validation_loop = LoopAgent(
    name="validation_refinement",
    description="Iteratively validate and refine generated code",
    sub_agents=[validator_agent, refiner_agent],
    max_iterations=5,
)

# Main orchestrator
root_agent = SequentialAgent(
    name="website_generator",
    description="Transforms video walkthroughs into functional websites",
    sub_agents=[
        analysis_agent,      # Populates: video_analysis_results, content_extraction_results
        architecture_agent,  # Uses above, Populates: site_architecture (via tool)
        code_generator_agent,# Uses above, Populates: generated_html, generated_css, generated_js
        validation_loop,     # Uses generated code, Populates: validation_results
    ],
)

# Define the application with plugins
app = App(
    name="video_to_website",
    root_agent=root_agent,
    plugins=[
        ModelFallbackPlugin(),
        ReflectAndRetryToolPlugin(max_retries=3),
        StaggerPlugin(min_delay=5.0, max_delay=15.0), # Add stagger plugin
    ],
)

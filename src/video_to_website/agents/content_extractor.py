from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from ..tools.video_tools import extract_audio_transcript
from ..prompts.analysis_prompts import CONTENT_EXTRACTION_INSTRUCTION

content_extractor_agent = Agent(
    name="content_extractor",
    model=Gemini(model="gemini-2.5-flash"),
    description="Extracts textual content and information structure from audio/video",
    instruction=CONTENT_EXTRACTION_INSTRUCTION,
    tools=[extract_audio_transcript],
    output_key="content_extraction_results",
)

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from ..tools.video_tools import analyze_video_frames, extract_and_save_images_from_video
from ..prompts.analysis_prompts import VIDEO_ANALYSIS_INSTRUCTION

video_analyzer_agent = Agent(
    name="video_analyzer",
    model=Gemini(model="gemini-2.5-flash"),
    description="Analyzes video frames to extract design intent and visual patterns",
    instruction=VIDEO_ANALYSIS_INSTRUCTION,
    tools=[analyze_video_frames, extract_and_save_images_from_video],
    output_key="video_analysis_results",
)

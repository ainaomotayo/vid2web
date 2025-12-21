from __future__ import annotations

import logging
import os
import time
import re
import json
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from google.adk.tools import ToolContext
from dotenv import load_dotenv

# Try to import yt_dlp for YouTube downloading
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

# Try to import dirtyjson for robust JSON parsing
try:
    import dirtyjson
    from dirtyjson.attributed_containers import AttributedDict, AttributedList
    DIRTYJSON_AVAILABLE = True
except ImportError:
    DIRTYJSON_AVAILABLE = False

logger = logging.getLogger(__name__)
load_dotenv()

def _is_youtube_url(url: str) -> bool:
    """Checks if the given string is a YouTube URL."""
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(re.match(youtube_regex, url))


def _download_youtube_video(url: str, output_path: Path) -> Path:
    """Downloads a YouTube video to the specified path."""
    if not YT_DLP_AVAILABLE:
        raise ImportError("yt-dlp is required to download YouTube videos. Please install it with `pip install yt-dlp`.")

    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': str(output_path),
        'quiet': True,
    }
    
    logger.info(f"Downloading YouTube video: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return output_path


def _upload_file(client: genai.Client, path: Path) -> types.File:
    """Uploads a file to the Gemini Files API."""
    logger.info(f"Uploading file: {path}")
    file = client.files.upload(file=path)
    
    # Wait for processing if it's a video
    while file.state.name == "PROCESSING":
        logger.info("Waiting for video processing...")
        time.sleep(2)
        file = client.files.get(name=file.name)
        
    if file.state.name == "FAILED":
        raise ValueError(f"File processing failed: {file.error.message}")
        
    logger.info(f"File uploaded and processed: {file.name}")
    return file

def _convert_dirty_json(data: Any) -> Any:
    """Recursively converts dirtyjson types to standard Python types."""
    if not DIRTYJSON_AVAILABLE:
        return data
        
    if isinstance(data, AttributedDict):
        return {k: _convert_dirty_json(v) for k, v in data.items()}
    elif isinstance(data, AttributedList):
        return [_convert_dirty_json(i) for i in data]
    elif isinstance(data, dict):
        return {k: _convert_dirty_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_convert_dirty_json(i) for i in data]
    else:
        return data

def _parse_json_response(text: str) -> dict[str, Any]:
    """Parses a JSON response from the LLM, handling potential markdown wrapping and list outputs."""
    # Strip markdown code blocks
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    parsed_data = None
    try:
        if DIRTYJSON_AVAILABLE:
            parsed_data = dirtyjson.loads(text)
            parsed_data = _convert_dirty_json(parsed_data)
        else:
            parsed_data = json.loads(text)
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}. Raw text: {text}")
        # Attempt to find JSON object if there's extra text
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                if DIRTYJSON_AVAILABLE:
                    parsed_data = dirtyjson.loads(json_str)
                    parsed_data = _convert_dirty_json(parsed_data)
                else:
                    parsed_data = json.loads(json_str)
        except Exception:
            pass
        
        if parsed_data is None:
             raise

    # Ensure the result is a dictionary
    if isinstance(parsed_data, list):
        logger.warning("Parsed JSON is a list, wrapping in dictionary.")
        return {"items": parsed_data}
    elif isinstance(parsed_data, dict):
        return parsed_data
    else:
        logger.warning(f"Parsed JSON is of type {type(parsed_data)}, wrapping in dictionary.")
        return {"content": parsed_data}

def analyze_video_frames(
    video_path: str,
    sample_rate: int = 1,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Extract and analyze frames from video input using Gemini 3.

    Args:
        video_path: Path to video file or URL.
        sample_rate: Frames per second to sample (not used directly with Gemini 3 as it handles video natively).
        tool_context: ADK tool context for state access.

    Returns:
        Dictionary containing frame analysis with keys:
        - design_tokens: Detected colors, fonts, spacing
        - components: Identified UI components
        - layout_structure: Grid/flexbox patterns detected
        - visual_hierarchy: Element importance and relationships
    """
    logger.info(f"Analyzing video: {video_path}")

    if not video_path:
        return {"status": "error", "error": "Video path is required"}

    # Handle YouTube URLs
    temp_video_path = None
    if _is_youtube_url(video_path):
        try:
            # Create a temporary path for the downloaded video
            temp_dir = Path("temp_videos")
            temp_dir.mkdir(exist_ok=True)
            # Use a simple name or hash for the file
            filename = "youtube_video.mp4" 
            temp_video_path = temp_dir / filename
            
            # Download if it doesn't exist or we want to overwrite
            # For simplicity, we'll overwrite or just use it
            _download_youtube_video(video_path, temp_video_path)
            path = temp_video_path
        except Exception as e:
            return {"status": "error", "error": f"Failed to download YouTube video: {e}"}
    else:
        path = Path(video_path)
        if not path.exists():
            return {"status": "error", "error": f"Video file not found: {video_path}"}

    try:
        # Ensure API key is loaded
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
             return {"status": "error", "error": "GOOGLE_API_KEY not found in environment"}

        client = genai.Client(api_key=api_key)
        video_file = _upload_file(client, path)

        prompt = """
        Analyze this video of a website walkthrough. Extract the following design details in JSON format:
        {
            "design_tokens": {
                "colors": [{"name": "string", "hex_code": "string"}],
                "typography": [{"font_family": "string", "font_size": "string", "font_weight": "string"}],
                "spacing": {"base": "string", "padding": "string"}
            },
            "components": [{"type": "string", "elements": ["string"]}],
            "layout_structure": "string",
            "visual_hierarchy": "string"
        }
        Ensure the output is valid JSON.
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[video_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        try:
            analysis_results = _parse_json_response(response.text)
            
            # If the result was wrapped in "items" because it was a list, try to extract the first item
            # if it looks like the expected object
            if "items" in analysis_results and isinstance(analysis_results["items"], list) and len(analysis_results["items"]) > 0:
                first_item = analysis_results["items"][0]
                if isinstance(first_item, dict) and "design_tokens" in first_item:
                    analysis_results = first_item
                    
        except Exception as e:
             logger.warning(f"Failed to parse JSON response from Gemini: {e}. Returning raw text.")
             analysis_results = {"raw_response": response.text, "error": str(e)}

        analysis_results["status"] = "success"

        # Store results in context if available
        if tool_context:
            logger.info("Storing analysis results in ToolContext")
            tool_context.state["video_analysis_results"] = analysis_results
            # Safely get design_tokens, defaulting to empty dict if not present or if parsing failed
            tool_context.state["design_tokens"] = analysis_results.get("design_tokens", {})

        return analysis_results

    except Exception as e:
        logger.error(f"Error analyzing video: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        # Cleanup temporary file if it was downloaded
        if temp_video_path and temp_video_path.exists():
            try:
                os.remove(temp_video_path)
            except OSError:
                pass


def extract_audio_transcript(
    video_path: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Extract and transcribe audio from video using Gemini 3.

    Args:
        video_path: Path to video file or URL.
        tool_context: ADK tool context for state access.

    Returns:
        Dictionary containing timestamped transcript and summary.
    """
    logger.info(f"Extracting audio from: {video_path}")

    if not video_path:
        return {"status": "error", "error": "Video path is required"}
    
    # Handle YouTube URLs
    temp_video_path = None
    if _is_youtube_url(video_path):
        try:
            temp_dir = Path("temp_videos")
            temp_dir.mkdir(exist_ok=True)
            filename = "youtube_video_audio.mp4"
            temp_video_path = temp_dir / filename
            _download_youtube_video(video_path, temp_video_path)
            path = temp_video_path
        except Exception as e:
            return {"status": "error", "error": f"Failed to download YouTube video: {e}"}
    else:
        path = Path(video_path)
        if not path.exists():
            return {"status": "error", "error": f"Video file not found: {video_path}"}

    try:
        # Ensure API key is loaded
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
             return {"status": "error", "error": "GOOGLE_API_KEY not found in environment"}

        client = genai.Client(api_key=api_key)
        video_file = _upload_file(client, path)

        prompt = """
        Transcribe the audio from this video. Provide the output in JSON format with the following keys:
        {
            "transcript": [{"timestamp": "string", "text": "string"}],
            "summary": "string",
            "navigation_structure": ["string"],
            "cta_elements": ["string"]
        }
        Ensure the output is valid JSON.
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[video_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        try:
            transcript_results = _parse_json_response(response.text)
            
            # Handle list wrapping if necessary
            if "items" in transcript_results and isinstance(transcript_results["items"], list) and len(transcript_results["items"]) > 0:
                first_item = transcript_results["items"][0]
                if isinstance(first_item, dict) and "transcript" in first_item:
                    transcript_results = first_item
                    
        except Exception as e:
             logger.warning(f"Failed to parse JSON response from Gemini: {e}. Returning raw text.")
             transcript_results = {"raw_response": response.text, "error": str(e)}
             
        transcript_results["status"] = "success"

        if tool_context:
            tool_context.state["content_extraction_results"] = transcript_results

        return transcript_results

    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        if temp_video_path and temp_video_path.exists():
            try:
                os.remove(temp_video_path)
            except OSError:
                pass

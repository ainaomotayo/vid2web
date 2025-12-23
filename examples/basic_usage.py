import asyncio
import logging
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.adk.models.google_llm import Gemini, _ResourceExhaustedError
from google.genai import types
from google.genai.errors import ClientError
from video_to_website.agent import app, root_agent

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Use the same YouTube video from our tests
VIDEO_URL = "https://www.youtube.com/watch?v=rNxC16mlO60"

async def run_with_retry(runner, user_id, session_id, message, max_retries=5):
    """Runs the agent with exponential backoff and model fallback logic."""
    retries = 0
    while retries < max_retries:
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message,
            ):
                # Check for tool call by inspecting the content directly
                is_tool_call = False
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            is_tool_call = True
                            tool_name = part.function_call.name
                            logger.info(f"🛠️ Calling tool: {tool_name}...")
                            break 
                
                if event.is_final_response() and not is_tool_call:
                    # Safely access content and parts
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text or ""
                        logger.info(f"Agent finished with response: {final_response}")
                    else:
                        logger.info("Agent finished (no text response).")
                else:
                    pass
            return # Success
            
        except* (_ResourceExhaustedError, ClientError, AttributeError, RuntimeError) as eg:
            # Handle exceptions from the group
            is_quota_error = False
            
            for e in eg.exceptions:
                if isinstance(e, _ResourceExhaustedError):
                    is_quota_error = True
                elif isinstance(e, ClientError) and e.code == 429:
                    is_quota_error = True
                elif isinstance(e, AttributeError) and "ClientConnectorDNSError" in str(e):
                    is_quota_error = True
                elif isinstance(e, RuntimeError) and "on_model_error_callback" in str(e):
                    is_quota_error = True
            
            if is_quota_error:
                wait_time = (2 ** retries) * 10
                logger.warning(f"Quota error caught (in ExceptionGroup). Retrying in {wait_time}s... (Attempt {retries + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
                retries += 1
            else:
                # If it's not a quota error we know how to handle, re-raise the group
                raise eg

    raise Exception("Max retries exceeded for agent execution.")

async def main():
    """
    Runs the full video-to-website pipeline.
    """
    logger.info("--- Starting Video-to-Website Generation (Golden Run) ---")
    
    # 1. Check for API Key
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.error("FATAL: GOOGLE_API_KEY environment variable not set.")
        logger.error("Please create a .env file in the root directory and add your key.")
        return

    # 2. Initialize ADK Runner with the App (which includes plugins)
    runner = InMemoryRunner(
        agent=app.root_agent,
        app_name="video_to_website_example",
    )
    
    # Register plugins from the App definition
    for plugin in app.plugins:
        runner.plugin_manager.register_plugin(plugin)
    
    # 3. Create a session with the video path in the initial state
    session = await runner.session_service.create_session(
        app_name="video_to_website_example",
        user_id="example_user",
        state={
            "input_video_path": VIDEO_URL,
            "target_framework": "html" # Default to HTML for basic run
        },
    )
    logger.info(f"ADK Session created: {session.id}")
    
    # 4. Create the initial message to kick off the agent
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text=f"Generate a website from the video at {VIDEO_URL}."
        )],
    )
    
    # 5. Run the agent with retry logic
    logger.info("Starting agent execution... This may take several minutes.")
    try:
        await run_with_retry(runner, "example_user", session.id, message)

        # 6. Re-fetch the session to get the final state
        updated_session = await runner.session_service.get_session(
            app_name=runner.app_name,
            user_id="example_user",
            session_id=session.id
        )
        final_state = updated_session.state

        # 7. Verify Output
        output_dir = Path(f"output/{session.id}/generated_website")
        if output_dir.exists():
            logger.info("\n--- Generation Complete! ---")
            logger.info(f"Output Directory: {output_dir.resolve()}")
            
            files = list(output_dir.glob("*"))
            logger.info(f"Generated Files: {[f.name for f in files]}")
            
            assets_dir = output_dir / "assets"
            if assets_dir.exists():
                assets = list(assets_dir.glob("*"))
                logger.info(f"Extracted Assets: {len(assets)} images found.")
            
            logger.info(f"To view it, open '{output_dir.resolve() / 'index.html'}' in your browser.")
        else:
            logger.error("Output directory was not created. Something went wrong.")

    except Exception as e:
        logger.error(f"An error occurred during agent execution: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())

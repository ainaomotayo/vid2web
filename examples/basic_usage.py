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
OUTPUT_DIR = Path("output/generated_website")

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
                if event.is_final_response():
                    final_response = event.content.parts[0].text if event.content.parts else ""
                    logger.info(f"Agent finished with response: {final_response}")
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
    Runs the full video-to-website pipeline and saves the output to the
    `output/generated_website` directory.
    """
    logger.info("--- Starting Video-to-Website Generation ---")
    
    # Ensure the output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output will be saved to: {OUTPUT_DIR.resolve()}")

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
        state={"input_video_path": VIDEO_URL},
    )
    logger.info(f"ADK Session created: {session.id}")
    
    # 4. Create the initial message to kick off the agent
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text=f"Generate a website from the video at {VIDEO_URL}. Save the files to the '{OUTPUT_DIR}' directory."
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

        # 7. Save the generated files from the state
        html = final_state.get("generated_html")
        css = final_state.get("generated_css")
        js = final_state.get("generated_js")

        if html:
            (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
            logger.info("✅ index.html saved.")
        if css:
            (OUTPUT_DIR / "styles.css").write_text(css, encoding="utf-8")
            logger.info("✅ styles.css saved.")
        if js:
            (OUTPUT_DIR / "scripts.js").write_text(js, encoding="utf-8")
            logger.info("✅ scripts.js saved.")

        logger.info("\n--- Generation Complete! ---")
        logger.info(f"You can find the generated website in the '{OUTPUT_DIR.resolve()}' directory.")
        logger.info(f"To view it, open '{OUTPUT_DIR.resolve() / 'index.html'}' in your browser.")

    except Exception as e:
        logger.error(f"An error occurred during agent execution: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())

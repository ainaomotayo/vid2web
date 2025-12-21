import asyncio
import logging
from google.adk.runners import InMemoryRunner
from google.genai import types
from video_to_website.agent import root_agent

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("Running custom styling example...")
    
    # Initialize runner
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="custom_styling_example",
    )
    
    # Create session with custom preferences
    session = await runner.session_service.create_session(
        app_name="custom_styling_example",
        user_id="style_user",
        state={
            "input_video_path": "examples/sample_videos/demo.mp4",
            "user:preferred_framework": "tailwind",
            "user:color_preferences": {"primary": "#FF5733"},
        },
    )
    
    # Create input message
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            "Generate a website with a modern, vibrant look."
        )],
    )
    
    # Run agent
    print("Starting agent execution...")
    try:
        async for event in runner.run_async(
            user_id="style_user",
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response():
                print(f"Agent Response: {event.content.parts[0].text}")
    except Exception as e:
        print(f"Execution failed (expected without API key): {e}")

if __name__ == "__main__":
    asyncio.run(main())

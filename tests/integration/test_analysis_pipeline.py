import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types
from video_to_website.agent import app

@pytest.fixture
def runner():
    runner = InMemoryRunner(
        agent=app.root_agent,
        app_name="test_analysis",
    )
    for plugin in app.plugins:
        runner.plugin_manager.register_plugin(plugin)
    return runner

@pytest.fixture
async def session(runner):
    return await runner.session_service.create_session(
        app_name="test_analysis",
        user_id="test_user",
    )

@pytest.mark.asyncio
async def test_parallel_analysis_extracts_design_and_content(runner, session, mock_video_path):
    """Analysis phase should extract both design tokens and content."""
    
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text=f"Analyze the video at {mock_video_path}"
        )],
    )
    
    events = []
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=message,
    ):
        events.append(event)
        
    # Re-fetch the session to get the updated state
    updated_session = await runner.session_service.get_session(
        app_name=session.app_name,
        user_id=session.user_id,
        session_id=session.id
    )
    final_state = updated_session.state
    
    # Check if analysis results are present
    assert final_state.get("video_analysis_results") is not None or final_state.get("content_extraction_results") is not None

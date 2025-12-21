import pytest
import os
from google.adk.runners import InMemoryRunner
from google.genai import types
from video_to_website.agent import app

@pytest.fixture
def runner():
    runner = InMemoryRunner(
        agent=app.root_agent,
        app_name="test_full_pipeline",
    )
    for plugin in app.plugins:
        runner.plugin_manager.register_plugin(plugin)
    return runner

@pytest.fixture
async def session(runner):
    return await runner.session_service.create_session(
        app_name="test_full_pipeline",
        user_id="test_user",
    )

@pytest.mark.asyncio
async def test_full_pipeline_execution(runner, session, mock_video_path):
    """Full pipeline should run from analysis to validation."""
    
    # Skip if no API key is present (e.g. in CI without secrets)
    if not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")

    # Use the YouTube URL from the fixture
    video_path = mock_video_path
    
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text=f"Generate a website from this video: {video_path}"
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
    
    # Check Analysis
    assert "video_analysis_results" in final_state
    assert "content_extraction_results" in final_state
    
    # Check Architecture (might be implicit in code gen, but good to check if agent sets it)
    # Note: architecture_agent doesn't have a tool to set state explicitly in the current implementation,
    # it relies on the LLM response being passed. However, code_generator uses it.
    
    # Check Code Generation
    assert "generated_html" in final_state
    assert "generated_css" in final_state
    assert "generated_js" in final_state
    
    # Check Validation
    # Validation results might be in the state if the validator tool sets them
    # Our validator tool mock implementation doesn't explicitly set state keys in the tool function itself,
    # but the agent might capture the output.
    # Let's check if we have a final response
    assert any(e.is_final_response() for e in events)

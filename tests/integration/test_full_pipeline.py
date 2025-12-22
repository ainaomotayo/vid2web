import pytest
import os
from pathlib import Path
from google.adk.runners import InMemoryRunner
from google.genai import types
from video_to_website.agent import app

@pytest.fixture
def runner(common_plugins):
    runner = InMemoryRunner(
        agent=app.root_agent,
        app_name="test_full_pipeline",
    )
    for plugin in common_plugins:
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
    
    # Check Architecture
    assert "site_architecture" in final_state
    
    # Check Code Generation
    assert "generated_html" in final_state
    assert "generated_css" in final_state
    assert "generated_js" in final_state
    
    # Check Image Extraction
    assert "asset_manifest" in final_state
    asset_manifest = final_state["asset_manifest"]
    assert isinstance(asset_manifest, list)
    if asset_manifest:
        # Check if the asset files were actually created
        first_asset_path = Path(asset_manifest[0])
        assert first_asset_path.exists()
        assert first_asset_path.parent.name == "assets"

    # Check Validation
    assert any(e.is_final_response() for e in events)

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types
from video_to_website.agents.code_generator import code_generator_agent
from video_to_website.agent import app

@pytest.fixture
def runner():
    # Note: We are testing a sub-agent here, but we want the global plugins.
    # We can manually register them.
    runner = InMemoryRunner(
        agent=code_generator_agent,
        app_name="test_generation",
    )
    for plugin in app.plugins:
        runner.plugin_manager.register_plugin(plugin)
    return runner

@pytest.fixture
async def session(runner):
    return await runner.session_service.create_session(
        app_name="test_generation",
        user_id="test_user",
        state={
            "site_architecture": {
                "site_map": {"pages": [{"title": "Home", "path": "/"}]},
                "component_specs": [],
                "style_architecture": {},
                "interaction_specs": {}
            },
            "design_tokens": {
                "colors": [{"name": "Primary", "hex_code": "#000000"}],
                "typography": [],
                "spacing": {}
            },
            "content_extraction_results": {
                "page_content": {"Hero": {"heading": "Welcome"}}
            }
        }
    )

@pytest.mark.asyncio
async def test_code_generation_produces_files(runner, session):
    """Code generation agent should produce HTML/CSS/JS."""
    
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text="Generate the website code based on the architecture and design."
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
    
    # Check if code artifacts are present
    assert "generated_html" in final_state
    assert "generated_css" in final_state
    assert "generated_js" in final_state

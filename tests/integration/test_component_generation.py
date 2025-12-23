import pytest
from pathlib import Path
from google.adk.runners import InMemoryRunner
from google.genai import types
from video_to_website.agents.code_generator import code_generator_agent
from video_to_website.plugins.model_fallback_plugin import ModelFallbackPlugin
from google.adk.plugins import ReflectAndRetryToolPlugin

@pytest.fixture
def runner():
    runner = InMemoryRunner(
        agent=code_generator_agent,
        app_name="test_component_gen",
    )
    runner.plugin_manager.register_plugin(ModelFallbackPlugin())
    runner.plugin_manager.register_plugin(ReflectAndRetryToolPlugin(max_retries=3))
    return runner

@pytest.fixture
async def session(runner):
    # Seed state with an architecture that implies components
    return await runner.session_service.create_session(
        app_name="test_component_gen",
        user_id="test_user",
        state={
            "site_architecture": {
                "site_map": {"pages": [{"title": "Home", "path": "/"}]},
                "component_specs": [
                    {"name": "Navbar", "html_tag": "nav", "description": "Main navigation bar"},
                    {"name": "Hero", "html_tag": "section", "description": "Hero section with title"}
                ],
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
            },
            "asset_manifest": []
        }
    )

@pytest.mark.asyncio
async def test_code_generator_creates_components(runner, session):
    """
    Verifies that the code_generator_agent calls save_component for reusable parts.
    """
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text="Generate the website code. Create separate components for the Navbar and Hero."
        )],
    )
    
    component_tool_called = False

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=message,
    ):
        # Check for tool call
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call and part.function_call.name == "save_component":
                    component_tool_called = True
                    break
        if component_tool_called:
            break
            
    assert component_tool_called, "Code generator did not call 'save_component'."
    
    # Verify state update (need to re-fetch session)
    updated_session = await runner.session_service.get_session(
        app_name=session.app_name,
        user_id=session.user_id,
        session_id=session.id
    )
    
    # Check if components were tracked in state
    generated_components = updated_session.state.get("generated_components", [])
    assert len(generated_components) > 0, "No components were tracked in session state."
    
    # Check if file exists on disk
    first_component = generated_components[0]
    file_path = Path(first_component["path"])
    assert file_path.exists(), f"Component file {file_path} was not created."
    assert file_path.parent.name == "components"

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
        app_name="test_framework_support",
    )
    runner.plugin_manager.register_plugin(ModelFallbackPlugin())
    runner.plugin_manager.register_plugin(ReflectAndRetryToolPlugin(max_retries=3))
    return runner

@pytest.mark.asyncio
async def test_code_generator_produces_react_code(runner):
    """
    Verifies that the code_generator_agent produces React code when requested.
    """
    session = await runner.session_service.create_session(
        app_name="test_framework_support",
        user_id="test_user",
        state={
            "site_architecture": {
                "site_map": {"pages": [{"title": "Home", "path": "/"}]},
                "component_specs": [{"name": "Navbar", "description": "Main navigation"}],
                "style_architecture": {},
                "interaction_specs": {}
            },
            "design_tokens": {"colors": [], "typography": [], "spacing": {}},
            "content_extraction_results": {"page_content": {}},
            "asset_manifest": [],
            "target_framework": "react" # Explicitly request React
        }
    )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text="Generate the website code. Create a Navbar component."
        )],
    )
    
    react_syntax_found = False
    component_saved = False

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=message,
    ):
        # Check tool calls for React syntax
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call and part.function_call.name == "save_component":
                    component_saved = True
                    args = part.function_call.args
                    code = args.get("code", "")
                    component_type = args.get("component_type", "")
                    
                    # Check for React indicators
                    if "className=" in code or "export default function" in code or component_type == "react":
                        react_syntax_found = True
                    break
        if react_syntax_found:
            break
            
    assert component_saved, "Code generator did not call 'save_component'."
    assert react_syntax_found, "Code generator did not produce React syntax (className, export default, etc.)."

@pytest.mark.asyncio
async def test_code_generator_produces_vue_code(runner):
    """
    Verifies that the code_generator_agent produces Vue code when requested.
    """
    session = await runner.session_service.create_session(
        app_name="test_framework_support",
        user_id="test_user",
        state={
            "site_architecture": {
                "site_map": {"pages": [{"title": "Home", "path": "/"}]},
                "component_specs": [{"name": "Navbar", "description": "Main navigation"}],
                "style_architecture": {},
                "interaction_specs": {}
            },
            "design_tokens": {"colors": [], "typography": [], "spacing": {}},
            "content_extraction_results": {"page_content": {}},
            "asset_manifest": [],
            "target_framework": "vue" # Explicitly request Vue
        }
    )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text="Generate the website code. Create a Navbar component."
        )],
    )
    
    vue_syntax_found = False
    component_saved = False

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=message,
    ):
        # Check tool calls for Vue syntax
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call and part.function_call.name == "save_component":
                    component_saved = True
                    args = part.function_call.args
                    code = args.get("code", "")
                    component_type = args.get("component_type", "")
                    
                    # Check for Vue indicators
                    if "<template>" in code or "<script>" in code or component_type == "vue":
                        vue_syntax_found = True
                    break
        if vue_syntax_found:
            break
            
    assert component_saved, "Code generator did not call 'save_component'."
    assert vue_syntax_found, "Code generator did not produce Vue syntax (<template>, <script>, etc.)."

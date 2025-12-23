import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types

# Robust import for EventType
try:
    from google.adk.types import EventType
except ImportError:
    try:
        from google.adk.events import EventType
    except ImportError:
        try:
            from google.adk.events.event import EventType
        except ImportError:
            # Fallback definition if import fails
            class EventType:
                TOOL_CALL = "tool_call"

from video_to_website.agents.architecture_agent import architecture_agent
from video_to_website.plugins.model_fallback_plugin import ModelFallbackPlugin
from google.adk.plugins import ReflectAndRetryToolPlugin

@pytest.fixture
def runner():
    runner = InMemoryRunner(
        agent=architecture_agent,
        app_name="test_tool_correctness",
    )
    # Register plugins for robustness
    runner.plugin_manager.register_plugin(ModelFallbackPlugin())
    runner.plugin_manager.register_plugin(ReflectAndRetryToolPlugin(max_retries=3))
    return runner

@pytest.fixture
async def session(runner):
    # Seed the state with the kind of data the architecture agent expects
    return await runner.session_service.create_session(
        app_name="test_tool_correctness",
        user_id="test_user",
        state={
            "video_analysis_results": {"design_tokens": {}, "components": []},
            "content_extraction_results": {"page_content": {}}
        }
    )

@pytest.mark.asyncio
async def test_architecture_agent_calls_correct_tool(runner, session):
    """
    Golden Dataset Test: Verifies that the architecture_agent calls the
    `save_page_structure` tool as instructed.
    """
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text="Create an architecture plan based on the analysis."
        )],
    )
    
    tool_called = False
    expected_tool_name = "save_page_structure"

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=message,
    ):
        # Use the correct EventType check
        event_type = getattr(event, "event_type", None)
        if event_type == EventType.TOOL_CALL:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_call and part.function_call.name == expected_tool_name:
                        tool_called = True
                        break
        if tool_called:
            break
            
    assert tool_called, f"Agent was expected to call '{expected_tool_name}' but did not."

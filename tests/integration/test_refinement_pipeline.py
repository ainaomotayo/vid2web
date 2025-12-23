import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types
from video_to_website.agents.refiner_agent import refiner_agent
from video_to_website.plugins.model_fallback_plugin import ModelFallbackPlugin
from google.adk.plugins import ReflectAndRetryToolPlugin

@pytest.fixture
def runner():
    runner = InMemoryRunner(
        agent=refiner_agent,
        app_name="test_refinement",
    )
    runner.plugin_manager.register_plugin(ModelFallbackPlugin())
    runner.plugin_manager.register_plugin(ReflectAndRetryToolPlugin(max_retries=3))
    return runner

@pytest.fixture
async def session(runner):
    # Seed the state with code that has a dependency issue
    return await runner.session_service.create_session(
        app_name="test_refinement",
        user_id="test_user",
        state={
            "generated_html": "<html><body><div class='old-class'>Content</div></body></html>",
            "generated_css": ".old-class { color: red; }",
            "generated_js": "",
            "validation_results": {
                "passed": False,
                "issues": [
                    {
                        "severity": "warning",
                        "description": "CSS class naming convention violation",
                        "suggestion": "Rename 'old-class' to 'new-class' in both HTML and CSS."
                    }
                ]
            }
        }
    )

@pytest.mark.asyncio
async def test_refiner_fixes_code_based_on_validation(runner, session):
    """
    Verifies that the refiner_agent receives the code and validation report,
    and calls apply_code_fixes with a LIST of fixes for multiple files.
    """
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text="Fix the issues identified in the validation report. Ensure you update all dependent files."
        )],
    )
    
    tool_called = False
    html_fixed = False
    css_fixed = False

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=message,
    ):
        # Check for a tool call by inspecting the content parts
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call and part.function_call.name == "apply_code_fixes":
                    tool_called = True
                    args = part.function_call.args
                    
                    # Check if 'fixes' argument is present and is a list
                    if "fixes" in args and isinstance(args["fixes"], list):
                        for fix in args["fixes"]:
                            if "index.html" in fix.get("file_path", "") and "new-class" in fix.get("fixed_code", ""):
                                html_fixed = True
                            if "styles.css" in fix.get("file_path", "") and "new-class" in fix.get("fixed_code", ""):
                                css_fixed = True
                    break
        if tool_called:
            break
            
    assert tool_called, "Refiner agent did not call 'apply_code_fixes'."
    assert html_fixed, "Refiner agent did not update the HTML file."
    assert css_fixed, "Refiner agent did not update the CSS file."

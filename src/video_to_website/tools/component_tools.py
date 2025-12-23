from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def _get_session_output_dir(tool_context: ToolContext | None) -> Path:
    """Determines the output directory based on the session ID."""
    base_output = Path("output")
    if tool_context and hasattr(tool_context, "session_id") and tool_context.session_id:
        return base_output / tool_context.session_id / "generated_website"
    else:
        return base_output / "generated_website"


def save_component(
    name: str,
    code: str,
    component_type: str = "html",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Saves a reusable UI component to the components directory.

    Args:
        name: The name of the component (e.g., 'Navbar', 'HeroSection').
        code: The code for the component.
        component_type: The type/framework of the component ('html', 'react', 'vue').
        tool_context: ADK tool context.

    Returns:
        Status dictionary.
    """
    logger.info(f"Saving component: {name} ({component_type})")
    
    try:
        # Determine file extension
        extension = "html"
        if component_type.lower() == "react":
            extension = "jsx"
        elif component_type.lower() == "vue":
            extension = "vue"
            
        filename = f"{name}.{extension}"
        
        # Determine path
        output_dir = _get_session_output_dir(tool_context)
        components_dir = output_dir / "components"
        components_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = components_dir / filename
        
        # Write file
        file_path.write_text(code, encoding="utf-8")
        
        # Update state to track components
        if tool_context:
            components = tool_context.state.get("generated_components", [])
            components.append({"name": name, "path": str(file_path), "type": component_type})
            tool_context.state["generated_components"] = components

        return {"status": "success", "path": str(file_path)}
        
    except Exception as e:
        logger.error(f"Error saving component {name}: {e}")
        return {"status": "error", "error": str(e)}

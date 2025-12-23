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
        # Use session-specific subdirectory
        return base_output / tool_context.session_id / "generated_website"
    else:
        # Fallback for CLI/Tests without session ID
        return base_output / "generated_website"


def save_artifact(
    filename: str,
    content: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Save generated content as an artifact and update the session state.

    Args:
        filename: Name of the file to save. Can be a path.
        content: File content.
        tool_context: ADK tool context for artifact management.

    Returns:
        Status and artifact metadata.
    """
    if not tool_context:
        return {"status": "error", "error": "ToolContext is required"}

    try:
        output_dir = _get_session_output_dir(tool_context)
        
        # Handle if filename already includes 'output/' (legacy behavior)
        clean_filename = filename
        if str(filename).startswith("output"):
             path_parts = Path(filename).parts
             if "generated_website" in path_parts:
                 idx = path_parts.index("generated_website")
                 clean_filename = str(Path(*path_parts[idx+1:]))
             elif "output" in path_parts:
                 idx = path_parts.index("output")
                 clean_filename = str(Path(*path_parts[idx+1:]))

        path = output_dir / clean_filename
        
        logger.info(f"Saving artifact to: {path}")
        
        # Ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        path.write_text(content, encoding="utf-8")
        
        # CRITICAL: Update the session state so the UI can find the code
        if path.name == "index.html":
            tool_context.state["generated_html"] = content
        elif path.name == "styles.css":
            tool_context.state["generated_css"] = content
        elif path.name == "scripts.js":
            tool_context.state["generated_js"] = content

        return {"status": "success", "filename": str(path)}
    except Exception as e:
        logger.error(f"Error saving artifact {filename}: {e}")
        return {"status": "error", "error": str(e)}


def create_project_structure(
    project_name: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Create the output project directory structure.

    Args:
        project_name: Name of the project.
        tool_context: ADK tool context.

    Returns:
        Created directory structure.
    """
    logger.info(f"Creating project structure for: {project_name}")
    try:
        output_dir = _get_session_output_dir(tool_context)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "assets").mkdir(exist_ok=True)
        (output_dir / "components").mkdir(exist_ok=True)

        return {
            "status": "success",
            "project_name": project_name,
            "path": str(output_dir),
        }
    except Exception as e:
        logger.error(f"Error creating project structure: {e}")
        return {"status": "error", "error": str(e)}

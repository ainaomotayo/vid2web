from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def save_artifact(
    filename: str,
    content: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Save generated content as an artifact.

    Args:
        filename: Name of the file to save. Can be a path.
        content: File content.
        tool_context: ADK tool context for artifact management.

    Returns:
        Status and artifact metadata.
    """
    if not tool_context:
        return {"status": "error", "error": "ToolContext is required"}

    logger.info(f"Saving artifact: {filename}")
    try:
        # Determine the output path
        # If filename starts with 'output/', treat it as relative to CWD
        # Otherwise, prepend 'output/' to keep artifacts organized
        path = Path(filename)
        if not str(path).startswith("output"):
             path = Path("output") / path
        
        # Ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        path.write_text(content, encoding="utf-8")

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
        base_path = Path("output") / project_name
        base_path.mkdir(parents=True, exist_ok=True)
        (base_path / "assets").mkdir(exist_ok=True)

        return {
            "status": "success",
            "project_name": project_name,
            "path": str(base_path),
        }
    except Exception as e:
        logger.error(f"Error creating project structure: {e}")
        return {"status": "error", "error": str(e)}

from __future__ import annotations

import logging
from typing import Any

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def save_page_structure(
    site_map: dict[str, Any],
    component_specs: list[dict[str, Any]],
    style_architecture: dict[str, Any],
    interaction_specs: dict[str, Any],
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Saves the generated page structure and site architecture to the session state.

    Args:
        site_map: The structure of pages and navigation.
        component_specs: Detailed specifications for UI components.
        style_architecture: CSS variables and global styles.
        interaction_specs: JavaScript behavior requirements.
        tool_context: ADK tool context.

    Returns:
        Status dictionary.
    """
    logger.info("Saving page structure to state...")
    
    if tool_context:
        architecture = {
            "site_map": site_map,
            "component_specs": component_specs,
            "style_architecture": style_architecture,
            "interaction_specs": interaction_specs,
        }
        tool_context.state["site_architecture"] = architecture
        return {"status": "success", "message": "Architecture saved to state."}
    
    return {"status": "error", "error": "No ToolContext available."}

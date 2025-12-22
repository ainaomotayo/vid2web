from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def read_generated_code(
    filename: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Reads the content of a generated code file.

    Args:
        filename: Name of the file to read (e.g., 'index.html', 'styles.css').
        tool_context: ADK tool context.

    Returns:
        Dictionary containing the file content.
    """
    logger.info(f"Reading generated code: {filename}")
    
    # Try to get from state first (fastest)
    if tool_context:
        if filename == "index.html" and "generated_html" in tool_context.state:
            return {"status": "success", "content": tool_context.state["generated_html"]}
        if filename == "styles.css" and "generated_css" in tool_context.state:
            return {"status": "success", "content": tool_context.state["generated_css"]}
        if filename == "scripts.js" and "generated_js" in tool_context.state:
            return {"status": "success", "content": tool_context.state["generated_js"]}

    # Fallback to file system
    try:
        path = Path(filename)
        if not str(path).startswith("output"):
             path = Path("output") / path
             
        if path.exists():
            return {"status": "success", "content": path.read_text(encoding="utf-8")}
        else:
            return {"status": "error", "error": f"File not found: {filename}"}
            
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")
        return {"status": "error", "error": str(e)}


def apply_code_fixes(
    file_path: str,
    fixed_code: str,
    explanation: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Applies fixes to a generated code file.

    Args:
        file_path: Path to the file to be fixed (e.g., 'output/generated_website/index.html').
        fixed_code: The complete, corrected code content.
        explanation: A brief explanation of what was fixed.
        tool_context: ADK tool context.

    Returns:
        Status dictionary.
    """
    logger.info(f"Applying fixes to {file_path}: {explanation}")
    
    try:
        # Determine the output path
        path = Path(file_path)
        if not str(path).startswith("output"):
             path = Path("output") / path
        
        if not path.exists():
            return {"status": "error", "error": f"File not found: {path}"}
            
        # Write the fixed code
        path.write_text(fixed_code, encoding="utf-8")
        
        # Update the session state with the new code so subsequent agents see it
        if tool_context:
            if path.name == "index.html":
                tool_context.state["generated_html"] = fixed_code
            elif path.name == "styles.css":
                tool_context.state["generated_css"] = fixed_code
            elif path.name == "scripts.js":
                tool_context.state["generated_js"] = fixed_code
                
            # Increment refinement count
            count = tool_context.state.get("refinement_count", 0)
            tool_context.state["refinement_count"] = count + 1

        return {"status": "success", "message": f"Fixed {path.name}"}
        
    except Exception as e:
        logger.error(f"Error applying fixes to {file_path}: {e}")
        return {"status": "error", "error": str(e)}

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Dict

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def _get_session_output_dir(tool_context: ToolContext | None) -> Path:
    """Determines the output directory based on the session ID."""
    base_output = Path("output")
    if tool_context and hasattr(tool_context, "session_id") and tool_context.session_id:
        return base_output / tool_context.session_id / "generated_website"
    else:
        return base_output / "generated_website"


def apply_code_fixes(
    fixes: List[Dict[str, str]],
    explanation: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Applies a set of code fixes to multiple files atomically.

    Args:
        fixes: A list of dictionaries, where each dict has:
               - 'file_path': Path to the file (e.g., 'output/generated_website/index.html')
               - 'fixed_code': The complete, corrected code content for that file.
        explanation: A brief explanation of what was fixed and why.
        tool_context: ADK tool context.

    Returns:
        Status dictionary.
    """
    logger.info(f"Applying patch set: {explanation}")
    
    results = []
    errors = []

    try:
        output_dir = _get_session_output_dir(tool_context)

        for fix in fixes:
            file_path = fix.get("file_path")
            fixed_code = fix.get("fixed_code")
            
            if not file_path or fixed_code is None:
                errors.append(f"Invalid fix object: {fix}")
                continue

            # Handle path resolution relative to session dir
            # If the agent provides 'output/generated_website/index.html', we map it to the session dir
            clean_filename = file_path
            if "generated_website" in file_path:
                parts = Path(file_path).parts
                idx = parts.index("generated_website")
                clean_filename = str(Path(*parts[idx+1:]))
            elif "output" in file_path:
                 parts = Path(file_path).parts
                 idx = parts.index("output")
                 clean_filename = str(Path(*parts[idx+1:]))

            path = output_dir / clean_filename
            
            # Ensure parent dir exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the fixed code
            path.write_text(fixed_code, encoding="utf-8")
            results.append(f"Updated {path.name}")
            
            # Update the session state
            if tool_context:
                if path.name == "index.html":
                    tool_context.state["generated_html"] = fixed_code
                elif path.name == "styles.css":
                    tool_context.state["generated_css"] = fixed_code
                elif path.name == "scripts.js":
                    tool_context.state["generated_js"] = fixed_code
                
                if "components" in str(path):
                    components = tool_context.state.get("generated_components", [])
                    found = False
                    for comp in components:
                        if comp["path"] == str(path):
                            comp["code"] = fixed_code
                            found = True
                            break
                    if not found:
                        components.append({"name": path.stem, "path": str(path), "type": "unknown"})
                    tool_context.state["generated_components"] = components

        if tool_context:
            count = tool_context.state.get("refinement_count", 0)
            tool_context.state["refinement_count"] = count + 1

        if errors:
            return {"status": "partial_success", "updated": results, "errors": errors}
        
        return {"status": "success", "message": f"Applied fixes to {len(results)} files: {', '.join(results)}"}
        
    except Exception as e:
        logger.error(f"Error applying fixes: {e}")
        return {"status": "error", "error": str(e)}

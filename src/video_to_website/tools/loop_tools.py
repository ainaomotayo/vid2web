from __future__ import annotations

import logging
from typing import Any

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def check_validation_status(
    validation_results: dict[str, Any],
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Analyzes validation results and determines if the loop should exit.

    Args:
        validation_results: The report from the validation step.
        tool_context: ADK tool context.

    Returns:
        Status dictionary with 'passed' boolean.
    """
    logger.info("Checking validation status...")
    
    passed = validation_results.get("passed", False)
    
    # If passed is not explicitly True, check for critical issues
    if not passed:
        issues = validation_results.get("issues", [])
        critical_issues = [i for i in issues if i.get("severity") == "error"]
        if not critical_issues:
            passed = True
            
    if tool_context:
        tool_context.state["validation_passed"] = passed
        logger.info(f"Validation passed: {passed}")

    return {
        "status": "success",
        "validation_passed": passed,
        "message": "Validation passed" if passed else "Validation failed, refinement needed"
    }

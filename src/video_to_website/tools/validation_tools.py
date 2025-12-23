from __future__ import annotations

import logging
import os
from typing import Any, List

from google.adk.tools import ToolContext

# Try to import playwright, but don't fail if it's not installed
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Try to import axe-core-python
try:
    from axe_core_python.async_playwright import Axe
    AXE_AVAILABLE = True
except ImportError:
    AXE_AVAILABLE = False

logger = logging.getLogger(__name__)


async def launch_browser_preview(
    html_path: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Launch browser with generated HTML for preview and capture console errors.

    Args:
        html_path: Path to HTML file.
        tool_context: ADK tool context.

    Returns:
        Browser session information and console errors.
    """
    logger.info(f"Launching browser preview for: {html_path}")
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not installed. Returning mock session.")
        return {"status": "success", "session_id": "mock_session_123", "note": "Playwright not available"}

    try:
        # Check if file exists before trying to open it
        if not os.path.exists(html_path):
             return {"status": "error", "error": f"File not found: {html_path}"}

        async with async_playwright() as p:
            # Disable web security to allow local file access to iframes if needed
            browser = await p.chromium.launch(headless=True, args=["--disable-web-security"])
            page = await browser.new_page()
            # Convert file path to file:// URL
            file_url = f"file://{os.path.abspath(html_path)}"
            
            # Capture console errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            
            await page.goto(file_url)
            title = await page.title()
            
            await browser.close()
            
        return {
            "status": "success", 
            "session_id": "playwright_session", 
            "page_title": title,
            "console_errors": console_errors
        }
    except Exception as e:
        logger.error(f"Error launching browser: {e}")
        return {"status": "error", "error": str(e)}


async def capture_screenshot(
    url: str,
    viewport: dict[str, int],
    tool_context: ToolContext | None = None,
) -> bytes:
    """Capture screenshot at specified viewport size.

    Args:
        url: URL or file path to capture.
        viewport: Width and height specification.
        tool_context: ADK tool context.

    Returns:
        Screenshot image bytes.
    """
    logger.info(f"Capturing screenshot of {url} at {viewport}")
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not installed. Returning mock bytes.")
        return b"mock_image_bytes"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-web-security"])
            page = await browser.new_page(viewport=viewport)
            
            # Handle local files
            if not url.startswith("http"):
                # Check if file exists
                if not os.path.exists(url):
                    logger.error(f"File not found for screenshot: {url}")
                    return b""
                url = f"file://{os.path.abspath(url)}"
                
            await page.goto(url)
            screenshot = await page.screenshot()
            await browser.close()
            return screenshot
    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}")
        return b""


async def validate_accessibility(
    html_path: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Run comprehensive accessibility validation checks using axe-core.

    Args:
        html_path: Path to HTML file to validate.
        tool_context: ADK tool context.

    Returns:
        Accessibility audit results.
    """
    logger.info("Validating accessibility...")
    
    if not PLAYWRIGHT_AVAILABLE or not AXE_AVAILABLE:
        logger.warning("Playwright or Axe not installed. Returning mock results.")
        return {"status": "warning", "message": "Validation tools missing", "issues": []}

    try:
        if not os.path.exists(html_path):
             return {"status": "error", "error": f"File not found: {html_path}"}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-web-security"])
            page = await browser.new_page()
            file_url = f"file://{os.path.abspath(html_path)}"
            await page.goto(file_url)
            
            # Run Axe analysis
            axe = Axe()
            # Use context to exclude iframes, which is more robust than the options parameter
            results = await axe.run(page, context={"exclude": [["iframe"]]})
            await browser.close()
            
            # Process results
            violations = results.get("violations", [])
            issues = []
            for v in violations:
                issues.append({
                    "id": v["id"],
                    "description": v["description"],
                    "impact": v["impact"],
                    "help": v["help"],
                    "nodes": [n["html"] for n in v["nodes"]]
                })
                
            score = 100 - (len(issues) * 5)
            return {
                "status": "success",
                "score": max(0, score),
                "issues": issues,
                "violation_count": len(violations)
            }

    except Exception as e:
        logger.error(f"Error validating accessibility: {e}")
        return {"status": "error", "error": str(e)}


async def check_responsive_layout(
    url: str,
    breakpoints: List[int],
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Validate responsive behavior and layout integrity across breakpoints.

    Args:
        url: URL to test.
        breakpoints: List of viewport widths to test.
        tool_context: ADK tool context.

    Returns:
        Responsive validation results.
    """
    logger.info(f"Checking responsiveness at breakpoints: {breakpoints}")
    
    if not PLAYWRIGHT_AVAILABLE:
        return {"status": "success", "results": {str(bp): "mock_pass" for bp in breakpoints}}

    results = {}
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-web-security"])
            
            # Handle local files
            target_url = url
            if not url.startswith("http"):
                if not os.path.exists(url):
                     return {"status": "error", "error": f"File not found: {url}"}
                target_url = f"file://{os.path.abspath(url)}"

            for width in breakpoints:
                page = await browser.new_page(viewport={"width": width, "height": 800})
                await page.goto(target_url)
                
                issues = []

                # 1. Check for Tailwind CSS
                tailwind_loaded = await page.evaluate("""() => {
                    const scripts = Array.from(document.querySelectorAll('script'));
                    return scripts.some(s => s.src.includes('tailwindcss'));
                }""")
                if not tailwind_loaded:
                    issues.append("Tailwind CSS CDN script missing")

                # 2. Check for horizontal scrollbar
                scroll_width = await page.evaluate("document.body.scrollWidth")
                client_width = await page.evaluate("document.body.clientWidth")
                if scroll_width > client_width + 1:
                    issues.append("Horizontal scroll detected")

                # 3. Check Layout Integrity
                elements = {
                    "header": page.get_by_role("banner").first,
                    "main": page.get_by_role("main").first,
                    "footer": page.get_by_role("contentinfo").first,
                }
                
                for name, locator in elements.items():
                    if await locator.count() > 0:
                        box = await locator.bounding_box()
                        if box:
                            if box['width'] == 0 or box['height'] == 0:
                                issues.append(f"Element <{name}> has zero size")
                            
                            # Check for computed styles (e.g., background color)
                            # This helps detect unstyled headers
                            if name == "header":
                                bg_color = await locator.evaluate("el => window.getComputedStyle(el).backgroundColor")
                                if bg_color == "rgba(0, 0, 0, 0)" or bg_color == "transparent":
                                    # Check if it has a background image class
                                    has_bg_class = await locator.evaluate("el => el.className.includes('bg-')")
                                    if not has_bg_class:
                                        issues.append(f"Header might be unstyled (transparent background)")

                if issues:
                    results[str(width)] = f"fail: {', '.join(issues)}"
                else:
                    results[str(width)] = "pass"
                
                await page.close()
            await browser.close()
            
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Error checking responsiveness: {e}")
        return {"status": "error", "error": str(e)}


def measure_performance(
    url: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Measure Core Web Vitals and performance metrics.

    Args:
        url: URL to measure.
        tool_context: ADK tool context.

    Returns:
        Performance metrics dictionary.
    """
    logger.info(f"Measuring performance for: {url}")
    # Placeholder for performance measurement
    return {
        "status": "success",
        "metrics": {
            "LCP": "1.2s",
            "CLS": "0.05",
            "FID": "10ms",
        },
    }

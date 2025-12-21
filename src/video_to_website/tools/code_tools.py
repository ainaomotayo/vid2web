from __future__ import annotations

import logging
import os
from typing import Any, List

from google import genai
from google.genai import types
from google.adk.tools import ToolContext
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

def generate_html(
    structure: dict[str, Any],
    content: dict[str, Any],
    tool_context: ToolContext | None = None,
) -> str:
    """Generate semantic HTML from structure and content specs using Gemini 3.

    Args:
        structure: Component hierarchy and layout.
        content: Text content and metadata.
        tool_context: ADK tool context.

    Returns:
        Generated HTML string.
    """
    logger.info("Generating HTML...")

    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
             return "<!-- Error generating HTML: GOOGLE_API_KEY not found in environment -->"

        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Generate a complete, semantic HTML5 file based on the following structure and content.
        
        Structure:
        {structure}
        
        Content:
        {content}
        
        Requirements:
        - Use semantic tags (header, nav, main, section, footer).
        - Include meta tags for viewport and charset.
        - Link to 'styles.css' and 'scripts.js'.
        - Ensure accessibility (aria labels where appropriate).
        - Output ONLY the raw HTML code, no markdown formatting.
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        
        html_content = response.text
        
        # Clean up markdown code blocks if present
        if html_content.startswith("```html"):
            html_content = html_content.replace("```html", "", 1)
        if html_content.endswith("```"):
            html_content = html_content.replace("```", "", 1)
        
        html_content = html_content.strip()

        if tool_context:
            tool_context.state["generated_html"] = html_content

        return html_content

    except Exception as e:
        logger.error(f"Error generating HTML: {e}")
        return f"<!-- Error generating HTML: {e} -->"


def generate_css(
    design_tokens: dict[str, Any],
    components: List[dict[str, Any]],
    tool_context: ToolContext | None = None,
) -> str:
    """Generate CSS from design tokens and component list using Gemini 3.

    Args:
        design_tokens: Colors, fonts, spacing values.
        components: List of component specifications.
        tool_context: ADK tool context.

    Returns:
        Generated CSS string.
    """
    logger.info("Generating CSS...")

    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
             return "/* Error generating CSS: GOOGLE_API_KEY not found in environment */"

        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Generate a complete CSS file based on the following design tokens and components.
        
        Design Tokens:
        {design_tokens}
        
        Components:
        {components}
        
        Requirements:
        - Use CSS variables for colors, fonts, and spacing.
        - Implement a mobile-first responsive design.
        - Use Flexbox and Grid for layouts.
        - Output ONLY the raw CSS code, no markdown formatting.
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        
        css_content = response.text
        
        # Clean up markdown code blocks if present
        if css_content.startswith("```css"):
            css_content = css_content.replace("```css", "", 1)
        if css_content.endswith("```"):
            css_content = css_content.replace("```", "", 1)
            
        css_content = css_content.strip()

        if tool_context:
            tool_context.state["generated_css"] = css_content

        return css_content

    except Exception as e:
        logger.error(f"Error generating CSS: {e}")
        return f"/* Error generating CSS: {e} */"


def generate_javascript(
    interactions: dict[str, Any],
    tool_context: ToolContext | None = None,
) -> str:
    """Generate JavaScript for specified interactions using Gemini 3.

    Args:
        interactions: Interaction specifications.
        tool_context: ADK tool context.

    Returns:
        Generated JavaScript string.
    """
    logger.info("Generating JavaScript...")

    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
             return "// Error generating JavaScript: GOOGLE_API_KEY not found in environment"

        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Generate a JavaScript file to handle the following interactions.
        
        Interactions:
        {interactions}
        
        Requirements:
        - Use modern ES6+ syntax.
        - Ensure code is wrapped in a DOMContentLoaded event listener.
        - Handle potential errors gracefully.
        - Output ONLY the raw JavaScript code, no markdown formatting.
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        
        js_content = response.text
        
        # Clean up markdown code blocks if present
        if js_content.startswith("```javascript"):
            js_content = js_content.replace("```javascript", "", 1)
        elif js_content.startswith("```js"):
            js_content = js_content.replace("```js", "", 1)
        if js_content.endswith("```"):
            js_content = js_content.replace("```", "", 1)
            
        js_content = js_content.strip()

        if tool_context:
            tool_context.state["generated_js"] = js_content

        return js_content

    except Exception as e:
        logger.error(f"Error generating JavaScript: {e}")
        return f"// Error generating JavaScript: {e}"

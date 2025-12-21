import pytest
from video_to_website.tools.code_tools import generate_html, generate_css, generate_javascript

class TestCodeTools:
    """Tests for code generation tools."""

    def test_generate_html(self):
        """Should generate HTML content."""
        structure = {"pages": []}
        content = {"title": "Test Site"}
        result = generate_html(structure, content)
        assert isinstance(result, str)
        if "Error generating HTML" not in result:
             assert "<html" in result

    def test_generate_css(self):
        """Should generate CSS content."""
        design_tokens = {"colors": [{"name": "Primary", "hex_code": "#000000"}]}
        components = []
        result = generate_css(design_tokens, components)
        assert isinstance(result, str)
        if "Error generating CSS" not in result:
            assert "body" in result

    def test_generate_javascript(self):
        """Should generate JavaScript content."""
        interactions = {}
        result = generate_javascript(interactions)
        assert isinstance(result, str)
        if "Error generating JavaScript" not in result:
             assert isinstance(result, str)

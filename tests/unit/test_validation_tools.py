import pytest
from video_to_website.tools.validation_tools import validate_accessibility, check_responsive_layout

class TestValidationTools:
    """Tests for validation tools."""

    def test_validate_accessibility(self):
        """Should return accessibility results."""
        html_content = "<html><body>Test</body></html>"
        result = validate_accessibility(html_content)
        assert result["status"] == "success"
        assert "score" in result

    @pytest.mark.asyncio
    async def test_check_responsive_layout(self):
        """Should check layout at breakpoints."""
        url = "http://example.com"
        breakpoints = [320, 768]
        result = await check_responsive_layout(url, breakpoints)
        assert result["status"] == "success"
        assert "results" in result

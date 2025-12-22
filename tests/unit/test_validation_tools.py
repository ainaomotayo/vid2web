import pytest
from video_to_website.tools.validation_tools import validate_accessibility, check_responsive_layout

class TestValidationTools:
    """Tests for validation tools."""

    @pytest.mark.asyncio
    async def test_validate_accessibility(self):
        """Should return accessibility results."""
        html_content = "<html><body>Test</body></html>"
        # Note: validate_accessibility expects a file path, not content string directly in the new implementation.
        # However, for this unit test, we might need to mock the file existence check or provide a dummy path.
        # Given the implementation checks os.path.exists, we should use a temporary file.
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            temp_path = f.name
            
        try:
            result = await validate_accessibility(temp_path)
            # If playwright/axe are missing, it returns warning, which is fine for unit test environment
            assert result["status"] in ["success", "warning"]
            if result["status"] == "success":
                assert "score" in result
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.asyncio
    async def test_check_responsive_layout(self):
        """Should check layout at breakpoints."""
        url = "http://example.com"
        breakpoints = [320, 768]
        result = await check_responsive_layout(url, breakpoints)
        assert result["status"] == "success"
        assert "results" in result

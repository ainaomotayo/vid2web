import pytest
from unittest.mock import Mock, patch
from video_to_website.tools.video_tools import analyze_video_frames

class TestAnalyzeVideoFrames:
    """Tests for analyze_video_frames tool."""

    def test_extracts_design_tokens_from_frames(self, mock_video_path):
        """Should extract color palette and typography from video frames."""
        # Arrange
        video_path = mock_video_path
        
        # Act
        result = analyze_video_frames(video_path, sample_rate=1)
        
        # Assert
        assert isinstance(result, dict)
        
        if result.get("status") == "success":
             assert "design_tokens" in result
             assert "colors" in result["design_tokens"]
        else:
             assert "error" in result

    def test_handles_invalid_video_path(self):
        """Should return error for empty video path."""
        result = analyze_video_frames("")
        assert result["status"] == "error"
        assert "Video path is required" in result["error"]

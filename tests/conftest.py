import pytest
from dotenv import load_dotenv
import os
from google.adk.plugins import ReflectAndRetryToolPlugin
from video_to_website.plugins.model_fallback_plugin import ModelFallbackPlugin
from video_to_website.plugins.stagger_plugin import StaggerPlugin

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def mock_video_path():
    # Use the local test video file
    return "tests/fixtures/sample_videos/test_video.mp4"

@pytest.fixture
def common_plugins():
    """Returns a list of plugins to be used in tests."""
    return [
        ModelFallbackPlugin(),
        ReflectAndRetryToolPlugin(max_retries=3),
        StaggerPlugin(min_delay=2.0, max_delay=5.0)
    ]

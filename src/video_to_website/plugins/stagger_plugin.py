from __future__ import annotations

import logging
import asyncio
import random
from typing import Any

from google.adk.plugins import BasePlugin
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

logger = logging.getLogger(__name__)

class StaggerPlugin(BasePlugin):
    """
    A plugin that introduces a random delay before agent execution to stagger parallel requests.
    This helps prevent hitting rate limits (TPM) when multiple agents run simultaneously.
    """

    def __init__(self, min_delay: float = 5.0, max_delay: float = 15.0):
        self.name = "StaggerPlugin"
        self.min_delay = min_delay
        self.max_delay = max_delay

    async def before_agent_callback(
        self,
        callback_context: CallbackContext,
        **kwargs, # Add **kwargs to accept unexpected arguments
    ) -> types.Content | None:
        """
        Introduces a random delay before the agent starts.
        """
        agent_name = callback_context.agent_name
        
        # We only want to stagger the sub-agents that are likely to run in parallel
        # and make heavy API calls.
        target_agents = ["video_analyzer", "content_extractor"]
        
        if agent_name in target_agents:
            delay = random.uniform(self.min_delay, self.max_delay)
            logger.info(f"StaggerPlugin: Delaying agent '{agent_name}' by {delay:.2f}s to prevent rate limiting.")
            await asyncio.sleep(delay)
            
        return None

from __future__ import annotations

import logging
import asyncio
from typing import Any

from google.adk.plugins import BasePlugin
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.models.google_llm import Gemini, _ResourceExhaustedError
from google.genai.errors import ClientError

logger = logging.getLogger(__name__)

class ModelFallbackPlugin(BasePlugin):
    """
    A plugin that detects quota errors and signals a need for model fallback via session state.
    """

    def __init__(self):
        self.name = "ModelFallbackPlugin"
        self.fallback_chain = {
            "gemini-3-flash-preview": "gemini-2.5-flash",
            "gemini-2.5-flash": "gemini-2.0-flash",
        }

    async def on_model_error_callback(
        self,
        callback_context: CallbackContext,
        error: Exception,
        llm_request: LlmRequest,
    ) -> LlmResponse | None:
        """
        Intercepts model errors and flags the session state if quota is exhausted.
        """
        
        # Check for ResourceExhausted errors from ADK or google-genai
        is_quota_error = False
        if isinstance(error, (_ResourceExhaustedError, ClientError)):
            if isinstance(error, ClientError) and error.code != 429:
                return None # Not a quota error
            is_quota_error = True
        # Also check for the specific AttributeError caused by old aiohttp which masks the 429
        elif isinstance(error, AttributeError) and "ClientConnectorDNSError" in str(error):
            is_quota_error = True

        if is_quota_error:
            agent_name = callback_context.agent_name
            logger.warning(f"Quota exhausted for agent '{agent_name}'. Signaling fallback.")
            
            # Respect the API's retry advice by waiting
            logger.info("Waiting 16 seconds before allowing retry to respect API cooldown...")
            await asyncio.sleep(16)
            
            # Set a flag in the session state to indicate fallback is needed
            # The runner loop will check this and update the model
            callback_context.state["fallback_model_needed"] = True
            
            # We return None to let the error propagate to the runner, 
            # which will catch it, see the flag, update the model, and retry.
            return None

        return None

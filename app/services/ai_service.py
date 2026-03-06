"""
AI Agent Service — OpenAI-powered conversational assistant.

The system prompt is loaded from app/prompts/proposal_assistant.txt
so it can be edited without touching application code.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.core.config import settings

# ── Load prompt from file ─────────────────────────────────────────────────────

_PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "proposal_assistant.txt"


def _load_system_prompt() -> str:
    try:
        return _PROMPT_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return (
            "You are a helpful assistant for a Proposal Automation System. "
            "Help users create migration proposals."
        )


SYSTEM_PROMPT = _load_system_prompt()


# ── Service ───────────────────────────────────────────────────────────────────


class AIService:
    """Wraps OpenAI chat completions for the proposal assistant."""

    def __init__(self) -> None:
        key = settings.OPENAI_API_KEY
        self._client = OpenAI(api_key=key) if key else None
        self._model = settings.OPENAI_MODEL

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send conversation history to OpenAI and return the assistant reply."""
        if not self._client:
            return "AI agent is not configured. Please set OPENAI_API_KEY in .env"
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                temperature=0,
                max_tokens=1024,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            return f"Error calling AI: {exc}"

    @staticmethod
    def extract_proposal_json(reply: str) -> Optional[Dict[str, Any]]:
        """Extract a create_proposal JSON block from the assistant reply."""
        try:
            if "```json" in reply:
                start = reply.index("```json") + 7
                end = reply.index("```", start)
                block = reply[start:end].strip()
            elif "{" in reply and "}" in reply:
                start = reply.index("{")
                end = reply.rindex("}") + 1
                block = reply[start:end]
            else:
                return None
            obj = json.loads(block)
            if isinstance(obj, dict) and obj.get("action") == "create_proposal":
                return obj.get("data")
            return None
        except (json.JSONDecodeError, ValueError):
            return None

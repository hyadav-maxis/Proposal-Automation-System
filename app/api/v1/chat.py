"""
AI Chat API router — /api/chat/*
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.chat import ChatRequest
from app.services.ai_service import AIService

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

# Single instance — AIService is stateless (no per-request DB needed)
_ai_svc = AIService()


@router.post("")
async def chat(request: ChatRequest):
    """
    Send a conversation history to the AI assistant and receive a reply.
    If the assistant has gathered enough info, it also returns proposal_data
    ready to send to POST /api/proposals/create.
    """
    if not _ai_svc.is_available:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "AI agent not configured. Set OPENAI_API_KEY in .env",
                "reply": "",
            },
        )
    reply = _ai_svc.chat(request.messages)
    proposal_data = _ai_svc.extract_proposal_json(reply)
    return {"reply": reply, "proposal_data": proposal_data}


@router.get("/status")
def chat_status():
    """Check whether the AI agent is configured and available."""
    return {"available": _ai_svc.is_available}

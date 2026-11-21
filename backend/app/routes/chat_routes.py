from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.auth import ChatSession
from app.db import ping
from app.errors import AppError
from app.schemas import ChatEvent, ChatRequest, OkResponse
from app.services.chat import ChatTrace, claim_session, stream_chat, validate_message

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def _sse(event: ChatEvent) -> str:
    return f"data: {event.model_dump_json(exclude_none=True)}\n\n"


@router.post(
    "",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}, "model": ChatEvent}},
)
async def chat_route(body: ChatRequest, session: ChatSession) -> StreamingResponse:
    """Send a message; the reply streams back as Server-Sent Events."""
    message = validate_message(body.message)
    claim_session(session)
    if not ping():
        raise AppError("unavailable", "The portal database is down. Please try again shortly.", 503)

    async def events() -> AsyncIterator[str]:
        async for event in stream_chat(session, message, ChatTrace()):
            yield _sse(event)

    return StreamingResponse(
        events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
    )


@router.post("/reset", response_model=OkResponse)
def reset_route(session: ChatSession) -> OkResponse:
    """New chat: clears the conversation history."""
    if session.lock.locked():
        raise AppError("busy", "Still answering your previous question.", 409)
    session.reset_chat()
    return OkResponse()

from pydantic import BaseModel

from app.agent.prompt_files import load_prompt
from app.agent.structured import structured_call


class MessageDraftResult(BaseModel):
    to: str
    subject: str
    body: str


async def draft_message_text(sender: str, student_ref: str, reason: str) -> MessageDraftResult:
    user_text = f"Sender: {sender}\nStudent: {student_ref}\nReason: {reason}"
    return await structured_call(
        "fast", MessageDraftResult, load_prompt("draft_message.md"), user_text
    )

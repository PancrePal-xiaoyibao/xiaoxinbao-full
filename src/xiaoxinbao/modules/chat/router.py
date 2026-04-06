from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from xiaoxinbao.bootstrap import ServiceContainer, get_container
from xiaoxinbao.modules.chat.schemas import ChatReplyData, ChatRequest
from xiaoxinbao.modules.shared.conversation import ConversationMetadata
from xiaoxinbao.modules.shared.responses import ApiResponse

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
ContainerDep = Annotated[ServiceContainer, Depends(get_container)]


@router.post("/reply", response_model=ApiResponse)
async def chat_reply(
    request: ChatRequest,
    container: ContainerDep,
) -> ApiResponse:
    result = await container.agent_service.reply(
        message=request.message,
        conversation_id=request.conversation_id,
        metadata=ConversationMetadata(
            sender_name=request.sender_name,
            room_name=request.room_name,
            mentioned=request.mentioned,
        ),
    )
    data = ChatReplyData(
        conversation_id=result.conversation_id,
        reply=result.reply,
        citations=result.citations,
    )
    return ApiResponse(data=data.model_dump())

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from xiaoxinbao.modules.chat.service import AgentService
from xiaoxinbao.modules.shared.conversation import ConversationMetadata
from xiaoxinbao.modules.wechat.normalizer import GewechatAdapter
from xiaoxinbao.modules.wechat.schemas import CallbackProcessResult, NormalizedInboundMessage
from xiaoxinbao.settings import Settings


class WechatService:
    def __init__(
        self,
        settings: Settings,
        adapter: GewechatAdapter,
        agent_service: AgentService,
    ) -> None:
        self._settings = settings
        self._adapter = adapter
        self._agent_service = agent_service
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def handle_callback(self, payload: dict[str, Any]) -> CallbackProcessResult:
        normalized_message, reason = self._adapter.normalize(payload)
        if normalized_message is None:
            return CallbackProcessResult(accepted=False, reason=reason)
        if normalized_message.chat_type == "group" and not self._should_trigger(normalized_message):
            return CallbackProcessResult(
                accepted=False,
                reason="group_not_triggered",
                conversation_id=normalized_message.conversation_id,
                normalized_message=normalized_message,
            )

        lock = self._locks[normalized_message.conversation_id]
        async with lock:
            result = await self._agent_service.reply(
                message=normalized_message.content,
                conversation_id=normalized_message.conversation_id,
                metadata=ConversationMetadata(
                    chat_type=normalized_message.chat_type,
                    sender_id=normalized_message.sender_id,
                    sender_name=normalized_message.sender_name,
                    room_id=normalized_message.room_id,
                    room_name=normalized_message.room_name,
                    mentioned=normalized_message.mentioned,
                ),
            )
        return CallbackProcessResult(
            accepted=True,
            reason="processed",
            conversation_id=result.conversation_id,
            reply=result.reply,
            normalized_message=normalized_message,
        )

    def _should_trigger(self, normalized_message: NormalizedInboundMessage) -> bool:
        if normalized_message.mentioned:
            return True
        return any(
            keyword in normalized_message.content
            for keyword in self._settings.group_trigger_keywords
            if keyword
        )

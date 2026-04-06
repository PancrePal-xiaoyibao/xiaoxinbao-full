from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from xiaoxinbao.modules.chat.service import AgentService
from xiaoxinbao.modules.shared.conversation import ConversationMetadata
from xiaoxinbao.modules.wechat.client import GewechatDeliveryClient
from xiaoxinbao.modules.wechat.normalizer import GewechatAdapter
from xiaoxinbao.modules.wechat.schemas import (
    CallbackProcessResult,
    DeliveryResultData,
    NormalizedInboundMessage,
)
from xiaoxinbao.settings import Settings


class WechatService:
    def __init__(
        self,
        settings: Settings,
        adapter: GewechatAdapter,
        agent_service: AgentService,
        delivery_client: GewechatDeliveryClient | None = None,
    ) -> None:
        self._settings = settings
        self._adapter = adapter
        self._agent_service = agent_service
        self._delivery_client = delivery_client
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
            delivery = await self._deliver_reply(normalized_message, result.reply)
        return CallbackProcessResult(
            accepted=True,
            reason="processed",
            conversation_id=result.conversation_id,
            reply=result.reply,
            normalized_message=normalized_message,
            delivery=delivery,
        )

    def _should_trigger(self, normalized_message: NormalizedInboundMessage) -> bool:
        if normalized_message.mentioned:
            return True
        return any(
            keyword in normalized_message.content
            for keyword in self._settings.group_trigger_keywords
            if keyword
        )

    async def _deliver_reply(
        self,
        normalized_message: NormalizedInboundMessage,
        reply: str,
    ) -> DeliveryResultData:
        receiver_id = normalized_message.room_id or normalized_message.sender_id
        ats = [normalized_message.sender_id] if normalized_message.chat_type == "group" else []
        content = reply
        if normalized_message.chat_type == "group":
            display_name = normalized_message.sender_name or normalized_message.sender_id
            content = f"@{display_name} {reply}"

        if (
            self._delivery_client is None
            or not self._settings.gewechat_send_enabled
            or not self._settings.gewechat_app_id
        ):
            return DeliveryResultData(
                attempted=False,
                receiver_id=receiver_id,
                ats=ats,
                content=content,
            )

        try:
            result = await self._delivery_client.send_text(
                app_id=self._settings.gewechat_app_id,
                receiver_id=receiver_id,
                content=content,
                ats=ats,
            )
        except Exception as exc:
            return DeliveryResultData(
                attempted=True,
                success=False,
                receiver_id=receiver_id,
                ats=ats,
                content=content,
                error=str(exc),
            )

        return DeliveryResultData(
            attempted=True,
            success=result.success,
            receiver_id=receiver_id,
            ats=ats,
            content=content,
            provider_response=result.response_data,
        )

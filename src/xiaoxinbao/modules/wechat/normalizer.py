from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from typing import Any

from xiaoxinbao.modules.wechat.schemas import NormalizedInboundMessage


class GewechatAdapter:
    def __init__(self, bot_names: list[str]) -> None:
        self._bot_names = bot_names

    def normalize(self, payload: dict[str, Any]) -> tuple[NormalizedInboundMessage | None, str]:
        if "testMsg" in payload and "token" in payload:
            return None, "test_callback"

        data = payload.get("Data")
        if not isinstance(data, dict):
            return None, "missing_data"

        msg_type = int(data.get("MsgType", 0) or 0)
        if msg_type == 51:
            return None, "status_sync"
        if msg_type != 1:
            return None, "unsupported_message_type"

        bot_wxid = self._extract_string(payload.get("Wxid"))
        from_user_id = self._extract_string(data.get("FromUserName"))
        to_user_id = self._extract_string(data.get("ToUserName")) or bot_wxid
        if not from_user_id:
            return None, "missing_sender"

        if self._is_non_user_message(data, from_user_id):
            return None, "non_user"

        if bool(data.get("IsSelf")) or (bot_wxid and from_user_id == bot_wxid):
            return None, "self_message"

        created_at = int(data.get("CreateTime") or time.time())
        if created_at < int(time.time()) - 300:
            return None, "expired_message"

        raw_content = self._extract_string(data.get("Content"))
        if not raw_content:
            return None, "empty_content"

        is_group = bool(data.get("ChatroomId")) or from_user_id.endswith("@chatroom")
        room_id = self._extract_string(data.get("ChatroomId")) or (
            from_user_id if is_group else None
        )
        room_name = self._extract_string(data.get("ChatroomName")) or room_id

        sender_id = self._extract_string(data.get("ActualUserId")) or from_user_id
        sender_name = self._extract_string(data.get("ActualUserName")) or sender_id
        content = raw_content

        if is_group:
            parsed_sender_id, content = self._parse_group_content(raw_content)
            if parsed_sender_id:
                sender_id = parsed_sender_id
            sender_name = self._extract_string(data.get("ActualUserName")) or sender_id
            mentioned = bool(data.get("IsAt")) or self._parse_is_at(
                self._extract_string(data.get("MsgSource")),
                to_user_id,
            )
        else:
            mentioned = True

        content = self._strip_mentions(content)
        conversation_id = sender_id if not is_group else f"{sender_id}@@{room_id}"

        normalized = NormalizedInboundMessage(
            message_id=str(data.get("MsgId") or data.get("NewMsgId") or "unknown"),
            chat_type="group" if is_group else "direct",
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_name=sender_name,
            room_id=room_id,
            room_name=room_name,
            mentioned=mentioned,
            content=content.strip(),
            created_at=created_at,
        )
        if not normalized.content:
            return None, "empty_content"
        return normalized, "accepted"

    @staticmethod
    def _extract_string(value: Any) -> str:
        if isinstance(value, dict):
            extracted = value.get("string")
            return str(extracted).strip() if extracted is not None else ""
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _is_non_user_message(data: dict[str, Any], from_user_id: str) -> bool:
        sender_type = str(data.get("SenderType") or data.get("MessageCategory") or "").lower()
        return sender_type in {"non_user", "system", "official"} or from_user_id.startswith("gh_")

    @staticmethod
    def _parse_group_content(raw_content: str) -> tuple[str | None, str]:
        if ":\n" not in raw_content:
            return None, raw_content
        sender_id, content = raw_content.split(":\n", maxsplit=1)
        return sender_id.strip() or None, content

    @staticmethod
    def _parse_is_at(msg_source: str, bot_wxid: str) -> bool:
        if not msg_source or not bot_wxid:
            return False
        try:
            root = ET.fromstring(msg_source)
        except ET.ParseError:
            return False
        atuserlist = root.findtext("atuserlist", default="")
        return bot_wxid in atuserlist

    def _strip_mentions(self, content: str) -> str:
        stripped = content
        for bot_name in self._bot_names:
            stripped = re.sub(rf"@{re.escape(bot_name)}[\u2005\s]*", "", stripped)
        return stripped.strip()

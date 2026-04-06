from __future__ import annotations

from pydantic import BaseModel

from xiaoxinbao.modules.knowledge.retriever import KnowledgeHit, KnowledgeRetriever
from xiaoxinbao.modules.llm.base import LLMGateway, LLMMessage
from xiaoxinbao.modules.sessions.store import SessionStore
from xiaoxinbao.modules.shared.conversation import ConversationMetadata
from xiaoxinbao.settings import Settings


class AgentResult(BaseModel):
    conversation_id: str
    reply: str
    citations: list[str]


class AgentService:
    def __init__(
        self,
        settings: Settings,
        session_store: SessionStore,
        retriever: KnowledgeRetriever,
        gateway: LLMGateway,
    ) -> None:
        self._settings = settings
        self._session_store = session_store
        self._retriever = retriever
        self._gateway = gateway

    async def reply(
        self,
        message: str,
        conversation_id: str,
        metadata: ConversationMetadata | None = None,
    ) -> AgentResult:
        resolved_metadata = metadata or ConversationMetadata()
        hits = self._retriever.search(message)
        prompt_messages = self._build_messages(
            message=message,
            conversation_id=conversation_id,
            metadata=resolved_metadata,
            hits=hits,
        )
        reply = await self._gateway.chat(prompt_messages, model=self._settings.model_name)
        self._session_store.append_turn(conversation_id, "user", message)
        self._session_store.append_turn(conversation_id, "assistant", reply)
        return AgentResult(
            conversation_id=conversation_id,
            reply=reply,
            citations=[hit.title for hit in hits],
        )

    def _build_messages(
        self,
        message: str,
        conversation_id: str,
        metadata: ConversationMetadata,
        hits: list[KnowledgeHit],
    ) -> list[LLMMessage]:
        messages: list[LLMMessage] = [
            {
                "role": "system",
                "content": self._build_system_prompt(metadata),
            }
        ]
        history = self._session_store.get_turns(conversation_id)
        messages.extend({"role": turn.role, "content": turn.content} for turn in history)
        user_message = message.strip()
        if hits:
            context_block = "\n".join(f"- {hit.title}: {hit.excerpt}" for hit in hits)
            user_message = f"{user_message}\n\nKnowledge Context:\n{context_block}"
        messages.append({"role": "user", "content": user_message})
        return messages

    @staticmethod
    def _build_system_prompt(metadata: ConversationMetadata) -> str:
        prompt = [
            "你是小馨宝，一名温和、谨慎、有边界感的心理支持 AI 助手。",
            "你不能替代专业医生，但可以帮助用户梳理情绪、给出安全的下一步建议。",
            "如果发现用户有明显自伤、伤人或急性危机倾向，优先建议联系当地紧急援助资源和可信任的人。",
        ]
        if metadata.chat_type == "group":
            prompt.append("当前场景是群聊，回复要简洁并避免泄露其他人的上下文。")
        if metadata.sender_name:
            prompt.append(f"当前用户名称：{metadata.sender_name}")
        if metadata.room_name:
            prompt.append(f"当前群组名称：{metadata.room_name}")
        return "\n".join(prompt)

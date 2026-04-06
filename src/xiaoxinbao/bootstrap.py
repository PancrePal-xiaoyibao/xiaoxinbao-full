from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from xiaoxinbao.modules.chat.service import AgentService
from xiaoxinbao.modules.knowledge.retriever import KnowledgeRetriever
from xiaoxinbao.modules.llm.factory import build_gateway
from xiaoxinbao.modules.sessions.store import SessionStore
from xiaoxinbao.modules.wechat.client import build_gewechat_client
from xiaoxinbao.modules.wechat.normalizer import GewechatAdapter
from xiaoxinbao.modules.wechat.service import WechatService
from xiaoxinbao.settings import Settings, get_settings


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    session_store: SessionStore
    retriever: KnowledgeRetriever
    agent_service: AgentService
    wechat_service: WechatService


def create_container(settings: Settings | None = None) -> ServiceContainer:
    resolved_settings = settings or get_settings()
    session_store = SessionStore(
        ttl_seconds=resolved_settings.session_ttl_seconds,
        max_turns=resolved_settings.session_history_limit,
    )
    retriever = KnowledgeRetriever(
        knowledge_dir=Path(resolved_settings.knowledge_dir),
        default_strategy=resolved_settings.retrieval_mode,
    )
    gateway = build_gateway(resolved_settings)
    agent_service = AgentService(
        settings=resolved_settings,
        session_store=session_store,
        retriever=retriever,
        gateway=gateway,
    )
    wechat_service = WechatService(
        settings=resolved_settings,
        adapter=GewechatAdapter(bot_names=resolved_settings.bot_names),
        agent_service=agent_service,
        delivery_client=build_gewechat_client(resolved_settings),
    )
    return ServiceContainer(
        settings=resolved_settings,
        session_store=session_store,
        retriever=retriever,
        agent_service=agent_service,
        wechat_service=wechat_service,
    )


@lru_cache(maxsize=1)
def get_container() -> ServiceContainer:
    return create_container()

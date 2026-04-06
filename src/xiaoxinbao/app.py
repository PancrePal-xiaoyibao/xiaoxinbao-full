from __future__ import annotations

from fastapi import FastAPI

from xiaoxinbao.modules.chat.router import router as chat_router
from xiaoxinbao.modules.health.router import router as health_router
from xiaoxinbao.modules.wechat.router import router as wechat_router
from xiaoxinbao.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="xiaoxinbao",
        version="0.1.0",
        description="Adapter-first AI chat service with Gewechat callback support.",
    )
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(wechat_router)
    app.state.settings = settings
    return app


app = create_app()

# xiaoxinbao-full

小馨宝 2.0 的 P0 后端实现，采用 `FastAPI + adapter-first` 架构，重点解决：

1. Gewechat 回调消息标准化
2. 群聊用户级 session 隔离
3. 本地可测的 Agent Core、知识检索与 mock LLM gateway

## Quick Start

```bash
uv sync
uv run ruff check .
uv run mypy
uv run pytest
uv run uvicorn xiaoxinbao.app:app --host 0.0.0.0 --port 8080
```

## APIs

- `GET /health`
- `POST /api/v1/chat/reply`
- `POST /api/v1/wechat/gewechat/callback`

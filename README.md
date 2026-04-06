# xiaoxinbao-full

小馨宝 2.0 的 P0 后端实现，采用 `FastAPI + adapter-first` 架构，重点解决：

1. Gewechat 回调消息标准化
2. 群聊用户级 session 隔离
3. 本地可测的 Agent Core、知识检索与 mock LLM gateway
4. 可选的 Gewechat 出站文本回复
5. 可切换的关键词 / 向量式检索与独立 Knowledge API

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
- `POST /api/v1/knowledge/search`
- `POST /api/v1/wechat/gewechat/callback`

## Post-P0

本轮已补齐：

1. `KnowledgeRetriever` 的 `keyword` / `vector` 两种搜索模式
2. `POST /api/v1/knowledge/search` 独立检索验证接口
3. `HttpGewechatDeliveryClient` 出站文本回复链路
4. OpenAI-compatible gateway 与 Gewechat 出站链路测试

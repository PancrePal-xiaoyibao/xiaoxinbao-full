# 小馨宝 2.0 — 社区 AI 心理助手引擎 · 产品需求文档 (PRD)

> 版本: v1.0 · 日期: 2026-04-06 · 作者: 小虾 🦞  
> 状态: **待确认**

---

## 1. 背景与动机

### 1.1 现状痛点

| 维度 | 现状 (小馨宝 1.0) | 问题 |
|------|-------------------|------|
| 平台 | FastGPT + Web 前端 | Web 端可用，但响应慢 |
| 群聊接入 | Gewechat 卫星机器人框架 | FastGPT 后台回复速度慢，群聊体验极差 |
| 并发能力 | 受限于 FastGPT 单线程调度 | 多群同时使用时队列阻塞 |
| 数据管理 | FastGPT 内置存储 | 无合规备案，不能长期留存用户数据 |
| 用户识别 | 无 | 无法区分群聊中的不同用户 |

### 1.2 核心目标

**重新设计一个轻量、高并发、可一键部署的 AI Chat + RAG Agent 引擎**，替代 FastGPT 后端，与 Gewechat/微信机器人无缝集成，在群聊中实现快速、精准、带用户上下文的心理支持服务。

---

## 2. 产品范围

### 2.1 In Scope (本期)

1. **Agent Core Engine** — AI Chat + RAG 核心，支持心理助手角色
2. **LLM Gateway** — 统一大模型 API 接入层（FastGPT 转发 或 直连 API，可热切换）
3. **Gewechat 适配器** — 兼容 Gewechat 卫星机器人协议，处理群聊消息
4. **微信机器人模块** — 内置微信机器人客户端，支持：
   - 群聊消息接收
   - @提及识别与回复（@answer @提问者）
   - 用户 ID 识别，独立对话上下文
5. **数据管理** — 会话数据自动过期清除（合规模式），未来可切换为加密持久化
6. **一键部署** — Docker Compose 单机部署方案

### 2.2 Out of Scope (后续迭代)

- 用户数据加密持久化（等 ICP 备案后）
- Web 管理后台
- 多租户 / 多 Agent 角色切换
- 语音消息处理

---

## 3. 架构决策记录 (ADR)

### ADR-1: 技术栈选择

| 维度 | 方案 A: Python FastAPI | 方案 B: Node.js (Bun) | 方案 C: Go |
|------|----------------------|----------------------|------------|
| 开发效率 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Agent SDK 生态 | ⭐⭐⭐⭐⭐ (OpenAI Agent SDK, LangChain) | ⭐⭐⭐⭐ | ⭐⭐ |
| 异步并发 | ⭐⭐⭐⭐ (asyncio) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 部署简便 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Gewechat 集成 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (JS 原生) | ⭐⭐⭐ |

**决策: Python 3.11+ / FastAPI**

**理由:**
- 主人明确倾向 Python + OpenAI Agent SDK
- FastAPI 异步能力足够支撑社区级高并发（非百万级 C10K）
- RAG / Agent 生态最成熟（LlamaIndex, LangChain, OpenAI Agent SDK）
- 部署轻量，单 Docker 容器即可运行

### ADR-2: LLM API 接入方案

| 方案 | 延迟 | 数据管控 | 并发上限 | 成本 |
|------|------|----------|----------|------|
| FastGPT 转发 API | 较高 (~2-5s) | 可定期删除记录 | 受 FastGPT 限流 | 已有 |
| 直连大模型 API | 低 (~1-2s) | 自主管控 | 仅受 API 配额 | 需申请 |

**决策: 双模设计，默认 FastGPT 转发，可热切换直连**

**理由:**
- 主人倾向 FastGPT 转发 — 数据管理便利 + 已有基础设施
- 架构上抽象出 LLM Gateway 层，后续切直连零改代码
- FastGPT 转发的额外延迟在 Agent 层面可接受（群聊场景容忍 ~3-5s）

### ADR-3: 微信机器人方案

**决策: 内置集成，兼容 Gewechat 协议，同时支持独立微信机器人运行**

- 优先兼容 Gewechat 协议（如果社区已部署 Gewechat）
- 内置 `wechat-bot` 模块，可独立作为微信机器人运行
- 两者共享相同的 Agent Core 接口，Adapter 模式解耦

---

## 4. 系统架构

### 4.1 架构总览

```
┌─────────────────────────────────────────────────────┐
│                   微信群聊 / Web                      │
└──────────────┬──────────────────────┬────────────────┘
               │                      │
    ┌──────────▼──────────┐  ┌───────▼───────────┐
    │   Gewechat Adapter │  │  WeChat Bot Client │
    │   (卫星机器人协议)   │  │  (内置微信机器人)   │
    └──────────┬──────────┘  └───────┬───────────┘
               │                      │
               └──────┬───────────────┘
                      │
              ┌───────▼────────┐
              │  Message Router │  ← 用户ID识别 / @解析 / 消息分发
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │  Agent Core    │  ← RAG检索 / Prompt构建 / 上下文管理
              │  (Chat + RAG)  │
              └───┬────────┬───┘
                  │        │
          ┌───────▼──┐  ┌──▼──────────┐
          │ LLM Gate │  │ Vector Store │  ← RAG 知识库
          │  way     │  │ (FAISS/      │
          └───────┬──┘  │  ChromaDB)   │
                  │      └─────────────┘
          ┌───────▼──────────────────┐
          │ FastGPT API / 直连 LLM API │
          └──────────────────────────┘
```

### 4.2 目录结构

```
xinxinbao/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
├── README.md
│
├── config/
│   ├── settings.py              # 全局配置 (Pydantic Settings)
│   ├── prompts/
│   │   └── system_prompt.py     # 小馨宝角色 Prompt
│   └── knowledge/               # RAG 知识库源文件
│       └── mental_health/       # 心理健康知识文档
│
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 入口
│   │
│   ├── gateway/                 # LLM Gateway 层
│   │   ├── __init__.py
│   │   ├── base.py              # 抽象接口
│   │   ├── fastgpt.py           # FastGPT 转发适配
│   │   └── direct_api.py        # 直连 API 适配
│   │
│   ├── agent/                   # Agent Core
│   │   ├── __init__.py
│   │   ├── core.py              # Chat + RAG 主逻辑
│   │   ├── rag.py               # RAG 检索模块
│   │   ├── context.py           # 用户对话上下文管理
│   │   └── memory.py            # 会话记忆 (自动过期)
│   │
│   ├── adapters/                # 消息通道适配器
│   │   ├── __init__.py
│   │   ├── base.py              # 抽象消息适配器
│   │   ├── Gewechat.py         # Gewechat 卫星机器人适配
│   │   ├── wechat_bot.py        # 内置微信机器人
│   │   └── web.py               # Web API (兼容旧前端)
│   │
│   ├── router/                  # 消息路由
│   │   ├── __init__.py
│   │   └── message_router.py    # 用户识别 / @解析 / 分发
│   │
│   └── data/                    # 数据管理
│       ├── __init__.py
│       ├── session_store.py     # 会话存储 (内存 + TTL 过期)
│       └── cleanup.py           # 自动清理定时任务
│
├── tests/
│   ├── test_agent.py
│   ├── test_gateway.py
│   ├── test_router.py
│   └── test_adapters.py
│
└── scripts/
    ├── build_knowledge.py       # 知识库向量化构建脚本
    └── deploy.sh                # 一键部署脚本
```

---

## 5. 核心功能规格

### 5.1 Agent Core (Chat + RAG)

| 特性 | 规格 |
|------|------|
| 角色设定 | 小馨宝心理助手 — 温暖、专业、有同理心的心理健康 AI 助手 |
| RAG 知识库 | 心理健康 FAQ、情绪疏导话术、危机干预指南 |
| 向量数据库 | ChromaDB (嵌入式，零运维) 或 FAISS (纯内存) |
| 上下文窗口 | 每用户保留最近 10 轮对话，TTL 30 分钟自动过期 |
| 响应延迟目标 | P95 < 5s (FastGPT 转发) / < 3s (直连) |
| 并发目标 | 同时支持 20+ 群聊并发请求 |

### 5.2 LLM Gateway

```python
# 接口抽象
class LLMGateway(Protocol):
    async def chat(self, messages: list[dict], **kwargs) -> str: ...
    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncIterator[str]: ...
```

- **FastGPT 模式**: 调用 FastGPT 的 `/api/v1/chat/completions` 等兼容端点
- **直连模式**: 调用 OpenAI 兼容 API（企业捐赠的模型 key）
- 通过 `.env` 中 `LLM_MODE=fastgpt|direct` 热切换，无需重启

### 5.3 消息路由 & 用户识别

```
群聊消息流:
  用户A在群里说: "小馨宝，我今天心情不好"
    → 微信机器人收到消息
    → Message Router 解析:
        - 群ID: group_123
        - 用户ID: user_A (微信ID)
        - 是否@提及: 是/否
    → Agent Core 加载 user_A 的上下文
    → LLM 生成回复
    → 微信机器人发送: "@用户A 小馨宝的回复内容"
```

**用户 ID 识别策略:**
- 优先使用微信唯一 ID
- 备选使用群内昵称 + 群ID 组合
- 每个用户独立维护对话上下文

**@回复策略:**
- 群聊中检测到 @小馨宝 或关键词触发
- 回复时 @提问者，确保用户看到
- 支持配置触发关键词列表

### 5.4 数据管理 & 合规

| 模式 | 行为 | 适用阶段 |
|------|------|----------|
| **合规模式 (默认)** | 会话数据仅存内存，TTL 过期自动删除，重启即清空 | ICP 备案前 |
| **持久化模式 (未来)** | 加密存储至 SQLite/PostgreSQL，用户授权后开启 | ICP 备案后 |

合规模式下:
- 会话上下文 TTL = 30 分钟
- 服务重启 = 所有历史数据清空
- 不写入任何磁盘持久化存储
- 日志仅记录请求/响应元数据（不含用户内容）

### 5.5 Gewechat 兼容

- 实现 Gewechat 卫星机器人协议的消息格式
- 通过 WebSocket 或 HTTP Webhook 接收/发送消息
- 兼容 Gewechat 的插件注册机制

### 5.6 微信机器人模块

**两种运行模式:**

1. **Gewechat 模式** — 作为 Gewechat 的下游服务运行，接收 Gewechat 转发的消息
2. **独立模式** — 内置微信机器人客户端（基于 `wechaty` 或 `gewechat`），直接连接微信

配置项:
```env
# .env
WECHAT_MODE=Gewechat|standalone
Gewechat_WEBHOOK_URL=...
Gewechat_WS_URL=...

# 独立模式配置
GEWECHAT_API_URL=...
GEWECHAT_TOKEN=...
```

---

## 6. 部署方案

### 6.1 一键部署

```yaml
# docker-compose.yml
version: "3.8"
services:
  xinxinbao:
    build: .
    ports:
      - "8080:8080"        # API 端口
    env_file: .env
    restart: unless-stopped
    volumes:
      - ./config/knowledge:/app/config/knowledge  # 知识库文件
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 6.2 部署步骤

```bash
# 1. 克隆项目
git clone <repo> && cd xinxinbao

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入:
#   LLM_MODE=fastgpt
#   FASTGPT_API_KEY=xxx
#   FASTGPT_API_BASE=https://xxx
#   WECHAT_MODE=Gewechat
#   Gewechat_WEBHOOK_URL=xxx

# 3. 构建知识库（首次）
docker compose run --rm xinxinbao python scripts/build_knowledge.py

# 4. 启动服务
docker compose up -d

# 完成！
```

---

## 7. 非功能性需求

| 维度 | 要求 |
|------|------|
| 响应延迟 | P95 < 5s (含 LLM 调用) |
| 并发能力 | ≥ 20 群同时在线 |
| 可用性 | 99%+ (单机) |
| 部署时间 | 从 clone 到运行 < 15 分钟 |
| 代码量 | 核心 < 3000 行 Python |
| 依赖数量 | 尽量少，避免依赖地狱 |

---

## 8. 关键技术依赖

| 库 | 用途 | 版本 |
|----|------|------|
| FastAPI | HTTP 框架 | ^0.115 |
| uvicorn | ASGI 服务器 | ^0.34 |
| httpx | 异步 HTTP 客户端 (调用 LLM API) | ^0.28 |
| chromadb | 向量数据库 (RAG) | ^1.0 |
| pydantic | 数据模型 & 配置 | ^2.0 |
| pydantic-settings | 环境变量管理 | ^2.0 |
| openai | OpenAI SDK (如用 Agent SDK) | ^1.0 |

可选:
| 库 | 用途 |
|----|------|
| python-socketio | WebSocket (Gewechat) |
| requests | Gewechat API 调用 |

---

## 9. 开放问题 & 风险

| # | 问题 | 影响 | 建议 |
|---|------|------|------|
| 1 | 微信机器人方案选型 (wechaty / gewechat / 其他) | 决定独立模式能否正常运行 | 调研社区现有微信机器人方案 |
| 2 | Gewechat 协议文档是否可获取 | 影响适配器开发进度 | 确认是否能拿到 Gewechat 协议文档 |
| 3 | FastGPT API 并发上限 | 可能成为性能瓶颈 | 压测确认，必要时切直连 |
| 4 | 知识库内容来源 | RAG 质量决定回答质量 | 社区提供心理健康知识文档 |
| 5 | ICP 备案时间线 | 影响持久化功能排期 | 先按合规模式设计 |

---

## 10. 里程碑建议

| 阶段 | 内容 | 预估工时 |
|------|------|----------|
| **P0: MVP** | Agent Core + LLM Gateway + Web API + 基础 RAG | 2-3 天 |
| **P1: 群聊接入** | Gewechat 适配器 + 消息路由 + 用户识别 | 1-2 天 |
| **P2: 微信机器人** | 内置微信机器人 + @回复 + 群聊上下文 | 2-3 天 |
| **P3: 部署上线** | Docker 化 + 一键部署 + 压测 | 1 天 |

**总预估: 6-9 天** (AI 辅助编码)

---

## 11. 给 AI 编程工具的执行指令

> 见附件 `AGENT_INSTRUCTIONS.md`（可在确认 PRD 后生成）

---

*小虾出品 · 2026-04-06 · 🦞*

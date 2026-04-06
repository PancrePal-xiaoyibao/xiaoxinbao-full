# 小馨宝 2.0 — 社区 AI 心理助手引擎 · 产品需求文档 (PRD)

> 版本: v1.1  
> 日期: 2026-04-06  
> 状态: **已校正，可执行**

---

## 1. 背景与目标

### 1.1 现状痛点

| 维度 | 现状 | 主要问题 |
|------|------|----------|
| LLM 接入 | FastGPT + Web 前端 | 响应慢，群聊体验差 |
| 微信接入 | 依赖 Gewechat 卫星机器人链路 | 接入能力存在外部依赖与稳定性风险 |
| 并发处理 | FastGPT 调度为主 | 多群并发时容易阻塞 |
| 数据管理 | 平台内置存储 | 备案前不适合长期留存敏感对话数据 |
| 用户识别 | 群聊内无法稳定区分用户 | 无法形成独立上下文与精准回复 |

### 1.2 核心目标

构建一个轻量、可测、可一键部署的 `AI Chat + RAG + WeChat Adapter` 服务，用于替代现有 FastGPT 后端在微信群场景中的核心处理能力，并满足：

1. 群聊中稳定识别发言用户、群组和是否被 @。
2. 将微信通道与 Agent Core 解耦，避免业务逻辑被微信协议实现绑死。
3. 默认使用内存会话与 TTL 清理，满足备案前的合规约束。
4. 在本仓库中形成可执行 PRD、`.debug`、代码、测试的闭环。

---

## 2. 本期范围

### 2.1 In Scope

1. `Agent Core`：统一聊天入口，拼装系统提示词、会话上下文与知识检索结果。
2. `LLM Gateway`：支持 `FastGPT` 代理模式与 `OpenAI-compatible` 直连模式。
3. `Knowledge Retrieval`：P0 先提供本地 Markdown 知识库加载 + 轻量检索适配层，保留后续切换向量库能力。
4. `Gewechat Callback Adapter`：接收外部 Gewechat 服务回调，标准化为内部消息模型。
5. `Message Router`：完成群聊/单聊识别、@ 触发判断、session_id 组装与串行处理。
6. `Session Store`：基于内存 + TTL 的会话上下文管理。
7. `API & Docs`：提供健康检查、聊天调试接口、Gewechat 回调接口以及对应 API 文档。
8. `自动化测试`：覆盖消息归一化、路由、会话 TTL、API 闭环测试。

### 2.2 Out of Scope

1. 真正登录微信个人号的“内置独立微信客户端”。
2. 备案前的持久化用户会话存储。
3. Web 管理后台。
4. 语音消息下载、转码和发送能力。
5. 多租户、多 Agent 角色切换。

---

## 3. 技术方案修正结论

### ADR-1: 技术栈基线

| 维度 | 决策 |
|------|------|
| 运行时 | Python 3.11+ |
| Web 框架 | FastAPI |
| 配置管理 | pydantic-settings |
| HTTP 客户端 | httpx |
| 测试 | pytest + pytest-asyncio |
| 质量检查 | ruff |
| 依赖管理 | uv |

**决策理由**

1. 目标仓库目前几乎为空仓，Python/FastAPI 最适合快速拉起一个可测的服务骨架。
2. 用户既有偏好仍是 Python 生态，后续接 OpenAI SDK、FastGPT 或其他兼容网关成本低。
3. 需要快速进入“文档 -> API -> 测试”闭环，FastAPI 在 OpenAPI、依赖注入、测试友好性上最合适。

### ADR-2: 微信接入方案

| 方案 | 是否 P0 | 结论 |
|------|---------|------|
| 内置 wechaty / itchat 客户端 | 否 | 不作为主路径 |
| 外部 Gewechat 服务 + 本服务回调适配 | 是 | 作为 P0 主方案 |
| 未来可插拔其他通道（企业微信/WCF 等） | 否 | 作为后续扩展点 |

**修正点**

结合 `dify-on-wechat` 的实现逻辑，本项目不再把“微信机器人本体”视为业务核心，而是采用：

1. 外部 `Gewechat Service` 负责登录微信与消息收发。
2. 本服务仅负责回调接收、消息标准化、路由、Agent 处理与回复生成。
3. 微信通道通过统一消息模型接入，后续新增其他通道时不改 Agent Core。

**重要风险说明**

参考 `dify-on-wechat` 当前仓库说明，微信个人号链路仍存在明显外部稳定性与可用性风险。因此：

1. P0 只承诺“适配 Gewechat 回调协议与内部处理闭环”。
2. 不把“稳定登录任意个人号”写入本期验收标准。
3. `standalone` 独立客户端能力降级为后续探索项。

### ADR-3: 消息模型与路由策略

借鉴 `dify-on-wechat` 的 `ChatMessage` 统一消息结构与 `session_id = actual_user_id@@group_id` 的群聊隔离规则，内部统一采用以下字段：

```json
{
  "message_id": "msg_001",
  "chat_type": "group",
  "conversation_id": "wxid_user@@room_123",
  "sender_id": "wxid_user",
  "sender_name": "张三",
  "room_id": "room_123",
  "room_name": "心理互助群",
  "mentioned": true,
  "content": "我今天心情不好",
  "raw_payload": {}
}
```

**路由规则**

1. 单聊 `conversation_id = sender_id`
2. 群聊默认 `conversation_id = sender_id@@room_id`
3. 如果未来开启共享群会话，再按 `room_id` 聚合
4. 群聊只在满足 `@机器人` 或命中关键词时触发
5. 同一 `conversation_id` 内串行处理，避免上下文乱序

### ADR-4: RAG 实现策略

| 阶段 | 实现 |
|------|------|
| P0 | 本地 Markdown 文档加载 + 轻量关键词检索 |
| P1 | 向量检索适配器（Chroma/FAISS） |

**修正原因**

当前仓库尚未具备知识库构建链路。为确保 Ralph 可以在本轮完成“实现 + 测试”，P0 先采用零外部依赖、可单测的轻量检索实现，同时保留标准检索接口，后续可以平滑替换为向量库。

### ADR-5: LLM Gateway 策略

| 模式 | 说明 |
|------|------|
| `fastgpt` | 调用 FastGPT/OpenAI-compatible 代理接口 |
| `direct` | 直连兼容 OpenAI Chat Completions 的模型服务 |
| `mock` | 测试模式，脱离外部网络进行本地验证 |

**修正点**

测试环境默认提供 `mock` gateway，确保自动化测试不依赖真实模型服务。

---

## 4. 参考实现借鉴点

本方案直接借鉴 `dify-on-wechat` 的以下设计思想，但不会原样照搬其全部依赖：

1. `channel_factory` 风格的适配器扩展位。
2. 统一消息对象，而不是把 Gewechat 原始 payload 传入业务层。
3. 群聊用户隔离会话规则：`actual_user_id@@group_id`。
4. 回调接收与消息消费解耦，避免入口阻塞。
5. 对非用户消息、状态同步消息、自发消息做显式过滤。

---

## 5. 系统架构

### 5.1 总体架构

```text
┌──────────────────────────────────────────────────────────────┐
│                    External Gewechat Service                 │
│         登录微信 / 接收消息 / 回调本服务 / 发送回复          │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP Callback
┌──────────────────────────────▼───────────────────────────────┐
│                        FastAPI App                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Wechat Adapter API                                     │  │
│  │ - POST /api/v1/wechat/gewechat/callback                │  │
│  │ - 标准化 payload -> InboundMessage                     │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Message Router                                         │  │
│  │ - 触发判断                                             │  │
│  │ - conversation_id 组装                                 │  │
│  │ - 串行消费                                             │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Agent Core                                             │  │
│  │ - Session Store (TTL)                                  │  │
│  │ - Prompt Builder                                       │  │
│  │ - Knowledge Retriever                                  │  │
│  │ - LLM Gateway                                          │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 目录结构

```text
xiaoxinbao-full/
├── .debug/
├── docs/
│   └── api/
├── config/
│   └── knowledge/
│       └── mental_health/
├── prd/
│   └── PRD.md
├── scripts/
│   └── build_knowledge.py
├── src/
│   └── xiaoxinbao/
│       ├── app.py
│       ├── settings.py
│       ├── modules/
│       │   ├── chat/
│       │   ├── knowledge/
│       │   ├── llm/
│       │   ├── sessions/
│       │   ├── shared/
│       │   └── wechat/
│       └── schemas/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example
```

---

## 6. 核心功能规格

### 6.1 Session Store

1. 默认内存存储。
2. TTL 默认 30 分钟。
3. 每个 `conversation_id` 保留最近 10 轮对话。
4. 进程重启后数据全部丢失。

### 6.2 Gewechat Callback Adapter

1. 仅接收文本消息作为 P0 主输入。
2. 过滤以下消息：
   - 状态同步消息
   - 非用户账号消息
   - 机器人自己发送的消息
   - 超过 5 分钟的过期消息
3. 解析以下字段：
   - `sender_id`
   - `sender_name`
   - `room_id`
   - `room_name`
   - `mentioned`
   - `content`

### 6.3 Message Router

1. 群聊仅在 `mentioned = true` 或命中触发关键词时进入 Agent。
2. 群聊回复默认保留“回复给谁”的上下文信息。
3. 路由层不直接依赖 LLM SDK 或 Gewechat SDK。

### 6.4 Chat API

| 接口 | 用途 |
|------|------|
| `GET /health` | 健康检查 |
| `POST /api/v1/chat/reply` | 本地调试聊天能力 |
| `POST /api/v1/wechat/gewechat/callback` | 接收 Gewechat 消息回调 |

### 6.5 合规约束

1. 默认不将用户消息落盘。
2. 日志仅记录元数据，不记录完整敏感会话内容。
3. 测试示例知识库使用公开心理健康基础文本，不引入真实用户数据。

---

## 7. 非功能性要求

| 维度 | 要求 |
|------|------|
| 响应延迟 | 本地 mock 模式 P95 < 500ms |
| 并发能力 | 支持 20 个以上 conversation_id 的并发排队处理 |
| 部署时间 | 从 clone 到通过测试 < 15 分钟 |
| 可测试性 | 核心链路必须可在离线测试环境完成验证 |

---

## 8. 关键依赖

| 库 | 用途 | 版本建议 |
|----|------|----------|
| fastapi | API 框架 | ^0.115 |
| uvicorn | ASGI 服务 | ^0.30 |
| httpx | HTTP 客户端 | ^0.27 |
| pydantic | 数据模型 | ^2.8 |
| pydantic-settings | 配置管理 | ^2.4 |
| pytest | 测试 | ^8.3 |
| pytest-asyncio | 异步测试 | ^0.23 |
| ruff | 代码检查 | ^0.6 |

---

## 9. 风险与应对

| # | 风险 | 影响 | 应对 |
|---|------|------|------|
| 1 | Gewechat 上游可用性与政策风险 | 个人号接入不稳定 | P0 只做 callback adapter，不承诺登录能力 |
| 2 | 外部模型服务不可用 | 无法测试聊天链路 | 提供 mock gateway |
| 3 | 轻量检索效果有限 | 心理知识召回较弱 | 预留向量检索接口 |
| 4 | 群聊消息格式复杂 | 解析异常导致漏消息 | 先限定文本消息 + 编写规范化测试 |

---

## 10. Ralph 可执行里程碑

| 阶段 | 内容 | 验收 |
|------|------|------|
| P0-1 | 项目骨架、配置、健康检查、质量工具 | `ruff` 与 `pytest` 可运行 |
| P0-2 | Session Store、Knowledge Retriever、LLM Gateway | 单元测试通过 |
| P0-3 | Chat API 与 Agent Core | 调试接口可返回结果 |
| P0-4 | Gewechat Callback Adapter 与 Message Router | 回调测试通过，群聊 session 规则正确 |
| P0-5 | Docker/README/API 文档闭环 | 本地启动说明完整 |

---

## 11. Ralph Story 拆分原则

1. 每个 Story 必须在单轮内完成。
2. 优先顺序固定为：骨架 -> 核心模块 -> API -> 通道适配 -> 文档与部署。
3. 每个 Story 必须包含 `Typecheck/Quality checks pass`。
4. 与 Gewechat 真实登录相关的工作不得作为本轮硬性验收项。

---

## 12. 当前结论

本 PRD 已从“内置微信机器人一体化实现”修正为“外部 Gewechat 服务 + 内部标准化适配 + Agent Core 解耦”的可执行方案。后续 Ralph 落地应严格围绕该修正版继续推进。

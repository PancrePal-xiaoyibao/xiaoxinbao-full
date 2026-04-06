# ADR 2026-04-06 - WeChat Stack Realignment

## Context

原始 PRD 将“内置微信机器人客户端”视作主路径，但参考 `dify-on-wechat` 的真实实现后，发现更合理的方案应是“外部微信接入服务 + 内部标准化适配 + Agent Core 解耦”。

## Decisions

1. 采用 `Gewechat callback adapter` 作为 P0 微信接入方案。
2. 内部统一消息模型，禁止业务层直接消费 Gewechat 原始 payload。
3. 群聊 session 默认按 `actual_user_id@@group_id` 隔离。
4. 过滤非用户消息、状态同步消息、自发消息与过期消息。
5. 以 `mock` LLM gateway 保障自动化测试闭环。

## Evidence Borrowed From dify-on-wechat

1. `channel_factory` 与通道解耦思路。
2. `ChatMessage` 风格的统一消息字段设计。
3. `chat_channel` 中按 session 串行处理消息的设计。
4. Gewechat callback 侧对 `is_at`、群成员、过期消息、自发消息的过滤逻辑。

## Risks

1. 上游 Gewechat 可用性并不稳定，不能把真实登录当作当前验收目标。
2. 当前仓库为空仓，必须优先建立最小可测链路，而不是引入完整外部 SDK 依赖。

## Consequences

1. 本轮实现聚焦于 callback 适配、消息路由、会话管理、调试 API 与测试。
2. `standalone` 微信客户端能力推迟到后续迭代。

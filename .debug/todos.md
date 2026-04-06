# TODOs

## In Progress

- [x] TODO-001 建立 Python/FastAPI/uv/ruff/pytest 项目骨架
- [x] TODO-002 实现 Session Store、Knowledge Retriever、LLM Gateway 抽象与 mock gateway
- [x] TODO-003 实现 Chat API、Agent Core 与标准响应模型
- [x] TODO-004 实现 Gewechat callback adapter、消息标准化与路由规则
- [x] TODO-005 补齐 API 文档、README、Docker 与自动化测试
- [x] TODO-006 修正 Ralph 资产：`prd.json`、`prd-progress.txt`、`.claude/scripts/prompt.md`
- [x] TODO-007 实现 Gewechat 出站文本回复链路与发送测试
- [x] TODO-008 升级检索策略并暴露 Knowledge Search API
- [x] TODO-009 补齐 OpenAI-compatible gateway 与出站链路集成测试、文档和进度回写

## Done

- [x] DONE-001 修正 `prd/PRD.md` 的技术栈与微信接入方案
- [x] DONE-002 建立 Ralph 执行基座与进度文件
- [x] DONE-003 完成 P0 后端代码、测试与部署文档闭环
- [x] DONE-004 完成 post-P0 出站发送、检索升级与集成测试闭环

## Exit Conditions

- [x] `ruff check .` 通过
- [x] `mypy` 通过
- [x] `pytest` 通过
- [x] `prd.json` 中所有 Story 标记为 `passes: true`
- [x] `.debug` 与 `prd/PRD.md` 状态一致

# Debug Workspace

## Current Goal

将 `prd/PRD.md` 的修正版继续推进到 P0 之后的可测能力，并保持以下三份状态同步：

1. `prd/PRD.md`
2. `prd.json`
3. `.debug/todos.md`

## Current Constraints

1. 微信接入仅以“外部 Gewechat 服务 + 本服务 callback adapter”作为 P0 主路径。
2. 不实现真实个人号登录能力，不把该能力作为当前验收项。
3. 默认不落盘用户会话，使用内存 + TTL。
4. 测试必须脱离真实 LLM 与真实微信环境，可在本地离线完成。

## Ralph Notes

1. 当前环境缺少 `amp` 与 `jq`，原始 `.claude/scripts/ralph.sh` 无法直接完成预检。
2. 当前 `.claude/scripts/prompt.md` 错误引用了 `progress.txt`，应改为 `prd-progress.txt`。
3. 在工具缺失修正前，使用“等价 Ralph 迭代”原则推进：
   - 每轮只做一个高优先级 Story
   - 每轮都要执行质量检查
   - 每轮都要回写 `prd.json` 与 `prd-progress.txt`

## Architecture Guardrails

1. Wechat 原始 payload 只能进入 adapter 层，不得直接进入 Agent Core。
2. 群聊默认 session 规则为 `actual_user_id@@group_id`。
3. 只处理文本消息；语音、图片、文件只保留扩展位。
4. 核心模块必须有 API 文档或测试覆盖，不允许“只写代码不留契约”。
5. 出站 Gewechat 能力必须是可关闭的 adapter，不得把外部发送失败扩散成核心聊天失败。

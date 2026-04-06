# xiaoxinbao-full

小馨宝 2.0 后端服务，采用 `FastAPI + adapter-first` 架构，当前已完成：

1. Gewechat 回调消息标准化
2. 群聊用户级 session 隔离
3. Agent Core、知识检索、LLM gateway
4. 可选的 Gewechat 出站文本回复
5. `keyword` / `vector` 两种检索模式
6. 可独立验证的 Chat API、Knowledge API、Gewechat Callback API

这份 README 以“测试同学可直接部署并继续验证”为目标编写。

## 1. 测试范围

当前版本已经适合继续做以下测试：

1. 本地调试聊天链路
2. 知识库检索效果验证
3. Gewechat callback 入站处理验证
4. Gewechat 出站文本回发验证
5. OpenAI-compatible / FastGPT 网关切换验证

当前不在强验收范围内：

1. 真正的微信个人号登录能力
2. 真实向量数据库接入
3. 语音、图片、文件消息处理

## 2. 目录说明

关键目录：

1. [`src/xiaoxinbao`](./src/xiaoxinbao) 应用代码
2. [`tests`](./tests) 自动化测试
3. [`docs/api`](./docs/api) 接口文档
4. [`config/knowledge`](./config/knowledge) 示例知识库
5. [`scripts/build_knowledge.py`](./scripts/build_knowledge.py) 知识库预览构建脚本

## 3. 环境要求

推荐环境：

1. Python `3.11+`
2. `uv`
3. Windows / macOS / Linux 均可

如果要联调真实 Gewechat 出站发送，还需要：

1. 已部署可访问的 Gewechat 服务
2. 可用的 `GEWECHAT_TOKEN`
3. 可用的 `GEWECHAT_APP_ID`

## 4. 本地部署

### 4.1 安装依赖

```bash
uv sync
```

### 4.2 准备环境变量

先复制环境变量模板：

```bash
cp .env.example .env
```

Windows PowerShell 可用：

```powershell
Copy-Item .env.example .env
```

### 4.3 推荐测试配置

如果只是做本地接口和链路验证，建议先使用最稳妥的 `mock` 配置：

```env
APP_ENV=development
APP_NAME=xiaoxinbao
LLM_MODE=mock
MODEL_NAME=mock-gpt
RETRIEVAL_MODE=keyword
RETRIEVAL_TOP_K=3
SESSION_TTL_SECONDS=1800
SESSION_HISTORY_LIMIT=10
BOT_NAMES=小馨宝
GROUP_TRIGGER_KEYWORDS=小馨宝,心理,求助
GEWECHAT_SEND_ENABLED=false
```

### 4.4 启动服务

```bash
uv run uvicorn xiaoxinbao.app:app --host 0.0.0.0 --port 8080
```

启动后访问：

```text
http://127.0.0.1:8080/docs
```

## 5. Docker 部署

### 5.1 准备 `.env`

```bash
cp .env.example .env
```

### 5.2 启动

```bash
docker compose up -d --build
```

### 5.3 健康检查

```bash
curl http://127.0.0.1:8080/health
```

期望返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok"
  }
}
```

## 6. 联调配置

### 6.1 使用真实 FastGPT

```env
LLM_MODE=fastgpt
MODEL_NAME=your-model-name
FASTGPT_API_BASE=https://your-fastgpt-base/v1
FASTGPT_API_KEY=your-fastgpt-key
```

说明：

1. 当前实现调用的是 OpenAI-compatible `chat/completions`
2. 需要确认你的 FastGPT 网关兼容该接口

### 6.2 使用直连 OpenAI-compatible 模型服务

```env
LLM_MODE=direct
MODEL_NAME=your-model-name
OPENAI_API_BASE=https://your-openai-compatible-base/v1
OPENAI_API_KEY=your-api-key
```

### 6.3 启用 Gewechat 出站发送

```env
GEWECHAT_SEND_ENABLED=true
GEWECHAT_API_BASE=http://127.0.0.1:2531/v2/api
GEWECHAT_TOKEN=xxx
GEWECHAT_APP_ID=xxx
GEWECHAT_SEND_TEXT_PATH=/message/postText
```

说明：

1. callback 收到并处理成功后，会尝试通过 Gewechat 回发文本
2. 群聊回发会使用 `room_id` 作为接收方
3. 群聊回发会携带 `ats`，并在文本前自动拼 `@发送人昵称`
4. 即使出站发送失败，服务本身也不会把整条 callback 处理判为失败

## 7. 测试步骤

### 7.1 自动化测试

部署前建议先跑一次：

```bash
uv run ruff check .
uv run mypy
uv run pytest
uv run python scripts/build_knowledge.py
```

当前基线结果应为：

1. `ruff` 通过
2. `mypy` 通过
3. `pytest` 通过
4. `config/knowledge/manifest.json` 成功生成

### 7.2 Chat API 手工验证

```bash
curl -X POST http://127.0.0.1:8080/api/v1/chat/reply ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"我今天心情不好\",\"conversation_id\":\"debug-001\",\"sender_name\":\"小明\"}"
```

期望：

1. HTTP 200
2. `code = 0`
3. `data.reply` 非空
4. `data.citations` 返回命中的知识条目

### 7.3 Knowledge API 手工验证

```bash
curl -X POST http://127.0.0.1:8080/api/v1/knowledge/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"我今天心情不好，压力也大\",\"strategy\":\"vector\",\"limit\":3}"
```

期望：

1. HTTP 200
2. `code = 0`
3. `data.hits` 非空
4. 能看到 `basic support` 或其他命中文档

### 7.4 Gewechat Callback API 手工验证

```bash
curl -X POST http://127.0.0.1:8080/api/v1/wechat/gewechat/callback ^
  -H "Content-Type: application/json" ^
  -d "{\"Wxid\":\"wxid_bot\",\"Data\":{\"MsgId\":\"1001\",\"MsgType\":1,\"CreateTime\":4102444800,\"FromUserName\":{\"string\":\"room_123@chatroom\"},\"ToUserName\":{\"string\":\"wxid_bot\"},\"ChatroomId\":\"room_123@chatroom\",\"ChatroomName\":\"心理互助群\",\"ActualUserName\":\"张三\",\"Content\":{\"string\":\"wxid_user:\n@小馨宝 我今天压力大\"},\"MsgSource\":\"<msgsource><atuserlist><![CDATA[,wxid_bot,]]></atuserlist></msgsource>\"}}"
```

期望：

1. HTTP 200
2. `accepted = true`
3. `conversation_id = wxid_user@@room_123@chatroom`
4. `normalized_message.mentioned = true`
5. 启用 Gewechat 出站时，`delivery.attempted = true`

## 8. 测试建议

建议测试同学按下面顺序推进：

1. 先用 `mock` 模式验证 `/health`、`/chat/reply`、`/knowledge/search`
2. 再验证 `/wechat/gewechat/callback` 的入站处理
3. 最后再打开 `GEWECHAT_SEND_ENABLED=true` 做真实出站联调
4. 若要切换真实模型，再从 `mock` 切到 `fastgpt` 或 `direct`

## 9. 常见问题

### 9.1 为什么 callback 成功了，但没有真的回发微信消息？

优先检查：

1. `GEWECHAT_SEND_ENABLED` 是否为 `true`
2. `GEWECHAT_API_BASE`、`GEWECHAT_TOKEN`、`GEWECHAT_APP_ID` 是否正确
3. Gewechat 服务是否真的暴露了 `POST /message/postText`

### 9.2 为什么群聊消息没有触发？

当前群聊触发规则：

1. 被机器人 @
2. 或命中 `GROUP_TRIGGER_KEYWORDS`

### 9.3 为什么知识检索命中不稳定？

当前 `vector` 不是正式向量数据库，而是轻量 token cosine 检索，适合测试接口与排序，不等价于生产级 embedding 检索。

## 10. 参考文档

1. [Chat API](./docs/api/chat.md)
2. [Knowledge API](./docs/api/knowledge.md)
3. [Gewechat Callback API](./docs/api/gewechat-callback.md)

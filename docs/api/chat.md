# Chat API

## POST `/api/v1/chat/reply`

本地调试 Agent Core，不依赖真实微信回调。

### Request

```json
{
  "message": "我今天心情不好",
  "conversation_id": "debug-001",
  "sender_name": "小明"
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "conversation_id": "debug-001",
    "reply": "小馨宝回应：...",
    "citations": ["basic support"]
  }
}
```

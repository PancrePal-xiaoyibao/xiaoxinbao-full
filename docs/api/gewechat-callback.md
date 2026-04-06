# Gewechat Callback API

## POST `/api/v1/wechat/gewechat/callback`

接收外部 Gewechat 服务回调，并在内部完成：

1. payload 标准化
2. 非用户/过期/自发消息过滤
3. 群聊触发判断
4. Agent Core 调用
5. 在启用出站模式时通过 Gewechat API 回发文本消息

### Supported P0 Fields

```json
{
  "Wxid": "wxid_bot",
  "Data": {
    "MsgId": "1001",
    "MsgType": 1,
    "CreateTime": 4102444800,
    "FromUserName": { "string": "room_123@chatroom" },
    "ToUserName": { "string": "wxid_bot" },
    "ChatroomId": "room_123@chatroom",
    "ChatroomName": "心理互助群",
    "ActualUserName": "张三",
    "Content": { "string": "wxid_user:\n@小馨宝 我今天压力大" },
    "MsgSource": "<msgsource><atuserlist><![CDATA[,wxid_bot,]]></atuserlist></msgsource>"
  }
}
```

## Delivery Behavior

当 `.env` 中启用以下配置时，callback 处理成功后会通过 Gewechat 文本消息接口回发：

```env
GEWECHAT_SEND_ENABLED=true
GEWECHAT_API_BASE=http://127.0.0.1:2531/v2/api
GEWECHAT_TOKEN=xxx
GEWECHAT_APP_ID=xxx
GEWECHAT_SEND_TEXT_PATH=/message/postText
```

群聊回复会：

1. 以群 `room_id` 作为接收方
2. 使用原发送人 `sender_id` 作为 `ats`
3. 在文本前自动补 `@发送人昵称`

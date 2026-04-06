# Gewechat Callback API

## POST `/api/v1/wechat/gewechat/callback`

接收外部 Gewechat 服务回调，并在内部完成：

1. payload 标准化
2. 非用户/过期/自发消息过滤
3. 群聊触发判断
4. Agent Core 调用

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

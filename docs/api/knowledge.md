# Knowledge API

## POST `/api/v1/knowledge/search`

独立验证知识库命中效果，不依赖聊天接口。

### Request

```json
{
  "query": "我今天心情不好，压力也大",
  "strategy": "vector",
  "limit": 3
}
```

### Response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "query": "我今天心情不好，压力也大",
    "strategy": "vector",
    "hits": [
      {
        "title": "basic support",
        "source": "config/knowledge/mental_health/basic_support.md",
        "excerpt": "当用户表达“心情不好”“很累”“压力大”时，优先做三件事：",
        "score": 0.5
      }
    ]
  }
}
```

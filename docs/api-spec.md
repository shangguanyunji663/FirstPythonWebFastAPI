# API 接口文档

## 概述

本文档详细描述了新闻系统的API接口，包括用户管理、新闻浏览、收藏、历史记录、AI问答和数据采集（RSS 爬虫）等功能模块。

## 基础URL

```
http://127.0.0.1:8000
```

> 前端默认 baseURL 为 `http://127.0.0.1:8000`，可通过 `frontend/.env.local` 的 `VITE_API_BASE_URL` 覆盖。

## 认证方式

大部分接口需要认证，认证通过在请求头中添加 `Authorization` 字段实现：

```
Authorization: Bearer <token值>
```

> 后端对 `Bearer ` 前缀做了严格解析，同时兼容直接传 token 值；前端 axios 封装（`frontend/src/api/request.js`）已统一携带 `Bearer` 前缀，推荐统一使用标准格式。

> 令牌有效期为 7 天，每个用户仅保留一条有效令牌（重新登录会覆盖旧令牌并重置有效期）。服务端只存令牌的 SHA-256 摘要，原始令牌仅在注册/登录响应中返回一次。

## 响应格式

所有接口返回JSON格式数据，通用响应结构如下：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## 错误响应

错误响应复用统一结构，`code` 为对应的 HTTP 状态码，`data` 一般为 `null`（仅两类例外：参数校验错误返回字段级错误明细数组；`DEBUG_MODE=true` 时附带调试信息）：

| code | 场景 | message 示例 |
|------|------|--------------|
| 400 | 请求参数校验失败（如分页参数小于 1、新密码少于 6 位），此时 `data` 为字段级错误明细数组 | `该字段为必填项` / `长度不足` / `取值不合法` |
| 400 | 数据库唯一约束冲突（按具体约束返回） | `用户名已存在` / `手机号已被注册` / `已收藏过该新闻` |
| 401 | 未认证、令牌无效/过期，或登录用户名/密码错误 | `无效的令牌或已经过期的令牌` / `用户名或密码错误` |
| 404 | 资源不存在 | `新闻不存在` / `收藏记录不存在` / `历史记录不存在` |
| 429 | 登录尝试过于频繁（同一用户名 60 秒内超过 5 次） | `登录尝试过于频繁，请稍后再试` |
| 500 | 服务器内部错误 | `服务器内部错误` |

> 仅当后端 `.env` 中 `DEBUG_MODE=true`（仅限本地开发）时，错误响应的 `data` 才会附带异常类型、详情与堆栈，生产环境一律返回 `null`。

## 接口详情

### 用户管理模块

#### 1. 用户注册

- **接口地址**: `POST /api/user/register`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名，4~20 位字母/数字/下划线 |
| password | string | 是 | 密码，6~32 位 |

> 参数校验失败返回 400，`data` 为字段级错误明细；用户名已存在返回 400，`message` 为 `用户已存在`。

- **请求示例**:

```json
{
  "username": "example_user",
  "password": "example_password"
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "token": "用户访问令牌",
    "userInfo": {
      "id": 1,
      "username": "example_user",
      "bio": "这个人很懒，什么都没留下",
      "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
    }
  }
}
```

#### 2. 用户登录

- **接口地址**: `POST /api/user/login`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名（仅要求非空，宽松规则兼容历史账号） |
| password | string | 是 | 密码（仅要求非空，最长 64 位） |

> 用户名或密码错误返回 401，`message` 为 `用户名或密码错误`（不区分账号不存在与密码错误）；失败尝试过多返回 429。

- **请求示例**:

```json
{
  "username": "example_user",
  "password": "example_password"
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "登录成功啦",
  "data": {
    "token": "用户访问令牌",
    "userInfo": {
      "id": 1,
      "username": "example_user",
      "nickname": null,
      "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
      "bio": "这个人很懒，什么都没留下"
    }
  }
}
```

#### 3. 获取用户信息

- **接口地址**: `GET /api/user/info`
- **请求头**: 需要认证
- **响应示例**:

```json
{
  "code": 200,
  "message": "获取用户信息成功",
  "data": {
    "id": 1,
    "username": "example_user",
    "nickname": null,
    "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
    "gender": "unknown",
    "bio": "这个人很懒，什么都没留下"
  }
}
```

#### 4. 更新用户信息

- **接口地址**: `PUT /api/user/update`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| nickname | string | 否 | 昵称，最长 50 字符 |
| avatar | string | 否 | 头像URL，最长 255 字符 |
| gender | string | 否 | 性别，仅允许 `male` / `female` / `unknown` |
| bio | string | 否 | 个人简介，最长 500 字符 |
| phone | string | 否 | 手机号，`1[3-9]` 开头的 11 位号码 |

- **请求示例**:

```json
{
  "bio": "这是我的个人简介"
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "更新用户信息成功",
  "data": {
    "id": 1,
    "username": "example_user",
    "nickname": null,
    "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
    "gender": "unknown",
    "bio": "这是我的个人简介"
  }
}
```

#### 5. 修改用户密码

- **接口地址**: `PUT /api/user/password`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| oldPassword | string | 是 | 当前密码 |
| newPassword | string | 是 | 新密码，最少 6 位 |

- **错误响应**: 旧密码错误返回 400，`message` 为 `旧密码不正确`（非 500）

- **请求示例**:

```json
{
  "oldPassword": "current_password",
  "newPassword": "new_password"
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "修改密码成功",
  "data": null
}
```

### 新闻模块

#### 1. 获取新闻分类列表

- **接口地址**: `GET /api/news/categories`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| skip | integer | 否 | 跳过的记录数，默认为0，最小值为0 |
| limit | integer | 否 | 返回的记录数限制，默认为100，取值范围 1~200 |

- **请求示例**:

```
GET /api/news/categories
GET /api/news/categories?skip=0&limit=10
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "获取新闻分类成功",
  "data": [
    {
      "id": 1,
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00",
      "name": "科技",
      "sort_order": 0
    }
  ]
}
```

#### 2. 获取新闻列表

- **接口地址**: `GET /api/news/list`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| categoryId | integer | 是 | 分类ID |
| page | integer | 否 | 页码，默认为1，最小值为1 |
| pageSize | integer | 否 | 每页显示的新闻数量，默认为10，取值范围 1~100 |

- **请求示例**:

```
GET /api/news/list?categoryId=1
GET /api/news/list?categoryId=1&page=2&pageSize=20
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "获取新闻列表成功",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "新闻标题",
        "description": "新闻简介",
        "image": null,
        "author": null,
        "categoryId": 1,
        "views": 0,
        "publishTime": "2023-01-01T00:00:00"
      }
    ],
    "total": 100,
    "hasMore": true
  }
}
```

> 列表项为 `NewsItemBase` 结构（不含正文 content；正文请调详情接口）。

#### 3. 获取新闻详情

- **接口地址**: `GET /api/news/detail`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 新闻ID |

- **请求示例**:

```
GET /api/news/detail?id=1
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "新闻标题",
    "content": "新闻内容",
    "image": null,
    "author": null,
    "publishTime": "2023-01-01T00:00:00",
    "categoryId": 1,
    "views": 1,
    "relatedNews": []
  }
}
```

> 浏览量在响应返回后由后台任务异步 +1（不阻塞响应），因此响应中的 `views` 是本次浏览前的值。

### 收藏模块

#### 1. 检查新闻收藏状态

- **接口地址**: `GET /api/favorite/check`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| newsId | integer | 是 | 新闻ID |

- **请求示例**:

```
GET /api/favorite/check?newsId=1
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "检查收藏状态成功",
  "data": {
    "isFavorite": true
  }
}
```

#### 2. 添加收藏

- **接口地址**: `POST /api/favorite/add`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| newsId | integer | 是 | 新闻ID |

- **请求示例**:

```json
{
  "newsId": 1
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "添加收藏成功",
  "data": {
    "id": 1,
    "userId": 1,
    "newsId": 1,
    "createTime": "2023-01-01T00:00:00"
  }
}
```

#### 3. 取消收藏

- **接口地址**: `DELETE /api/favorite/remove`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| newsId | integer | 是 | 新闻ID |

- **请求示例**:

```
DELETE /api/favorite/remove?newsId=1
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "删除收藏成功",
  "data": null
}
```

#### 4. 获取收藏列表

- **接口地址**: `GET /api/favorite/list`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为1，最小值为1 |
| pageSize | integer | 否 | 每页条数，默认为10，取值范围 1~100 |

- **请求示例**:

```
GET /api/favorite/list
GET /api/favorite/list?page=1&pageSize=10
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "获取收藏列表成功",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "新闻标题",
        "description": "",
        "image": "",
        "author": "",
        "categoryId": 1,
        "views": 1,
        "publishTime": "2023-01-01T00:00:00",
        "favoriteId": 1,
        "favoriteTime": "2023-01-01T00:00:00"
      }
    ],
    "total": 1,
    "hasMore": false
  }
}
```

#### 5. 清空所有收藏

- **接口地址**: `DELETE /api/favorite/clear`
- **请求头**: 需要认证
- **响应示例**:

```json
{
  "code": 200,
  "message": "清空了1条记录",
  "data": null
}
```

### 浏览历史模块

#### 1. 添加浏览记录

- **接口地址**: `POST /api/history/add`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| newsId | integer | 是 | 新闻ID |

- **请求示例**:

```json
{
  "newsId": 1
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "添加成功",
  "data": {
    "id": 1,
    "userId": 1,
    "newsId": 1,
    "viewTime": "2023-01-01T00:00:00"
  }
}
```

#### 2. 获取浏览历史列表

- **接口地址**: `GET /api/history/list`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为1，最小值为1 |
| pageSize | integer | 否 | 每页条数，默认为10，取值范围 1~100 |

- **请求示例**:

```
GET /api/history/list
GET /api/history/list?page=1&pageSize=10
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "新闻标题",
        "description": "",
        "image": "",
        "author": "",
        "categoryId": 1,
        "views": 1,
        "publishTime": "2023-01-01T00:00:00",
        "historyId": 1,
        "viewTime": "2023-01-01T00:00:00"
      }
    ],
    "total": 1,
    "hasMore": false
  }
}
```

#### 3. 删除单条浏览记录

- **接口地址**: `DELETE /api/history/delete/{history_id}`
- **请求头**: 需要认证
- **路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| history_id | integer | 是 | 历史记录ID（仅能删除当前登录用户自己的记录，删除他人的记录返回 404） |

- **请求示例**:

```
DELETE /api/history/delete/1
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

#### 4. 清空浏览历史

- **接口地址**: `DELETE /api/history/clear`
- **请求头**: 需要认证
- **响应示例**:

```json
{
  "code": 200,
  "message": "清空成功",
  "data": null
}
```
### AI 问答模块

> AI 问答走后端代理：前端不持有任何模型服务密钥，提供方（智谱 / 本地 Ollama）由后端 `.env` 的 `AI_PROVIDER` 配置。对话记录自动落库 `ai_chat` 表。

#### 1. AI 对话（SSE 流式）

- **接口地址**: `POST /api/ai/chat`
- **请求头**: 需要认证
- **响应类型**: `text/event-stream`（SSE 流式，不是普通 JSON）
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| message | string | 是 | 用户消息，1~4000 字符 |
| history | array | 否 | 历史对话 `[{role, content}]`，`role` 仅允许 `user` / `assistant`，`content` 1~4000 字符；后端最多取最近 10 条 |

- **请求示例**:

```json
{
  "message": "帮我总结一下今天的科技新闻",
  "history": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "你好，有什么可以帮你？" }
  ]
}
```

- **响应格式（SSE）**: 每行为 `data: <JSON>`，JSON 为 OpenAI 兼容的流式 chunk（取 `choices[0].delta.content` 累加即为回答）；以 `data: [DONE]` 结束；出错时返回 `data: {"error": "错误说明"}`：

```
data: {"choices":[{"delta":{"content":"今天"}}]}

data: {"choices":[{"delta":{"content":"的科技新闻…"}}]}

data: [DONE]
```

#### 2. 获取聊天历史

- **接口地址**: `GET /api/ai/history`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| limit | integer | 否 | 返回条数，默认20，取值范围 1~100（时间正序） |

- **响应示例**:

```json
{
  "code": 200,
  "message": "获取聊天历史成功",
  "data": {
    "list": [
      {
        "id": 1,
        "message": "你好",
        "response": "你好，有什么可以帮你？",
        "createdAt": "2023-01-01T00:00:00"
      }
    ],
    "total": 1
  }
}
```

### 数据采集模块

> 新闻数据由后端内置的 RSS 爬虫采集：应用启动时先抓取一次，之后每 `CRAWL_INTERVAL_HOURS`（默认 6）小时自动抓取公开源（源列表见 `backend/crawler/sources.py`），按（标题，分类）去重入库，并自动失效对应分类的缓存。`.env` 中设置 `CRAWLER_ENABLED=false` 可整体关闭定时抓取。

#### 1. 手动触发抓取

- **接口地址**: `POST /api/crawler/run`
- **请求头**: 需要认证
- **请求参数**: 无

- **响应示例**:

```json
{
  "code": 200,
  "message": "抓取完成：获取 120 条，新增 3 条",
  "data": {
    "fetched": 120,
    "inserted": 3,
    "skipped": 117,
    "failed_sources": []
  }
}
```

- **响应字段说明**:

| 字段 | 说明 |
|------|------|
| fetched | 本次从各源解析出的新闻条数 |
| inserted | 实际新增入库的条数 |
| skipped | 因（标题，分类）重复被跳过的条数 |
| failed_sources | 抓取失败的源 URL 列表（单源失败只记日志，不影响其他源） |
